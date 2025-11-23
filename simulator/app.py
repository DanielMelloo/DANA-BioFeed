from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import requests
import threading
import time
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'simulator_secret'

# In-memory storage for simulated devices
# { id: SimulatedDevice }
DEVICES = {}

MAIN_API_URL = "http://localhost:5000/api"

class SimulatedDevice:
    def __init__(self, name, feeder_id, token=None, device_type='feeder'):
        self.id = str(uuid.uuid4())[:8] # Internal Simulator ID
        self.name = name
        self.feeder_id = feeder_id # Real DB ID (Feeder ID or Tank ID)
        self.token = token
        self.device_type = device_type # 'feeder', 'food_tank', 'water_tank'
        self.connected = False
        self.last_log = "Initialized"
        
        # Sensors (Feeder)
        self.battery_level = 100
        self.drawer_weight = 0.0
        
        # Sensors (Tank)
        self.tank_level = 100 # %
        self.tank_weight = 5.0 # kg (for food tank)
        
        # Internal State
        self.is_feeding = False
        self.is_refilling = False
        self.door_state = 'CLOSED' 
        
        # Thread control
        self.active = True
        self.thread = threading.Thread(target=self.run_loop)
        self.thread.daemon = True
        self.thread.start()

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.last_log = f"[{timestamp}] {message}"
        print(f"[{self.name}] {message}")

    def run_loop(self):
        while self.active:
            if self.token and self.feeder_id:
                try:
                    if self.device_type == 'feeder':
                        self.send_feeder_heartbeat()
                    else:
                        self.send_tank_heartbeat()
                except Exception as e:
                    self.connected = False
                    self.log(f"Connection Error: {e}")
            time.sleep(5) 

    def send_tank_heartbeat(self):
        # /api/tank/<id>/status
        payload = {
            'level': self.tank_level,
            'weight': self.tank_weight
        }
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            url = f"{MAIN_API_URL}/tank/{self.feeder_id}/status"
            response = requests.post(url, json=payload, headers=headers, timeout=2)
            
            if response.status_code == 200:
                self.connected = True
                self.log(f"Tank Data sent: {self.tank_level}%")
            else:
                self.connected = False
                self.log(f"API Error: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.connected = False
            self.log("Main API unreachable")

    def send_feeder_heartbeat(self):
        # Simulate the payload sent by the ESP32
        # Based on api_feed.py: /api/feeder/<id>/status
        
        # Determine sensor states based on weights/levels
        water_sensor_state = 'LSH'
        # For feeder, we don't simulate main tank level here anymore, 
        # but we simulate the internal water pill.
        # Let's assume internal water pill is OK unless we add a control for it.
        
        payload = {
            'battery': self.battery_level,
            'weight': self.drawer_weight,
            'water_sensor': water_sensor_state, # Internal Pill
            'firmware_version': '1.0.0-SIM'
        }
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            # Correct URL: /api/feeder/<id>/status
            url = f"{MAIN_API_URL}/feeder/{self.feeder_id}/status"
            response = requests.post(url, json=payload, headers=headers, timeout=2)
            
            if response.status_code == 200:
                self.connected = True
                self.log("Data sent successfully")
                
                # Check for commands in response
                data = response.json()
                if 'commands' in data and data['commands']:
                    for cmd in data['commands']:
                        self.handle_command(cmd)
            else:
                self.connected = False
                self.log(f"API Error: {response.status_code} - {response.text}")
        except requests.exceptions.ConnectionError:
            self.connected = False
            self.log("Main API unreachable")

    def handle_command(self, cmd):
        self.log(f"Received Command: {cmd['type']}")
        
        if cmd['type'] == 'feed':
            self.simulate_feed(cmd.get('duration', 1000))
        elif cmd['type'] == 'refill':
            self.simulate_refill(cmd.get('duration', 1000))
        elif cmd['type'] == 'water_refill':
            self.simulate_water_refill(cmd.get('duration', 5000))

    def simulate_feed(self, duration):
        def _feed():
            self.is_feeding = True
            self.door_state = 'OPEN'
            self.log("Feeding... (Door Open)")
            time.sleep(duration / 1000.0)
            self.door_state = 'CLOSED'
            self.drawer_weight = max(0, self.drawer_weight - 50) 
            self.is_feeding = False
            self.log("Feeding Done (Door Closed)")
            
            # Acknowledge command
            self.ack_command('feed', 'executed')
            
        threading.Thread(target=_feed).start()

    def simulate_refill(self, duration):
        def _refill():
            self.is_refilling = True
            self.log("Refilling Drawer...")
            time.sleep(duration / 1000.0)
            self.drawer_weight = min(500, self.drawer_weight + 210) 
            # Note: We don't decrease Main Tank level here anymore, 
            # because Main Tank is now a separate device!
            # In a real system, the Main Tank ESP would detect the drop.
            # For simulation, we might need to manually lower the tank level on the other simulator instance.
            self.is_refilling = False
            self.log("Refill Done")
            
            self.ack_command('refill', 'executed')
            
        threading.Thread(target=_refill).start()

    def simulate_water_refill(self, duration):
        def _water_refill():
            self.log("Refilling Water...")
            time.sleep(duration / 1000.0)
            # Same here, Main Tank level is separate.
            self.log("Water Refill Done")
            
            self.ack_command('water_refill', 'executed')
            
        threading.Thread(target=_water_refill).start()

    def ack_command(self, cmd_type, status):
        # /api/feeder/<id>/ack
        url = f"{MAIN_API_URL}/feeder/{self.feeder_id}/ack"
        headers = {'Authorization': f'Bearer {self.token}'}
        payload = {'command_id': 'sim-cmd', 'status': status} # Mock ID
        try:
            requests.post(url, json=payload, headers=headers, timeout=2)
        except:
            pass


@app.route('/')
def index():
    return render_template('index.html', devices=DEVICES)

@app.route('/create', methods=['POST'])
def create_device():
    name = request.form.get('name')
    feeder_id = request.form.get('feeder_id')
    token = request.form.get('token')
    device_type = request.form.get('device_type')
    device = SimulatedDevice(name, feeder_id, token, device_type)
    DEVICES[device.id] = device
    flash(f"Device {name} created!", "success")
    return redirect(url_for('index'))

@app.route('/device/<id>')
def device_control(id):
    device = DEVICES.get(id)
    if not device:
        return redirect(url_for('index'))
    return render_template('device.html', device=device)

@app.route('/device/<id>/update', methods=['POST'])
def update_device(id):
    device = DEVICES.get(id)
    if not device:
        return redirect(url_for('index'))
        
    device.token = request.form.get('token')
    
    if device.device_type == 'feeder':
        device.battery_level = int(request.form.get('battery_level'))
        device.drawer_weight = float(request.form.get('drawer_weight'))
    else:
        # Tank
        device.tank_level = int(request.form.get('tank_level'))
        device.tank_weight = float(request.form.get('tank_weight'))
    
    flash("Device state updated!", "success")
    return redirect(url_for('device_control', id=id))

@app.route('/device/<id>/delete', methods=['POST'])
def delete_device(id):
    if id in DEVICES:
        DEVICES[id].active = False
        del DEVICES[id]
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(port=5001, debug=True)
