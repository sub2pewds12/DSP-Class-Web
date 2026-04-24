import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.environ.get('GRAFANA_CLOUD_URL').rstrip('/') + '/api/datasources/proxy/uid/grafanacloud-prom/api/v1/label/__name__/values'
token = os.environ.get('GRAFANA_CLOUD_API_TOKEN')
resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
print(resp.status_code)
if resp.status_code == 200:
    metrics = resp.json().get('data', [])
    print("Found metrics:", [m for m in metrics if 'dsp' in m])
else:
    print(resp.text)
