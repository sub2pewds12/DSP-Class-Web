import os
import requests
from dotenv import load_dotenv

load_dotenv()

def list_datasources():
    url = os.getenv('GRAFANA_CLOUD_URL').rstrip('/') + "/api/datasources"
    token = os.getenv('GRAFANA_CLOUD_API_TOKEN')
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"Connecting to {url}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        ds_list = response.json()
        print("\n--- FOUND DATA SOURCES ---")
        for ds in ds_list:
            print(f"Name: {ds['name']} | Type: {ds['type']} | UID: {ds['uid']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    list_datasources()
