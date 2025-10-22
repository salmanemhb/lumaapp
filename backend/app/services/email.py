"""
Email service using Resend API
"""
import resend
import logging
from typing import Dict, Optional, List
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Configure Resend
try:
    resend.api_key = settings.RESEND_API_KEY
    if not resend.api_key or resend.api_key == "":
        logger.error("❌ RESEND_API_KEY is empty or not set!")
    else:
        logger.info(f"✅ Resend API key configured: {resend.api_key[:10]}...")
except Exception as e:
    logger.exception(f"❌ Failed to configure Resend API: {e}")

# Sender email - Using Resend verified test email
# Sender email
SENDER_EMAIL = "Luma ESG <hello@getluma.es>"


class EmailService:
    """Service for sending transactional emails via Resend"""
    
    @staticmethod
    def _get_base_template(language: str = "en") -> str:
        """Get base HTML template for emails"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background-color: #f3f4f6;
            padding: 0;
            margin: 0;
            width: 100% !important;
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }}
        .email-wrapper {{
            width: 100%;
            background-color: #f3f4f6;
            padding: 20px 0;
        }}
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 36px;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.5px;
        }}
        .header p {{
            margin: 8px 0 0 0;
            font-size: 16px;
            opacity: 0.95;
            font-weight: 400;
        }}
        .content {{
            background: white;
            padding: 40px 30px;
        }}
        .content p {{
            margin-bottom: 16px;
            color: #374151;
            font-size: 16px;
        }}
        .content strong {{
            color: #111827;
        }}
        .leaf-icon {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .button {{
            display: inline-block;
            background: #10b981;
            color: white !important;
            padding: 14px 32px;
            text-decoration: none;
            border-radius: 8px;
            margin: 20px 0;
            font-weight: 600;
            font-size: 16px;
            transition: background 0.3s ease;
        }}
        .button:hover {{
            background: #059669;
        }}
        .button-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .info-box {{
            background: #f0fdf4;
            border: 2px solid #10b981;
            padding: 24px;
            margin: 24px 0;
            border-radius: 8px;
        }}
        .info-box h3 {{
            color: #059669;
            margin: 0 0 12px 0;
            font-size: 18px;
        }}
        .info-box p {{
            margin: 8px 0;
        }}
        .credentials {{
            background: #f9fafb;
            padding: 24px;
            border-left: 4px solid #10b981;
            margin: 24px 0;
            border-radius: 6px;
        }}
        .credentials p {{
            margin: 8px 0;
            font-family: 'Courier New', monospace;
        }}
        .divider {{
            height: 1px;
            background: #e5e7eb;
            margin: 24px 0;
        }}
        .footer {{
            background: #f9fafb;
            text-align: center;
            padding: 30px;
            color: #6b7280;
            font-size: 14px;
        }}
        .footer p {{
            margin: 8px 0;
        }}
        .footer a {{
            color: #10b981;
            text-decoration: none;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
        /* Mobile Responsive */
        @media only screen and (max-width: 600px) {{
            .email-wrapper {{
                padding: 10px 0;
            }}
            .email-container {{
                border-radius: 0;
                box-shadow: none;
            }}
            .header {{
                padding: 30px 20px;
            }}
            .header h1 {{
                font-size: 28px;
            }}
            .header p {{
                font-size: 14px;
            }}
            .content {{
                padding: 30px 20px;
            }}
            .button {{
                display: block;
                width: 100%;
                padding: 16px;
                font-size: 16px;
            }}
            .info-box {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="email-container">
            {content}
            <div class="footer">
                <p><strong>Luma</strong></p>
                <p>Bring clarity to sustainability</p>
                <div class="divider"></div>
                <p>© 2025 Luma ESG · <a href="https://getluma.es">getluma.es</a></p>
            </div>
        </div>
    </div>
</body>
</html>
        """
    
    @staticmethod
    def send_welcome_email(to_email: str, company_name: str, language: str = "en") -> Dict:
        """
        Send welcome email with Google Form link for verification
        
        Args:
            to_email: Recipient email address
            company_name: Name of the company
            language: Email language ('en' or 'es')
        
        Returns:
            Response from Resend API
        """
        if language == "es":
            subject = f"Bienvenido a Luma – Confirma la información de {company_name}"
            greeting = f"Hola equipo de {company_name},"
            intro = "Gracias por tu interés en unirte a Luma, la plataforma de automatización ESG para empresas españolas."
            instruction = "Por favor, completa el siguiente formulario para confirmar la información de tu empresa y los detalles de contacto CSRD."
            verification_text = "Una vez verificado, recibirás tus credenciales de acceso al panel de control."
            button_text = "Completar Formulario"
            closing = "Equipo Luma"
        else:
            subject = f"Welcome to Luma – Confirm {company_name}'s Information"
            greeting = f"Hello {company_name} team,"
            intro = "Thank you for your interest in joining Luma, the ESG automation platform for Spanish companies."
            instruction = "Please fill out the form below to confirm your company information and CSRD contact details."
            verification_text = "Once verified, you'll receive your login credentials for the dashboard."
            button_text = "Complete Form"
            closing = "Luma Team"
        
        # Get the Google Form URL
        form_url = settings.GOOGLE_FORM_URL
        
        content = f"""
<div class="header">
    <h1>Luma</h1>
    <p>Bring clarity to sustainability</p>
</div>
<div class="content">
    <h2 style="color: #111827; font-size: 24px; margin-bottom: 20px;">Welcome to the Luma Private Beta, {company_name}!</h2>
    <div class="leaf-icon">🌱</div>
    
    <p>Thank you for joining us on this journey. We're excited to have <strong>{company_name}</strong> on board as we bring clarity to sustainability reporting.</p>
    
    <div class="info-box">
        <h3>👉 Help us personalize your experience</h3>
        <p>Please take 2 minutes to complete our quick onboarding form.</p>
        <p>This helps us understand your sustainability needs and give you early access to the right features.</p>
    </div>
    
    <div class="button-container">
        <a href="{form_url}" class="button">Fill the Onboarding Form</a>
    </div>
    
    <div class="divider"></div>
    
    <h3 style="color: #111827; margin-top: 24px;">What happens next?</h3>
    <ul style="padding-left: 20px; color: #4b5563;">
        <li style="margin: 8px 0;">Our team will review your onboarding form</li>
        <li style="margin: 8px 0;">You'll receive beta access within the next 2-3 weeks</li>
        <li style="margin: 8px 0;">We'll send you exclusive updates on Luma's development</li>
        <li style="margin: 8px 0;">Get early insights on CSRD compliance and ESG reporting</li>
    </ul>
    
    <p style="margin-top: 24px;">Best regards,<br><strong>The Luma Team</strong></p>
</div>
        """
        
        html_body = EmailService._get_base_template().format(content=content)
        
        logger.info(f"Attempting to send welcome email to {to_email} for company {company_name}")
        logger.debug(f"Email details - From: {SENDER_EMAIL}, Subject: {subject}")
        
        try:
            response = resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": to_email,
                "subject": subject,
                "html": html_body,
            })
            logger.info(f"Successfully sent welcome email to {to_email}. Response: {response}")
            return response
        except Exception as e:
            logger.exception(f"Failed to send welcome email to {to_email}: {str(e)}")
            raise
    
    @staticmethod
    def send_credentials_email(
        to_email: str,
        company_name: str,
        user_email: str,
        password: str,
        language: str = "en"
    ) -> Dict:
        """
        Send login credentials email after approval
        
        Args:
            to_email: Recipient email address
            company_name: Name of the company
            user_email: Login email (may differ from to_email)
            password: Generated password
            language: Email language ('en' or 'es')
        
        Returns:
            Response from Resend API
        """
        if language == "es":
            subject = "Tu Acceso al Panel de Luma está Listo 🎉"
            greeting = f"Hola equipo de {company_name},"
            approved = f"¡Buenas noticias! Tu empresa ha sido aprobada para acceder a Luma."
            credentials_title = "Credenciales de Acceso:"
            login_label = "Email:"
            password_label = "Contraseña:"
            login_text = "Inicia sesión aquí"
            security_note = "Por favor, cambia tu contraseña después del primer inicio de sesión."
            closing = "¡Bienvenido a bordo!"
        else:
            subject = "Your Luma Dashboard Access is Ready 🎉"
            greeting = f"Hello {company_name} team,"
            approved = f"Great news! Your company has been approved for Luma access."
            credentials_title = "Login Credentials:"
            login_label = "Email:"
            password_label = "Password:"
            login_text = "Login Here"
            security_note = "Please change your password after first login."
            closing = "Welcome aboard!"
        
        content = f"""
<div class="header">
    <h1>Luma</h1>
    <p>Bring clarity to sustainability</p>
</div>
<div class="content">
    <h2 style="color: #111827; font-size: 24px; margin-bottom: 20px;">Your Luma Dashboard Access is Ready 🎉</h2>
    
    <p><strong>{greeting}</strong></p>
    <p>{approved}</p>
    
    <div class="credentials">
        <h3 style="margin: 0 0 16px 0; color: #059669;">{credentials_title}</h3>
        <p><strong>{login_label}</strong> {user_email}</p>
        <p><strong>{password_label}</strong> <code style="background: #e5e7eb; padding: 4px 8px; border-radius: 4px; font-size: 14px;">{password}</code></p>
    </div>
    
    <div class="button-container">
        <a href="{settings.FRONTEND_URL}/login" class="button">{login_text}</a>
    </div>
    
    <div class="info-box">
        <p><strong>🔒 Security note:</strong> {security_note}</p>
    </div>
    
    <p style="margin-top: 24px;">{closing}<br><strong>The Luma Team</strong></p>
</div>
        """
        
        html_body = EmailService._get_base_template().format(content=content)
        
        return resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": to_email,
            "subject": subject,
            "html": html_body
        })
    
    @staticmethod
    def send_report_ready_email(
        to_email: str,
        company_name: str,
        report_url: str,
        coverage: float,
        language: str = "en"
    ) -> Dict:
        """
        Send email when sustainability report is ready
        
        Args:
            to_email: Recipient email address
            company_name: Name of the company
            report_url: Download URL for the report
            coverage: CSRD coverage percentage
            language: Email language ('en' or 'es')
        
        Returns:
            Response from Resend API
        """
        if language == "es":
            subject = f"Tu Informe de Sostenibilidad Luma está Listo 📊"
            greeting = f"Hola equipo de {company_name},"
            ready = "Tu informe de sostenibilidad mensual ha sido generado con éxito."
            coverage_text = f"Cobertura CSRD: <strong>{coverage:.0f}%</strong>"
            download_text = "Descargar Informe"
            dashboard_text = "Ver Panel de Control"
        else:
            subject = f"Your Luma Sustainability Report is Ready 📊"
            greeting = f"Hello {company_name} team,"
            ready = "Your monthly sustainability report has been successfully generated."
            coverage_text = f"CSRD Coverage: <strong>{coverage:.0f}%</strong>"
            download_text = "Download Report"
            dashboard_text = "View Dashboard"
        
        content = f"""
<div class="header">
    <h1>Luma</h1>
    <p>Bring clarity to sustainability</p>
</div>
<div class="content">
    <h2 style="color: #111827; font-size: 24px; margin-bottom: 20px;">Your Sustainability Report is Ready 📊</h2>
    
    <p><strong>{greeting}</strong></p>
    <p>{ready}</p>
    
    <div class="info-box">
        <h3>CSRD Coverage</h3>
        <p style="font-size: 32px; font-weight: 700; color: #10b981; margin: 12px 0;">{coverage:.0f}%</p>
    </div>
    
    <div class="button-container">
        <a href="{report_url}" class="button">{download_text}</a>
        <a href="{settings.FRONTEND_URL}/dashboard" class="button" style="background: #059669; margin-left: 10px;">{dashboard_text}</a>
    </div>
    
    <p style="margin-top: 24px;">Best regards,<br><strong>The Luma Team</strong></p>
</div>
        """
        
        html_body = EmailService._get_base_template().format(content=content)
        
        return resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": to_email,
            "subject": subject,
            "html": html_body
        })
