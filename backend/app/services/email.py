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
resend.api_key = settings.RESEND_API_KEY
logger.info(f"Resend API configured successfully")

# Sender email
SENDER_EMAIL = "onboarding@resend.dev"


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
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }
        .content {
            background: #f9fafb;
            padding: 30px;
            border: 1px solid #e5e7eb;
            border-top: none;
        }
        .button {
            display: inline-block;
            background: #667eea;
            color: white !important;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 6px;
            margin: 15px 0;
            font-weight: 600;
        }
        .credentials {
            background: white;
            padding: 20px;
            border-left: 4px solid #667eea;
            margin: 20px 0;
            border-radius: 4px;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #6b7280;
            font-size: 14px;
        }
    </style>
</head>
<body>
    {content}
    <div class="footer">
        <p>© 2025 Luma ESG | <a href="https://getluma.es">getluma.es</a></p>
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
        
        content = f"""
<div class="header">
    <h1>🌱 Luma ESG</h1>
</div>
<div class="content">
    <p><strong>{greeting}</strong></p>
    <p>{intro}</p>
    <p>{instruction}</p>
    <p style="text-align: center;">
        <a href="{settings.GOOGLE_FORM_URL}" class="button">{button_text}</a>
    </p>
    <p>{verification_text}</p>
    <p>{closing}</p>
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
    <h1>🌱 Luma ESG</h1>
</div>
<div class="content">
    <p><strong>{greeting}</strong></p>
    <p>{approved}</p>
    
    <div class="credentials">
        <h3>{credentials_title}</h3>
        <p><strong>{login_label}</strong> {user_email}</p>
        <p><strong>{password_label}</strong> <code>{password}</code></p>
    </div>
    
    <p style="text-align: center;">
        <a href="{settings.FRONTEND_URL}/login" class="button">{login_text}</a>
    </p>
    
    <p><em>{security_note}</em></p>
    <p>{closing}</p>
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
    <h1>🌱 Luma ESG</h1>
</div>
<div class="content">
    <p><strong>{greeting}</strong></p>
    <p>{ready}</p>
    
    <div class="credentials">
        <p>{coverage_text}</p>
    </div>
    
    <p style="text-align: center;">
        <a href="{report_url}" class="button">{download_text}</a>
        <a href="{settings.FRONTEND_URL}/dashboard" class="button" style="background: #10b981;">{dashboard_text}</a>
    </p>
</div>
        """
        
        html_body = EmailService._get_base_template().format(content=content)
        
        return resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": to_email,
            "subject": subject,
            "html": html_body
        })
