# System Resilience & Infrastructure Caching

To ensure the platform remains stable under heavy administrative load or during peak student registration periods, we have implemented several production-grade resilience patterns.

## ⚡ Analytics Caching
The **Developer Dashboard** and **System Analytics** endpoints utilize a 5-minute caching layer (`default` cache backend).

- **Performance Goal**: Dashboard telemetry (latencies, consistency jitters, and error hotspots) are expensive to calculate across the entire database.
- **Implementation**: `InfrastructureService.get_system_analytics` checks for a cached result before querying models.
- **Manual Bypass**: Administrators can bypass the cache for a "real-time" view by clicking the "Refresh" button (which triggers the API with `bypass_cache=True`).

## 📊 Traffic Pulse & NOC Telemetry
The **Traffic Pulse** histogram provides a high-density, real-time visualization of every request processed by the platform. This NOC-style view allows for immediate identification of performance jitter and "bursty" traffic patterns.

### 1. Dual-Scale Visualization
Administrators can toggle between two scaling modes to suit different diagnostic needs:
- **Linear Mode (LIN)**: Maps latency directly (0ms - 1000ms). Best for identifying small fluctuations in healthy traffic.
- **Logarithmic Mode (LOG)**: Uses a base-10 scale to visualize latencies from 1ms up to 10 seconds. This is the preferred mode for "hunting" high-latency outliers (spikes) that would otherwise disappear on a linear scale.

### 2. Heatmap Engine
The bars are dynamically color-coded based on severity:
- **Emerald Green**: Healthy, fast responses (< 200ms).
- **Amber/Orange**: Elevated latency (500ms - 900ms).
- **Vibrant Red**: Performance bottleneck (> 1000ms).
- **Blue Tint**: System requests (heartbeats/telemetry) are often filtered or tinted to reduce noise.

### 3. Real-time Middleware
The `ActivityTrackingMiddleware` records the duration and status of every request (excluding `/static/` assets and the telemetry endpoint itself) into a rolling 100-pulse buffer. This buffer is stored in the cache for maximum speed and zero database overhead.

## 🦾 Self-Healing Engine
The system proactively monitors its own health scores via the `perform_health_check` logic.

### 1. Health Thresholds
- **90%+**: Optimal Performance.
- **70% - 89%**: Warning: Elevated jitter or latency detected.
- **< 40%**: **Critical**: System recovery sequence triggered.

### 2. Automated Recovery Actions
When health falls below the **40% threshold**, the system automatically executes:
1. **Cache Flush**: Clears non-essential caches to release memory pressure and remove potentially stale or corrupted state.
2. **Emergency Alert**: Sends a high-priority HTML email to the system administrator with a full diagnostic dump of the current telemetry.
3. **Incident Sanitizer**: The system uses a concurrent probing engine to automatically resolve incidents where the target URL has returned to a healthy state (HTTP 200).

## 🗄️ Storage Integrity
To prevent media storage bloat, the academic engine maintains a "one-team-one-slot" policy:
- **Automatic Purging**: When a student makes a new submission, the service physically deletes all previous `TeamSubmission` records and files for that specific assignment.
- **Atomic Transactions**: Deletions and new creations are wrapped in a database transaction to ensure no data is lost during the replacement process.

## 👻 Ghost Heartbeat Integration
The resilience engine is integrated into the background heartbeat loop. Every 5 minutes (5 iterations), the heartbeat automatically triggers a health check, ensuring the system remains self-aware even when no administrators are actively monitoring the dashboard.

## 🗄️ Database Connection Management
To prevent connection exhaustion on pooled database services (like Supabase Transaction Pooler), we implement strict session management:

- **Short-Lived Connections**: In high-density environments, we set `CONN_MAX_AGE = 0` to ensure Django closes database connections immediately after each request. This prevents "Idle" connections from filling the pool.
- **PGBouncer Compatibility**: The system is optimized for transaction-level pooling, ensuring high availability even under concurrent API bursts.
- **Latency Tracking**: Every connection attempt is timed by the heartbeat to detect networking jitter before it impacts end-user experience.
