import time
import threading
from django.db import connection, OperationalError
from django.utils import timezone
from django.core.cache import cache
from teams.models import SystemPulse

def execute_pulse():
    """Core logic to check DB latency and log a system pulse.
    Prioritizes the 'production' database alias to ensure real-world tracking.
    """
    from django.db import connections
    
    # Use 'production' alias if PROD_DB_URL is configured, otherwise fallback to 'default'
    db_alias = 'production' if 'production' in connections else 'default'
    conn = connections[db_alias]

    start_time = time.perf_counter()
    try:
        conn.ensure_connection()
        status = 'OPERATIONAL'
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        
        latency = (time.perf_counter() - start_time) * 1000
        
        # Ensure we never show absolute 0.0ms for readability/trust
        if latency < 0.1: latency = 0.1
        
        if latency > 1000: status = 'WARNING'
        if latency > 5000: status = 'CRITICAL'

        # Log identifying the target DB so the dashboard knows it was a production check
        info = f"Target: {db_alias.upper()}"
        SystemPulse.objects.create(status=status, latency=latency, info=info)
        return status, latency
    except Exception as e:
        latency = (time.perf_counter() - start_time) * 1000
        SystemPulse.objects.create(status='DOWN', latency=latency, info=str(e))
        return 'DOWN', latency

def prune_old_pulses(hours=48):
    """Keep the health history lean by removing old records."""
    cutoff = timezone.now() - timezone.timedelta(hours=hours)
    SystemPulse.objects.filter(timestamp__lt=cutoff).delete()

def start_ghost_heartbeat():
    """Starts the background loop within the web process if not already running."""
    # Use cache to ensure only one thread runs across potential multiple worker processes
    # if the cache backend is shared (like Redis). If local memory, it's per-process.
    if cache.get('heartbeat_is_running'):
        return

    thread = threading.Thread(target=_ghost_loop, daemon=True)
    thread.start()

def _ghost_loop():
    """The background loop that performs the heartbeat checks."""
    iteration = 0
    while True:
        # Mark heartbeat as active for slightly more than the sleep interval
        cache.set('heartbeat_is_running', True, 75)
        
        last_activity = cache.get('last_system_activity')
        now = timezone.now()
        
        # 30-minute grace period per user request
        is_active = True
        if last_activity:
            idle_time = (now - last_activity).total_seconds()
            if idle_time > 1800: # 30 minutes
                is_active = False
        else:
            # If no activity recorded yet, we check once and then probably idle
            is_active = False

        if is_active:
            execute_pulse()
        else:
            # Shutdown the thread if idle too long
            cache.delete('heartbeat_is_running')
            break

        # Prune every 30 minutes
        iteration += 1
        if iteration % 30 == 0:
            prune_old_pulses()

        time.sleep(60)
