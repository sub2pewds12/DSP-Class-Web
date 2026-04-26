# System Resilience & Infrastructure Caching

To ensure the platform remains stable under heavy administrative load or during peak student registration periods, we have implemented several production-grade resilience patterns.

## ⚡ Analytics Caching
The **Developer Dashboard** and **System Analytics** endpoints utilize a 5-minute caching layer (`default` cache backend).

- **Performance Goal**: Dashboard telemetry (latencies, consistency jitters, and error hotspots) are expensive to calculate across the entire database.
- **Implementation**: `InfrastructureService.get_system_analytics` checks for a cached result before querying models.
- **Manual Bypass**: Administrators can bypass the cache for a "real-time" view by clicking the "Refresh" button (which triggers the API with `bypass_cache=True`).

## 📊 Traffic Pulse & NOC Telemetry
The **Traffic Pulse** histogram provides a high-density, real-time visualization of every request processed by the platform. This NOC-style view allows for immediate identification of performance jitter and "bursty" traffic patterns.

### 1. Advanced Scaling Controls
Administrators can surgically adjust the visualization depth and bounds via integrated header controls:
- **VIEW (X-Axis)**: Toggle history density between **25, 50, 75, or 100 pulses**. Defaults to 100 for high-density visibility.
- **CAP (Y-Axis)**: Scale the vertical linear range between **250ms, 500ms, 1s, 2s, or 5s**. This allows for high-resolution monitoring of high-performance endpoints.
- **Dual Mode**: Seamlessly switch between **Linear (LIN)** and **Logarithmic (LOG)** scales. LOG mode visualizations cover 1ms to 10s on a base-10 scale.

### 2. High-Fidelity Heatmap
The bars use a continuous HSL hue interpolation engine:
- **Green (120°)**: Healthy (< 100ms).
- **Yellow (60°)**: Trending elevated (250ms - 500ms).
- **Red (0°)**: Critical bottleneck (> 1000ms).
- **Interpolation**: Colors transition smoothly through the spectrum based on actual latency, providing immediate intuitive feedback on performance "drift."

### 3. Real-time Middleware & Buffer
The `ActivityTrackingMiddleware` records the duration and status of every request into a high-capacity rolling **100-pulse buffer**. 
- **Storage**: In-memory cache for sub-millisecond overhead.
- **Exclusion**: Static assets and telemetry requests are filtered to maintain data purity.
- **Persistence**: Data is retained as long as the cache survives, providing historical context across administrative sessions.

## 🤖 AI-Powered Incident Management

The platform is integrated with **Google Gemini (AI Service)** to provide human-readable, professional incident reports during system degradations. This replaces generic automated messages with context-aware SITREP (Situation Report) updates.

### 1. Context-Aware Generation
When a performance incident is detected (e.g., high database latency or elevated error rates), the AI analyzes the raw telemetry data (health score, latency, error percentages) and generates a concise summary for the **Statuspage**.

### 2. "Safe AI" Architecture (Rate Limiting)
To prevent API cost bloat and redundant reporting, the AI service is governed by a **4-hour state lock**:
- **Trigger**: AI only runs on the *initial* detection of an incident.
- **Cooldown**: Once a report is generated, the AI service locks itself for 4 hours. Subsequent health checks will use the existing report or fallback to cached data.
- **Fail-safe**: If the AI API is unreachable or rate-limited, the system automatically falls back to hardcoded, professional templates.

## 🦾 Self-Healing Engine
The system proactively monitors its own health scores via the `perform_health_check` logic.

### 1. Health Thresholds
- **90%+**: Optimal Performance.
- **70% - 89%**: Warning: Elevated jitter or latency detected.
- **< 40%**: **Critical**: System recovery sequence triggered.

### 2. Automated Recovery Actions
When health falls below the **40% threshold**, the system automatically executes:
1. **AI SITREP**: Triggers the `AIService` to generate a professional incident report based on current failure metrics.
2. **Statuspage Broadcast**: Updates the public Statuspage with the AI-generated SITREP and sets the affected components to 'Major Outage'.
3. **Cache Flush**: Clears non-essential caches to release memory pressure and remove potentially stale or corrupted state.
4. **Emergency Alert**: Sends a high-priority HTML email to the system administrator with the AI report and a full diagnostic dump.

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
