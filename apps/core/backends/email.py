from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings

class RedirectEmailBackend(EmailBackend):
    """
    A custom SMTP backend that intercepts all outgoing emails 
    and redirects them to a single test recipient.
    """
    def send_messages(self, email_messages):
        test_recipient = getattr(settings, 'EMAIL_REDIRECT_RECIPIENT', 'sub2pewds10102005@gmail.com')
        
        for message in email_messages:
            original_to = message.to
            message.to = [test_recipient]
            message.cc = []
            message.bcc = []
            
            # 1. Update Subject
            if message.subject and not message.subject.startswith("[INTERCEPTED]"):
                message.subject = f"[INTERCEPTED] {message.subject}"
            
            # 2. Update Body (Plain Text)
            banner = f"--- INTERCEPTED TEST EMAIL ---\nOriginal Recipient: {', '.join(original_to)}\n------------------------------\n\n"
            message.body = banner + message.body
            
            # 3. Update HTML Alternatives (if any)
            if hasattr(message, 'alternatives'):
                for i, (content, mimetype) in enumerate(message.alternatives):
                    if mimetype == 'text/html':
                        html_banner = f"""
                        <div style="background: #fff5f5; border: 2px dashed #f56565; padding: 15px; margin-bottom: 20px; color: #c53030; font-family: sans-serif;">
                            <strong>⚠️ INTERCEPTED TEST EMAIL</strong><br>
                            This email was originally addressed to: <code>{', '.join(original_to)}</code><br>
                            It has been redirected to you for testing purposes.
                        </div>
                        """
                        message.alternatives[i] = (html_banner + content, mimetype)
            
        return super().send_messages(email_messages)
