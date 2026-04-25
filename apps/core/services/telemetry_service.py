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
        if status_code == 204:
            status = 'NO_CONTENT'
        elif status_code >= 500:
            status = 'DOWN'
        elif status_code >= 400:
            status = 'WARNING'
        elif latency_ms > 1000:
            status = 'CRITICAL'
            
        # Intensity for coloring (0 = Green, 100 = Red)
        if status_code >= 500 or status == 'CRITICAL':
            intensity = 100
        elif status_code >= 400:
            intensity = 60 # Amber-ish
        elif status_code == 204:
            intensity = 30 # Sky Blue intensity
        else:
            # Scale latency 0-1000ms to intensity 0-100
            intensity = min(100, (latency_ms / 1000) * 100)

        # Calculate HSL color based on intensity
        # 140 (Green) -> 0 (Red)
        hue = max(0, 140 - (1.4 * intensity))
        color = f"hsl({hue}, 80%, 50%)"
        base_color = f"hsl({hue}, 40%, 20%)"

        # Logarithmic height for histogram (1ms to 10s range)
        # 1ms=0%, 10ms=25%, 100ms=50%, 1000ms=75%, 10000ms=100%
        if latency_ms <= 1:
            log_h = 2
            lin_h = 2
        else:
            log_h = max(2, min(100, math.log10(latency_ms) * 25))
            # Linear height (0ms to 1000ms)
            lin_h = max(2, min(100, (latency_ms / 1000) * 100))

        new_pulse = {
            'timestamp': timezone.now(),
            'status': status,
            'latency': latency_ms,
            'log_h': log_h,
            'lin_h': lin_h,
            'status_code': status_code,
            'intensity': round(intensity, 1),
            'color': color,
            'base_color': base_color
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
            from django.conf import settings
            if not settings.DEBUG:
                return []
                
            # Seed with 100 mock pulses representing a healthy system
            seed_pulses = []
            now = timezone.now()
            for i in range(100):
                latency = random.uniform(20, 150) # Mostly fast
                if i % 20 == 0: latency = random.uniform(300, 800) # Occasional slow
                
                # Use the same logic as record_pulse
                import math
                log_h = min(100, max(5, math.log10(max(1, latency)) * 25))
                
                intensity = min(100, (latency / 1000) * 100)
                if latency > 1000: intensity = 100

                hue = max(0, 140 - (1.4 * intensity))
                color = f"hsl({hue}, 80%, 50%)"
                base_color = f"hsl({hue}, 40%, 20%)"

                seed_pulses.append({
                    'timestamp': now - timezone.timedelta(minutes=(100-i)),
                    'status': 'OPERATIONAL' if latency < 1000 else 'CRITICAL',
                    'latency': latency,
                    'log_h': min(100, max(5, math.log10(max(1, latency)) * 25)),
                    'lin_h': min(100, max(5, (latency / 1000) * 100)),
                    'status_code': 200,
                    'intensity': round(intensity, 1),
                    'color': color,
                    'base_color': base_color
                })
            cache.set(cache_key, seed_pulses, 86400)
            return seed_pulses
            
        return pulses

    @staticmethod
    def get_dashboard_context():
        """Returns a structure optimized for Chart.js in dev_dashboard.html"""
        metrics = TelemetryService.get_live_metrics()
        
        # Standard status categories for a "full" legend
        standard_categories = [
            ('200 Success', '#10b981'),  # Emerald
            ('201 Created', '#059669'),  # Dark Green
            ('204 No Content', '#0ea5e9'), # Sky Blue (Distinct from Emerald)
            ('4xx Client Error', '#f59e0b'), # Amber
            ('5xx Server Error', '#ef4444'), # Red
        ]

        status_labels = []
        status_values = []
        colors = []

        resp_map = metrics.get('responses_by_status', {})

        # Populate standard categories
        for label, color in standard_categories:
            val = 0
            if '200' in label: val = resp_map.get('200', 0)
            elif '201' in label: val = resp_map.get('201', 0)
            elif '204' in label: val = resp_map.get('204', 0)
            elif '4xx' in label: val = sum(v for k, v in resp_map.items() if k.startswith('4'))
            elif '5xx' in label: val = sum(v for k, v in resp_map.items() if k.startswith('5'))
            
            status_labels.append(label)
            status_values.append(val)
            colors.append(color)

        # Add "Other" if there are any other status codes recorded
        other_val = sum(v for k, v in resp_map.items() if k not in ['200', '201', '204'] and not k.startswith('4') and not k.startswith('5'))
        if other_val > 0:
            status_labels.append('Other')
            status_values.append(other_val)
            colors.append('#6b7280')

        # Add "In Flight" if requests > responses
        status_total = sum(status_values)
        if metrics['requests_total'] > status_total:
            pending = metrics['requests_total'] - status_total
            status_labels.append('In Flight')
            status_values.append(pending)
            colors.append('#94a3b8')

        # X-Axis Time Labels
        pulses = TelemetryService.get_recent_pulses()
        time_labels = []
        if pulses:
            indices = [0, len(pulses)//2, len(pulses)-1]
            for idx in indices:
                if 0 <= idx < len(pulses):
                    time_labels.append(pulses[idx]['timestamp'])

        return {
            'summary': metrics,
            'charts': {
                'status_distribution': {
                    'labels': status_labels,
                    'data': status_values,
                    'colors': colors
                }
            },
            'pulses': pulses,
            'time_labels': time_labels,
            'log_benchmarks': [
                {'pos': 0, 'label': '0ms'},
                {'pos': 25, 'label': '10ms'},
                {'pos': 50, 'label': '100ms'},
                {'pos': 75, 'label': '1s'},
                {'pos': 100, 'label': '10s'}
            ],
            'lin_benchmarks': [
                {'pos': 0, 'label': '0ms'},
                {'pos': 25, 'label': '250ms'},
                {'pos': 50, 'label': '500ms'},
                {'pos': 75, 'label': '750ms'},
                {'pos': 100, 'label': '1s'}
            ]
        }
