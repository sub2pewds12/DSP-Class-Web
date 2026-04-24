import prometheus_client
from django.utils import timezone
import time

class TelemetryService:
    """
    Bridge between the Prometheus registry and the internal Django Dashboard.
    Allows us to extract real-time performance data without an external Grafana server.
    """

    @staticmethod
    def get_live_metrics():
        """
        Scrapes the local prometheus registry and returns a simplified dictionary 
        of current metrics.
        """
        metrics = list(prometheus_client.REGISTRY.collect())
        data = {
            'requests_total': 0,
            'responses_by_status': {},
            'avg_latency': 0,
            'db_queries_total': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }

        for m in metrics:
            # 1. Total Requests
            if m.name in ['django_http_requests_total_by_method', 'django_http_requests_before_middlewares']:
                # Filter out '_created' samples which are just timestamps
                data['requests_total'] = max(data['requests_total'], sum(
                    sample.value for sample in m.samples 
                    if not sample.name.endswith('_created')
                ))
            
            # 2. Status Codes
            if m.name in ['django_http_responses_total_by_status', 'django_http_responses_before_middlewares']:
                for sample in m.samples:
                    if sample.name.endswith('_created'):
                        continue
                    # Some versions use 'status', some use 'status_code'
                    status = sample.labels.get('status') or sample.labels.get('status_code') or 'unknown'
                    data['responses_by_status'][status] = data['responses_by_status'].get(status, 0) + sample.value

            # 3. Latency (Histogram)
            if m.name in ['django_http_requests_latency_seconds_by_view_method', 'django_http_requests_latency_including_middlewares_seconds']:
                # For histograms, prometheus_client returns samples with suffixes like _sum and _count
                sum_val = sum(s.value for s in m.samples if s.name.endswith('_sum'))
                count_val = sum(s.value for s in m.samples if s.name.endswith('_count'))
                
                if count_val > 0:
                    data['avg_latency'] = round((sum_val / count_val) * 1000, 2)

            # 4. Database Queries
            if m.name in ['django_db_query_duration_seconds', 'django_db_queries_total']:
                data['db_queries_total'] = sum(sample.value for sample in m.samples if sample.name.endswith('_count'))

        return data


    @staticmethod
    def record_pulse(status_code, latency_ms):
        """
        Records a single 'pulse' (request) into a rolling buffer in the cache.
        This provides the data for the '90-Day Uptime' (now 'Recent Traffic') histogram.
        """
        from django.core.cache import cache
        import math
        
        cache_key = 'telemetry_pulses_v2'
        pulses = cache.get(cache_key, [])
        
        # Determine status category
        status = 'OPERATIONAL'
        if status_code >= 500:
            status = 'DOWN'
        elif status_code >= 400:
            status = 'WARNING'
        elif latency_ms > 1000:
            status = 'CRITICAL'
            
        # Logarithmic height for the histogram bar (to make spikes visible but not overwhelming)
        # We use log10(latency + 1) normalized to a 0-100 scale
        log_h = min(100, max(5, math.log10(max(1, latency_ms)) * 25))
        
        new_pulse = {
            'timestamp': timezone.now(),
            'status': status,
            'latency': latency_ms,
            'log_h': log_h,
            'status_code': status_code
        }
        
        # Use a more robust cache interaction (atomic-ish)
        pulses.append(new_pulse)
        # Keep only the last 100 pulses
        if len(pulses) > 100:
            pulses = pulses[-100:]
            
        cache.set(cache_key, pulses, 86400) # Keep for 24h
        
        # Also update a 'last_updated' timestamp for the frontend
        cache.set('telemetry_last_updated', timezone.now(), 86400)

    @staticmethod
    def get_recent_pulses():
        """Retrieves the rolling buffer of pulses. Seeds with mock data if empty."""
        from django.core.cache import cache
        import random
        
        cache_key = 'telemetry_pulses_v2'
        pulses = cache.get(cache_key)
        
        if pulses is None or len(pulses) == 0:
            # Seed with 100 mock pulses representing a healthy system
            # This ensures the user sees a graph immediately on a fresh start
            seed_pulses = []
            now = timezone.now()
            for i in range(100):
                latency = random.uniform(20, 150) # Mostly fast
                if i % 20 == 0: latency = random.uniform(300, 800) # Occasional slow
                
                # Use the same logic as record_pulse
                import math
                log_h = min(100, max(5, math.log10(max(1, latency)) * 25))
                
                seed_pulses.append({
                    'timestamp': now - timezone.timedelta(minutes=(100-i)),
                    'status': 'OPERATIONAL' if latency < 1000 else 'CRITICAL',
                    'latency': latency,
                    'log_h': log_h,
                    'status_code': 200
                })
            cache.set(cache_key, seed_pulses, 86400)
            return seed_pulses
            
        return pulses

    @staticmethod
    def get_dashboard_context():
        """Returns a structure optimized for Chart.js in dev_dashboard.html"""
        metrics = TelemetryService.get_live_metrics()
        
        # Prepare Status Code Donut Data
        status_labels = list(metrics['responses_by_status'].keys())
        status_values = list(metrics['responses_by_status'].values())
        
        # Colors based on status code groups
        colors = []
        for s in status_labels:
            if s.startswith('2'): colors.append('#10b981') # Green
            elif s.startswith('4'): colors.append('#f59e0b') # Amber
            elif s.startswith('5'): colors.append('#ef4444') # Red
            else: colors.append('#6b7280') # Gray

        return {
            'summary': metrics,
            'charts': {
                'status_distribution': {
                    'labels': status_labels,
                    'data': status_values,
                    'colors': colors
                }
            },
            'pulses': TelemetryService.get_recent_pulses(),
            'log_benchmarks': [
                {'pos': 0, 'label': '0ms'},
                {'pos': 25, 'label': '10ms'},
                {'pos': 50, 'label': '100ms'},
                {'pos': 75, 'label': '1s'},
                {'pos': 100, 'label': '10s'}
            ]
        }
