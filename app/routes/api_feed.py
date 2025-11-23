from flask import Blueprint, request, jsonify
from database import db
from app.models.feeder import Feeder
from app.models.log import Log
from app.services.auth import token_required
from app.services.command_bus import CommandBus
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/feeder/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    feeder = Feeder(name=data['name'])
    db.session.add(feeder)
    db.session.commit()
    
    return jsonify({
        'id': feeder.id,
        'token': feeder.token,
        'message': 'Registered successfully'
    })

@api_bp.route('/feeder/<int:id>/config', methods=['GET'])
@token_required
def get_config(feeder, id):
    if feeder.id != id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    feeder.last_seen = datetime.utcnow()
    feeder.online = True
    db.session.commit()

    return jsonify({
        'interval_seconds': feeder.interval_seconds,
        'open_duration_ms': feeder.open_duration_ms,
        'next_run': feeder.next_run.timestamp() if feeder.next_run else 0
    })

@api_bp.route('/feeder/<int:id>/status', methods=['POST'])
@token_required
def report_status(feeder, id):
    if feeder.id != id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update feeder status
    feeder.last_seen = datetime.utcnow()
    feeder.online = True
    if 'firmware_version' in data:
        feeder.firmware_version = data.get('firmware_version')
    if 'battery' in data:
        feeder.battery_level = data.get('battery')

    # --- Advanced Sensor Logic ---
    # 1. Food Scale Logic
    if 'weight' in data:
        weight = float(data['weight'])
        feeder.drawer_weight = weight
        
        # Thresholds
        target = feeder.target_weight or 210.0
        warning = feeder.warning_weight or 80.0
        critical = feeder.critical_weight or 20.0
        
        if weight > warning:
            new_state = 'LSH'
            new_status = 'NORMAL'
        elif weight > critical:
            new_state = 'LSL'
            new_status = 'WARNING'
        else:
            new_state = 'LSLL'
            new_status = 'CRITICAL'

        if feeder.status != 'TRIP':
            # Check for LSLL persistence (Fault 1)
            if new_state == 'LSLL':
                # Trigger Auto-Refill (Action for LSLL)
                if not feeder.is_locked:
                    # Check Main Food Tank Level (if linked)
                    can_refill = True
                    if feeder.food_tank:
                        if feeder.food_tank.level <= 5: # Arbitrary 5% threshold
                            can_refill = False
                            print(f"Feeder {feeder.id}: Food LSLL but Main Food Tank Empty!")
                            # Could trigger notification
                    
                    if can_refill:
                        # Send Multi-dose refill command
                        # We want to fill 1 unit (target_weight)
                        CommandBus.add_command(feeder.id, {
                            'type': 'refill', 
                            'units': 1, 
                            'unit_weight': feeder.target_weight,
                            'duration': feeder.open_duration_ms
                        }) 
                        print(f"Feeder {feeder.id}: Food LSLL. Attempting auto-refill.")

            feeder.sensor_state = new_state
            feeder.status = new_status

    # 2. Water Sensor Logic
    if 'water_sensor' in data:
        # Expecting 'LSH' or 'LSLL'
        w_state = data['water_sensor']
        feeder.water_sensor_state = w_state
        
        if w_state == 'LSLL':
            # Water Critical -> Attempt Refill
            if not feeder.water_locked:
                # Check Main Water Tank Level (if linked)
                if feeder.water_tank: # This is the "Main Water Tank"
                    # Check if Main Tank is empty (using level or weight)
                    if feeder.water_tank.level > 5: # Arbitrary 5% threshold
                        # Open Solenoid
                        CommandBus.add_command(feeder.id, {
                            'type': 'water_refill',
                            'duration': 5000 # Open for 5 seconds (configurable?)
                        })
                        print(f"Feeder {feeder.id}: Water LSLL. Refilling from {feeder.water_tank.name}.")
                    else:
                        print(f"Feeder {feeder.id}: Water LSLL but Main Water Tank Empty!")
                        # Could trigger a notification here
                else:
                     print(f"Feeder {feeder.id}: Water LSLL but no Main Water Tank linked.")

    db.session.commit()
    
    # Check for pending commands
    commands = CommandBus.get_commands(feeder.id)
    
    return jsonify({
        "status": "ok", 
        "commands": commands,
        "feeder_status": feeder.status
    })

@api_bp.route('/feeder/<int:id>/command', methods=['GET'])
@token_required
def get_command(feeder, id):
    if feeder.id != id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    commands = CommandBus.get_commands(id)
    return jsonify({'commands': commands})

@api_bp.route('/feeder/<int:id>/ack', methods=['POST'])
@token_required
def ack_command(feeder, id):
    if feeder.id != id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    cmd_id = data.get('command_id')
    status = data.get('status')
    
    # Log the execution
    if status == 'executed':
        # If it was a feed command, log it
        # In a real app, we'd match the command ID to know what it was.
        # For simplicity, we assume if we get an ACK it might be a feed.
        # But better to just log explicit feed reports or infer from command type.
        pass

    return jsonify({'status': 'ack_received'})

# Endpoint to log feed events from ESP32 (optional, if not covered by status)
@api_bp.route('/feeder/<int:id>/log', methods=['POST'])
@token_required
def log_event(feeder, id):
    if feeder.id != id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    action = data.get('action', 'auto')
    duration = data.get('duration_ms', 0)
    
    log = Log(feeder_id=id, action=action, duration_ms=duration)
    db.session.add(log)
    
    feeder.last_run = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'status': 'logged'})
    return jsonify({'status': 'logged'})

# --- Tank API Routes ---

from app.models.tank import Tank

@api_bp.route('/tank/<int:id>/status', methods=['POST'])
def report_tank_status(id):
    # Simple Token Auth for Tanks
    token = None
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
    
    if not token:
        return jsonify({'error': 'Token missing'}), 401

    tank = Tank.query.get_or_404(id)
    if tank.token != token:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    
    tank.last_seen = datetime.utcnow()
    tank.online = True
    
    if 'level' in data:
        tank.level = int(data['level'])
    
    # Optional: Update weight if provided (e.g. for Food Tank scales)
    if 'weight' in data:
        tank.current_weight = float(data['weight'])
        # Recalculate level based on max_weight if needed, 
        # but for now we trust the 'level' sent by ESP or use weight directly.
        # If ESP sends weight but not level, we could calculate:
        # tank.level = int((tank.current_weight / tank.max_weight) * 100)

    db.session.commit()
    
    return jsonify({'status': 'ok', 'level': tank.level})
