from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count
from apps.core.models import SystemPulse, SystemError
from apps.core.utils.email_service import send_html_email

class InfrastructureService:
    """
    Handles system-level notifications, telemetry cleanup, and infrastructure health.
    """
    
    @staticmethod
    def trigger_prod_sync():
        """Triggers a background production data sync if on Render."""
        import os
        import threading
        from django.core.cache import cache
        from django.core.management import call_command
        from django.utils import timezone
        
        if not os.getenv('PROD_DB_URL'):
            return "idle"
            
        last_sync = cache.get('last_prod_sync_time')
        now = timezone.now()
        
        if not last_sync or (now - last_sync).total_seconds() > 300:
            def run_sync():
                try:
                    call_command('sync_prod')
                    cache.set('last_prod_sync_time', timezone.now(), 3600)
                    cache.set('last_sync_result', 'success', 3600)
                except Exception as e:
                    cache.set('last_sync_result', f'failed: {str(e)}', 3600)

            threading.Thread(target=run_sync, daemon=True).start()
            return "syncing"
        
        return cache.get('last_sync_result', 'idle')

    @staticmethod
    def get_storage_analytics():
        """Aggregates Cloudinary and local storage statistics."""
        from django.conf import settings
        from apps.academia.models import ClassDocument, TeamSubmission, SubmissionFile
        import cloudinary.api
        import os

        # Initialize with defaults
        stats = {
            'total_files': 0,
            'usage': {'used': 0, 'limit': 1000, 'pct': 0},
            'bandwidth': {'used': 0, 'limit': 1000, 'pct': 0},
            'resources': 0,
            'plan': 'N/A',
            'portal_url': f"https://cloudinary.com/console/cloud/{settings.CLOUDINARY_STORAGE['CLOUD_NAME']}/media_library"
        }

        # 1. Cloudinary SDK Stats
        try:
            os.environ['CLOUDINARY_URL'] = f"cloudinary://{settings.CLOUDINARY_STORAGE['API_KEY']}:{settings.CLOUDINARY_STORAGE['API_SECRET']}@{settings.CLOUDINARY_STORAGE['CLOUD_NAME']}"
            usage = cloudinary.api.usage()
            stats['plan'] = usage.get('plan', 'Cloudinary Free')
            
            # Storage (MB)
            storage = usage.get('storage', {})
            stats['usage']['used'] = round(storage.get('usage', 0) / (1024 * 1024), 2)
            stats['usage']['limit'] = round(storage.get('limit', 0) / (1024 * 1024), 2)
            stats['usage']['pct'] = storage.get('used_percent', 0)
            
            # Bandwidth (MB)
            bw = usage.get('bandwidth', {})
            stats['bandwidth']['used'] = round(bw.get('usage', 0) / (1024 * 1024), 2)
            stats['bandwidth']['limit'] = round(bw.get('limit', 0) / (1024 * 1024), 2)
            stats['bandwidth']['pct'] = bw.get('used_percent', 0)
            
            stats['resources'] = usage.get('resources', 0)
        except:
            # Fallback to local size calculation
            local_size_mb = 0
            if os.path.exists(settings.MEDIA_ROOT):
                for dp, dn, filenames in os.walk(settings.MEDIA_ROOT):
                    for f in filenames:
                        local_size_mb += os.path.getsize(os.path.join(dp, f))
            local_size_mb /= (1024 * 1024)
            stats['usage']['used'] = round(local_size_mb, 2)
            stats['usage']['pct'] = min(100, round((local_size_mb / stats['usage']['limit']) * 100, 1))

        # 2. File Count Aggregation
        doc_count = ClassDocument.objects.count()
        sub_count = SubmissionFile.objects.count()
        main_sub_count = TeamSubmission.objects.exclude(file='').count()
        
        stats['total_files'] = doc_count + sub_count + main_sub_count
        
        return stats
    
    @staticmethod
    def send_system_error_alert(error_instance):
        """Sends an HTML email alert when a system error occurs with smart throttling."""
        from apps.core.services.notification_service import NotificationService
        
        # We throttle identical errors for 10 minutes to prevent email storms
        if NotificationService.should_throttle('system_error', error_instance.message, cooldown_minutes=10):
            return
            
        send_html_email(
            subject="CRITICAL: Runtime Application Error",
            template_name='core/emails/system_alert.html',
            context={
                'alert_title': 'Runtime Application Error Detected',
                'error_message': error_instance.message,
                'timestamp': error_instance.timestamp,
                'module': 'Django Web App',
                'url': error_instance.url,
                'user': error_instance.user.email if error_instance.user else 'Anonymous',
                'dashboard_url': 'http://localhost:8000/dev-dashboard/'
            },
            recipient_list=['sub2pewds10102005@gmail.com']
        )

    @staticmethod
    def get_system_analytics(pulses_window=100, bypass_cache=False):
        """Calculates advanced metrics from system pulses and error logs with 5-minute caching."""
        cache_key = f'system_analytics_{pulses_window}'
        
        if not bypass_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                # We need to refresh the pulse objects since they might be stale in a different context,
                # but for rapid dashboard refreshes, this is a massive performance win.
                return cached_data

        pulses = list(SystemPulse.objects.all()[:pulses_window])
        advanced_insights = []
        health_score = 100
        
        if not pulses:
            res = {
                "pulses": [], 
                "insights": [], 
                "health": 100, 
                "momentum": "UNKNOWN",
                "severity": "success",
                "message": "Collecting telemetry...",
                "volatility": 0,
                "consistency": 100
            }
            cache.set(cache_key, res, 300)
            return res

        # 1. Volatility Index (Jitter Detection)
        latencies = [p.latency for p in pulses]
        jitters = [abs(latencies[i] - latencies[i-1]) for i in range(1, len(latencies))]
        avg_volatility = sum(jitters) / len(jitters) if jitters else 0
        
        if avg_volatility > 200:
            advanced_insights.append({
                "type": "volatility", 
                "label": "High Volatility", 
                "text": f"Response jitter is elevated ({avg_volatility:.1f}ms).", 
                "icon": "bi-reception-2"
            })
            health_score -= 15
        else:
            advanced_insights.append({
                "type": "volatility", 
                "label": "Signal Stable", 
                "text": "Latency variance is within nominal limits.", 
                "icon": "bi-reception-4 text-success"
            })

        # 2. Consistency Index
        consistent_pulses = len([p for p in pulses if p.latency < 500 and p.status != 'DOWN'])
        consistency_pct = (consistent_pulses / len(pulses)) * 100
        
        if consistency_pct < 90:
            advanced_insights.append({
                "type": "consistency", 
                "label": "Consistency Drop", 
                "text": f"System fell below baseline for {100-consistency_pct:.0f}% of recent cycles.", 
                "icon": "bi-activity text-warning"
            })
            health_score -= 20

        # 3. Performance Momentum (Trend)
        momentum = "STABLE"
        current_window = latencies[:20]
        baseline_window = latencies[20:100]
        curr_avg = sum(current_window)/len(current_window) if current_window else 0
        base_avg = sum(baseline_window)/len(baseline_window) if baseline_window else 0
        if curr_avg < base_avg * 0.9: momentum = "IMPROVING"
        elif curr_avg > base_avg * 1.1: momentum = "DEGRADING"
        
        # 4. Friction Analysis
        hotspot = SystemError.objects.values('url').annotate(count=Count('id')).order_by('-count').first()
        if hotspot and hotspot['count'] > 2:
            advanced_insights.append({
                "type": "friction", 
                "label": "Service Friction", 
                "text": f"Recurrent failures detected on endpoint: {hotspot['url']}.", 
                "icon": "bi-exclamation-octagon text-danger"
            })
            health_score -= 10

        # Final Scoring & Insights
        health_score = max(5, min(100, health_score))
        severity = "success"
        if health_score < 70: severity = "warning"
        if health_score < 40 or any(p.status == 'DOWN' for p in pulses[:5]): severity = "danger"

        analysis_msg = "Infrastructure is operating at peak efficiency."
        if momentum == "DEGRADING" and health_score < 80:
            analysis_msg = "Degradation trend detected. Resource scaling or error audit recommended."
        elif health_score < 50:
            analysis_msg = "Critical performance degradation. Immediate intervention required."

        result = {
            "pulses": pulses,
            "insights": advanced_insights,
            "health": health_score,
            "momentum": momentum,
            "severity": severity,
            "message": analysis_msg,
            "volatility": avg_volatility,
            "consistency": consistency_pct,
            "cached_at": timezone.now()
        }
        
        cache.set(cache_key, result, 300) # Cache for 5 minutes
        return result

    @staticmethod
    def perform_health_check():
        """
        Self-healing automated logic. 
        Triggers emergency cleanup or alerts if health falls below threshold.
        """
        analytics = InfrastructureService.get_system_analytics(bypass_cache=True)
        health_score = analytics['health']
        
        # If health is critical, trigger an emergency recovery sequence
        if health_score < 40:
            # 1. Clear session cache to prevent possible memory pressure or stale state leaks
            cache.clear()
            
            # 2. Trigger high-priority administrative notification
            send_html_email(
                subject="URGENT: Automated System Recovery Triggered",
                template_name='core/emails/emergency_alert.html',
                context={
                    'health_score': health_score,
                    'message': "The system's health dropped below the 40% threshold. Automated recovery (Cache Flush) has been executed.",
                    'timestamp': timezone.now(),
                    'analytics': analytics
                },
                recipient_list=['sub2pewds10102005@gmail.com']
            )
            return "emergency_recovery_triggered"
            
        return "system_healthy"

    @staticmethod
    def is_protected_environment():
        """Detects if the current database is a protected cloud environment."""
        from django.conf import settings
        db_config = settings.DATABASES.get('default', {})
        db_url = db_config.get('NAME', '')
        db_host = db_config.get('HOST', '')
        
        protected_keywords = ['supabase', 'aws', 'rds', 'elephantsql', 'render', 'pooler']
        
        # Check both NAME and HOST
        is_cloud = any(key in str(db_url).lower() for key in protected_keywords) or \
                   any(key in str(db_host).lower() for key in protected_keywords)
        
        # Specifically check for supabase patterns
        is_supabase = 'supabase.com' in str(db_host).lower() or 'supabase.co' in str(db_host).lower()
        
        return is_cloud or is_supabase

    @staticmethod
    def validate_safe_operation(command_name):
        """Raises PermissionError if a destructive command is run on a protected DB without bypass."""
        import os
        if InfrastructureService.is_protected_environment():
            # List of dangerous commands to intercept
            destructive_commands = ['flush', 'reset_db', 'drop_schema', 'nuke']
            if command_name.lower() in destructive_commands:
                if os.getenv('SAFETY_VALVE_OPEN') != 'True':
                    raise PermissionError(
                        f"\n[!!!] CRITICAL SAFETY VIOLATION [!!!]\n"
                        f"Attempted '{command_name}' on a PROTECTED CLOUD DATABASE.\n"
                        f"Operation blocked by Infrastructure Sentinel.\n"
                        f"To bypass, set environment variable SAFETY_VALVE_OPEN=True."
                    )
