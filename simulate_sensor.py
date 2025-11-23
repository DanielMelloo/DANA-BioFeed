import requests
import json
import time

BASE_URL = 'http://localhost:5000'

def register_feeder():
    print("Registering Feeder...")
    resp = requests.post(f'{BASE_URL}/api/feeder/register', json={'name': 'Sensor Feeder'})
    if resp.status_code == 200:
        data = resp.json()
        print(f"Registered: ID={data['id']}, Token={data['token']}")
        return data['id'], data['token']
    else:
        print("Registration Failed:", resp.text)
        return None, None

def report_status(feeder_id, token, weight, water_sensor='LSH', battery=100):
    url = f'{BASE_URL}/api/feeder/{feeder_id}/status'
    headers = {'x-access-token': token}
    payload = {
        'weight': weight,
        'water_sensor': water_sensor,
        'battery': battery,
        'firmware_version': '1.0.0'
    }
    print(f"Reporting Weight: {weight}g, Water: {water_sensor}...")
    try:
        resp = requests.post(url, json=payload, headers=headers)
        print(f"Response ({resp.status_code}): {resp.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fid, token = register_feeder()
    if fid:
        # 1. Normal (210g, Water OK)
        report_status(fid, token, 210, 'LSH')
        time.sleep(1)
        
        # 2. Food Warning (80g, Water OK)
        report_status(fid, token, 80, 'LSH')
        time.sleep(1)
        
        # 3. Water Critical (210g, Water LSLL) -> Should trigger water_refill if tank linked
        report_status(fid, token, 210, 'LSLL')
        time.sleep(1)

        # 4. Food Critical (20g, Water OK) -> Should trigger refill
        report_status(fid, token, 20, 'LSH')
