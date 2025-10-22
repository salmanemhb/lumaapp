"""
Authentication routes - signup and login
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.models.database import Company, User, UserRole
from app.models.schemas import SignupRequest, SignupResponse, LoginRequest, LoginResponse
from app.services.auth import authenticate_user, create_access_token, hash_password
from app.services.email import EmailService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Company signup endpoint
    Creates pending company and sends welcome email with Google Form link
    """
    # Check if company already exists
    existing_company = db.query(Company).filter(Company.name == request.company_name).first()
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name already registered. Please contact admin if this is an error."
        )
    
    # Check if email already used
    existing_email = db.query(Company).filter(Company.contact_email == request.contact_email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )
    
    # Create pending company entry
    company = Company(
        name=request.company_name,
        sector=request.sector,
        contact_email=request.contact_email,
        approved=False
    )
    
    db.add(company)
    db.commit()
    db.refresh(company)
    
    # Send welcome email with form link
    logger.info(f"Company {request.company_name} signed up successfully, sending welcome email to {request.contact_email}")
    try:
        EmailService.send_welcome_email(
            to_email=request.contact_email,
            company_name=request.company_name,
            language="es"  # Default to Spanish for Spain-first
        )
        logger.info(f"Welcome email sent successfully to {request.contact_email}")
    except Exception as e:
        # Log error but don't fail the signup
        logger.exception(f"Failed to send welcome email to {request.contact_email}: {str(e)}")
        logger.error(f"Email error details - Company: {request.company_name}, Error type: {type(e).__name__}")
    
    return SignupResponse(
        message="Thank you for signing up! Please check your email for next steps.",
        company_id=company.id
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint
    Returns JWT token for approved users only
    """
    # Authenticate user
    user = authenticate_user(db, request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval. Please wait for confirmation email."
        )
    
    # Check company approval
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if not company or not company.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company account not approved yet."
        )
    
    # Create access token
    token_data = {
        "sub": user.id,
        "company_id": user.company_id,
        "email": user.email,
        "role": user.role.value
    }
    access_token = create_access_token(data=token_data)
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "company_id": user.company_id,
            "company_name": company.name,
            "role": user.role.value
        }
    )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(lambda: __import__('app.services.auth', fromlist=['get_current_user']).get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user information from token
    """
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "company_id": current_user.company_id,
        "company_name": company.name if company else None,
        "role": current_user.role.value,
        "last_login": current_user.last_login
    }


@router.get("/test-email")
async def test_email():
    """
    Test endpoint to verify email configuration
    """
    import resend
    logger.info("🧪 Testing email configuration...")
    logger.info(f"Resend API Key: {resend.api_key[:10] if resend.api_key else 'NOT SET'}...")
    
    try:
        from app.services.email import SENDER_EMAIL
        logger.info(f"Sender Email: {SENDER_EMAIL}")
        
        # Try to send a test email
        response = EmailService.send_welcome_email(
            to_email="test@example.com",
            company_name="Test Company",
            language="en"
        )
        logger.info(f"✅ Test email sent successfully: {response}")
        return {
            "status": "success",
            "message": "Test email sent",
            "response": response
        }
    except Exception as e:
        logger.exception(f"❌ Test email failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }
