"""
Welcome email service for Comet Invitation Hunter
Handles sending welcome emails to newly verified users
"""

import logging
import uuid
from typing import Optional

import resend

from backend.config import config

logger = logging.getLogger(__name__)

class WelcomeEmailSender:
    """Handles welcome email notifications for new verified users"""
    
    def __init__(self):
        self.resend_api_key = config.resend_api_key
        self.from_email = config.from_email
        
        # Initialize Resend client
        if self.resend_api_key:
            resend.api_key = self.resend_api_key
        else:
            logger.warning("RESEND_API_KEY not configured - welcome emails will not be sent")
    
    def send_welcome_email(self, email: str) -> bool:
        """
        Send welcome email to newly verified user
        
        Args:
            email: Email address of the newly verified user
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not email:
            logger.warning("No email provided for welcome email")
            return False
            
        if not self.resend_api_key:
            logger.error("Resend API key not configured - cannot send welcome email")
            return False
        
        try:
            # Create email content
            subject = "🎉 Welcome to Comet Invitation Hunter!"
            html_content = self._create_welcome_html()
            text_content = self._create_welcome_text()
            
            # Send email using Resend API
            email_data = {
                "from": f"Comet Hunter <{self.from_email}>",
                "to": [email],
                "subject": subject,
                "html": html_content,
                "text": text_content,
                "tags": [
                    {"name": "category", "value": "welcome"},
                    {"name": "type", "value": "new-user"}
                ]
            }
            
            response = resend.Emails.send(email_data)
            
            # Check if response indicates success
            if response and isinstance(response, dict) and 'id' in response:
                logger.info(f"Welcome email sent successfully to {email} (ID: {response['id']})")
                return True
            elif response and hasattr(response, 'id'):
                logger.info(f"Welcome email sent successfully to {email} (ID: {response.id})")
                return True
            else:
                logger.warning(f"Resend API returned unexpected response: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {e}")
            return False
    
    def _create_welcome_html(self) -> str:
        """Create HTML welcome email content"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Comet Invitation Hunter</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    margin: 0; 
                    padding: 0; 
                    background-color: #f8f9fa;
                }
                .container { max-width: 600px; margin: 0 auto; background-color: white; }
                .header { 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 30px 20px; 
                    text-align: center; 
                }
                .header h1 { margin: 0; font-size: 28px; font-weight: 600; }
                .content { padding: 30px 20px; }
                .welcome-message { 
                    font-size: 18px; 
                    color: #2d3748; 
                    margin-bottom: 20px; 
                    text-align: center;
                }
                .info-box { 
                    background-color: #f7fafc; 
                    border: 1px solid #e2e8f0; 
                    border-radius: 8px; 
                    padding: 20px; 
                    margin: 20px 0;
                }
                .info-box h3 { 
                    color: #2d3748; 
                    margin-top: 0; 
                    font-size: 18px;
                }
                .info-box p { 
                    margin: 10px 0; 
                    color: #4a5568;
                }
                .important-notice { 
                    background-color: #fef5e7; 
                    border: 1px solid #f6ad55;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 20px 0;
                }
                .important-notice strong { 
                    color: #c05621;
                }
                .footer { 
                    margin-top: 40px; 
                    padding: 30px 20px; 
                    background-color: #f7fafc; 
                    text-align: center; 
                    font-size: 14px; 
                    color: #718096; 
                    border-top: 1px solid #e2e8f0;
                }
                @media (max-width: 600px) {
                    .container { margin: 0; }
                    .content { padding: 20px 15px; }
                    .header { padding: 20px 15px; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to Comet Invitation Hunter!</h1>
                </div>
                
                <div class="content">
                    <div class="welcome-message">
                        Congratulations! You're now subscribed to Comet Invitation Hunter and will receive email notifications whenever new Comet browser invitations are found.
                    </div>
                    
                    <div class="info-box">
                        <h3>What happens next?</h3>
                        <p>• We'll continuously monitor X/Twitter for Comet browser invitation codes</p>
                        <p>• You'll receive email notifications when new invitations are available</p>
                        <p>• We'll classify posts as either free (direct links) or conditional (require actions)</p>
                        <p>• All notifications are sent in batches to avoid spam</p>
                    </div>
                    
                    <div class="important-notice">
                        <strong>⚠️ Important:</strong> Please make sure to trust emails from <strong>comethunter@skywu.me</strong> to ensure our notification emails don't end up in your spam folder.
                    </div>
                    
                    <div class="info-box">
                        <h3>Need to unsubscribe?</h3>
                        <p>You can unsubscribe from notifications at any time by clicking the unsubscribe link in any email we send you, or by visiting our unsubscribe page.</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Comet Invitation Hunter</strong></p>
                    <p>Thank you for being a verified follower of @0xSky99!</p>
                    <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_welcome_text(self) -> str:
        """Create plain text welcome email content"""
        return """
🎉 WELCOME TO COMET INVITATION HUNTER!

Congratulations! You're now subscribed to Comet Invitation Hunter and will receive email notifications whenever new Comet browser invitations are found.

⚠️  IMPORTANT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please make sure to trust emails from **comethunter@skywu.me** to ensure our notification emails don't end up in your spam folder.

NEED TO UNSUBSCRIBE?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You can unsubscribe from notifications at any time by clicking the unsubscribe link in any email we send you, or by visiting our unsubscribe page.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMET INVITATION HUNTER

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """.strip()

# Global welcome email sender instance
welcome_email_sender = WelcomeEmailSender()