# System Resilience & Infrastructure Caching

To ensure the platform remains stable under heavy administrative load or during peak student registration periods, we have implemented several production-grade resilience patterns.

## ⚡ Analytics Caching
The **Developer Dashboard** and **System Analytics** endpoints utilize a 5-minute caching layer (`default` cache backend).

- **Performance Goal**: Dashboard telemetry (latencies, consistency jitters, and error hotspots) are expensive to calculate across the entire database.
- **Implementation**: `InfrastructureService.get_system_analytics` checks for a cached result before querying models.
- **Manual Bypass**: Administrators can bypass the cache for a "real-time" view by clicking the "Refresh" button (which triggers the API with `bypass_cache=True`).

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

## 👻 Ghost Heartbeat Integration
The resilience engine is integrated into the background heartbeat loop. Every 5 minutes (5 iterations), the heartbeat automatically triggers a health check, ensuring the system remains self-aware even when no administrators are actively monitoring the dashboard.
