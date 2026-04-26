import os
import google.generativeai as genai
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AIService:
    """
    Intelligence layer for automated system observability and reporting.
    Includes strict rate-limiting to prevent API abuse and cost overruns.
    """
    
    @classmethod
    def _setup(cls):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("[AI DEBUG] API Key NOT found in environment")
            return False
        genai.configure(api_key=api_key)
        return True

    @classmethod
    def generate_incident_report(cls, analytics):
        """
        Generates a professional, human-like incident report based on telemetry data.
        """
        # 1. Strict Rate Limit: 1 request per 4 hours for AI-generated reports
        rate_limit_key = 'ai_incident_report_lock'
        if cache.get(rate_limit_key):
            logger.info("AI Report Rate Limit Active: Falling back to static report.")
            return None

        if not cls._setup():
            return None

        try:
            model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
            
            prompt = f"""
            You are a Senior Site Reliability Engineer (SRE) for a University Project Registry system.
            A system instability has been detected. Based on the following telemetry data, 
            write a concise (2-3 sentences) status update for the student-facing Statuspage.
            
            DATA:
            - Health Score: {analytics.get('health')}/100
            - Error Rate: {analytics.get('error_rate') or 0}%
            - DB Latency: {analytics.get('db_telemetry', {}).get('avg_latency')}ms
            - Media Latency: {analytics.get('media_telemetry', {}).get('avg_latency')}ms
            
            GUIDELINES:
            - Be calm and professional.
            - Mention specific issues (e.g. 'high database latency' or 'increased error rates') if they are prominent.
            - Do not use corporate jargon like 'synergy' or 'robust'.
            - End with a statement that we are investigating.
            - DO NOT mention the AI itself.
            """

            response = model.generate_content(prompt)
            report_text = response.text.strip()
            
            # Set the lock for 4 hours
            cache.set(rate_limit_key, True, 14400)
            
            return report_text

        except Exception as e:
            print(f"[AI DEBUG] Exception: {str(e)}")
            logger.error(f"AI Generation Error: {str(e)}")
            return None
