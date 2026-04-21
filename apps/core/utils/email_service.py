from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import threading

def _send_email_task(email):
    """Worker task to send the email in a background thread."""
    email.send(fail_silently=True)

def send_html_email(subject, template_name, context, recipient_list):
    """
    Renders an HTML template and sends a multi-part email with plain-text fallback.
    Non-blocking version: Spawns a background thread to handle the SMTP connection.
    """
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=recipient_list
    )
    email.attach_alternative(html_content, "text/html")
    
    # Offload SMTP sending to a background thread to unblock the main process
    thread = threading.Thread(target=_send_email_task, args=(email,))
    thread.start()
