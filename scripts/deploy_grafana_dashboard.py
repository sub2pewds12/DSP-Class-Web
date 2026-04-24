import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def deploy_dashboard():
    # Configuration
    GRAFANA_URL = os.getenv('GRAFANA_CLOUD_URL', 'https://sub2pewds12.grafana.net/').rstrip('/')
    API_TOKEN = os.getenv('GRAFANA_CLOUD_API_TOKEN')
    
    if not API_TOKEN:
        print("Error: GRAFANA_CLOUD_API_TOKEN not found in .env")
        return

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Dashboard Definition
    dashboard = {
        "dashboard": {
            "id": None,
            "uid": "dsp-v3",
            "title": "🚀 DSP Web: Command Center",
            "tags": ["django", "production", "telemetry"],
            "timezone": "browser",
            "panels": [
                # PANEL 1: Total Traffic (Stat)
                {
                    "title": "Total Requests",
                    "type": "stat",
                    "datasource": {"type": "prometheus", "uid": "grafanacloud-prom"},
                    "gridPos": {"h": 4, "w": 8, "x": 0, "y": 0},
                    "targets": [{"expr": "sum(dsp_v3_requests)", "refId": "A"}],
                    "options": {
                        "colorMode": "value",
                        "graphMode": "area",
                        "justifyMode": "center"
                    },
                    "fieldConfig": {
                        "defaults": {"color": {"mode": "palette-classic"}, "unit": "none"}
                    }
                },
                # PANEL 2: Avg Latency (Stat)
                {
                    "title": "Avg Latency",
                    "type": "stat",
                    "datasource": {"type": "prometheus", "uid": "grafanacloud-prom"},
                    "gridPos": {"h": 4, "w": 8, "x": 8, "y": 0},
                    "targets": [{"expr": "avg(dsp_v3_latency)", "refId": "A"}],
                    "options": {
                        "colorMode": "background",
                        "graphMode": "area",
                        "justifyMode": "center"
                    },
                    "fieldConfig": {
                        "defaults": {
                            "unit": "ms",
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "orange", "value": 200},
                                    {"color": "red", "value": 500}
                                ]
                            }
                        }
                    }
                },
                # PANEL 3: DB Operations (Stat)
                {
                    "title": "DB Ops",
                    "type": "stat",
                    "datasource": {"type": "prometheus", "uid": "grafanacloud-prom"},
                    "gridPos": {"h": 4, "w": 8, "x": 16, "y": 0},
                    "targets": [{"expr": "sum(dsp_v3_db_ops)", "refId": "A"}],
                    "options": {
                        "colorMode": "value",
                        "graphMode": "area",
                        "justifyMode": "center"
                    },
                    "fieldConfig": {
                        "defaults": {"color": {"mode": "palette-classic"}, "unit": "none"}
                    }
                },
                # PANEL 4: Traffic Trend (Time Series)
                {
                    "title": "Real-time Traffic Momentum",
                    "type": "timeseries",
                    "datasource": {"type": "prometheus", "uid": "grafanacloud-prom"},
                    "gridPos": {"h": 8, "w": 24, "x": 0, "y": 4},
                    "targets": [
                        {"expr": "rate(dsp_v3_requests[2m])", "legendFormat": "Requests/sec", "refId": "A"}
                    ],
                    "options": {
                        "legend": {"displayMode": "table", "placement": "bottom"},
                        "tooltip": {"mode": "single"}
                    },
                    "fieldConfig": {
                        "defaults": {
                            "custom": {"drawStyle": "line", "pointSize": 5, "lineWidth": 2, "fillOpacity": 10},
                            "unit": "reqps"
                        }
                    }
                },
                # PANEL 5: Status Codes (Pie Chart)
                {
                    "title": "HTTP Status Codes",
                    "type": "piechart",
                    "datasource": {"type": "prometheus", "uid": "grafanacloud-prom"},
                    "gridPos": {"h": 8, "w": 8, "x": 0, "y": 12},
                    "targets": [
                        {"expr": "sum by(status) (dsp_v3_responses_count)", "legendFormat": "HTTP {{status}}", "refId": "A"}
                    ],
                    "options": {
                        "pieType": "pie",
                        "legend": {
                            "displayMode": "table",
                            "placement": "right"
                        },
                        "tooltip": {"mode": "single"}
                    }
                },
                # PANEL 6: Database Operations Trend (Time Series)
                {
                    "title": "Database Operations Momentum",
                    "type": "timeseries",
                    "datasource": {"type": "prometheus", "uid": "grafanacloud-prom"},
                    "gridPos": {"h": 8, "w": 16, "x": 8, "y": 12},
                    "targets": [
                        {"expr": "rate(dsp_v3_db_ops[2m])", "legendFormat": "Queries/sec", "refId": "A"}
                    ],
                    "options": {
                        "legend": {"displayMode": "table", "placement": "bottom"},
                        "tooltip": {"mode": "single"}
                    },
                    "fieldConfig": {
                        "defaults": {
                            "custom": {"drawStyle": "line", "pointSize": 5, "lineWidth": 2, "fillOpacity": 10},
                            "unit": "reqps",
                            "color": {"mode": "fixed", "fixedColor": "purple"}
                        }
                    }
                },
                # PANEL 7: Cloudinary Portal Link
                {
                    "title": "External Portals",
                    "type": "text",
                    "gridPos": {"h": 4, "w": 24, "x": 0, "y": 20},
                    "options": {
                        "content": f"# Cloudinary Dashboard\n\n<a href='https://cloudinary.com/console/cloud/{os.getenv('CLOUDINARY_CLOUD_NAME', 'dev_cloud')}/media_library' target='_blank' style='font-size: 1.5em; text-decoration: none; color: #ff5722;'>🔗 Go to Cloudinary Media Library</a>",
                        "mode": "markdown"
                    }
                }
            ],
            "schemaVersion": 36,
            "version": 1
        },
        "overwrite": True
    }

    print(f"Deploying to {GRAFANA_URL}...")
    
    # Push to API
    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        headers=headers,
        json=dashboard
    )

    if response.status_code == 200:
        data = response.json()
        print("\n--- DASHBOARD DEPLOYED SUCCESSFULLY ---")
        print(f"URL: {GRAFANA_URL}{data['url']}")
    else:
        print(f"\n--- FAILED TO DEPLOY: {response.status_code} ---")
        print(response.text)
        print("\nNote: Your API token might not have 'Editor' permissions.")
        print("Try generating a 'Service Account Token' with Admin rights if this persists.")

if __name__ == "__main__":
    deploy_dashboard()
