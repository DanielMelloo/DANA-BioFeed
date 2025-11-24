from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import db
from app.models.feeder import Feeder
from app.models.log import Log
from app.models.tank import Tank
from app.services.command_bus import CommandBus
from datetime import datetime
from flask_login import login_required, current_user
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    feeders = Feeder.query.all()
    
    # Check online status (simple timeout check)
    now = datetime.utcnow()
    for f in feeders:
        if f.last_seen:
            delta = now - f.last_seen
            f.online = delta.total_seconds() < 120 # 2 minutes timeout
        else:
            f.online = False
            
    return render_template('dashboard.html', feeders=feeders)

@dashboard_bp.route('/tanks')
@login_required
def tanks():
    tanks = Tank.query.all()
    return render_template('tanks.html', tanks=tanks)

@dashboard_bp.route('/tanks/create', methods=['POST'])
@login_required
def create_tank():
    name = request.form.get('name')
    type = request.form.get('type')
    capacity = request.form.get('capacity')
    
    tank = Tank(name=name, type=type, capacity=capacity)
    db.session.add(tank)
    db.session.commit()
    flash('Tanque criado com sucesso!', 'success')
    return redirect(url_for('dashboard.tanks'))

@dashboard_bp.route('/tanks/<int:id>/update', methods=['POST'])
@login_required
def update_tank(id):
    tank = Tank.query.get_or_404(id)
    
    # Update Definitions if provided
    if request.form.get('name'):
        tank.name = request.form.get('name')
    if request.form.get('type'):
        tank.type = request.form.get('type')
    if request.form.get('capacity'):
        tank.capacity = request.form.get('capacity')
        
    # Update Level if provided
    if request.form.get('level'):
        tank.level = int(request.form.get('level'))
        tank.last_refill = datetime.utcnow()
        
    db.session.commit()
    flash('Tanque atualizado com sucesso!', 'success')
    return redirect(url_for('dashboard.tanks'))

@dashboard_bp.route('/feeder/<int:id>')
@login_required
def feeder_detail(id):
    feeder = Feeder.query.get_or_404(id)
    logs = Log.query.filter_by(feeder_id=id).order_by(Log.timestamp.desc()).limit(50).all()
    tanks = Tank.query.all()
    return render_template('feeder.html', feeder=feeder, logs=logs, tanks=tanks)

@dashboard_bp.route('/feeder/<int:id>/update', methods=['POST'])
@login_required
def update_feeder(id):
    feeder = Feeder.query.get_or_404(id)
    feeder.name = request.form.get('name')
    # Calculate total seconds from D/H/M/S inputs
    days = int(request.form.get('interval_days', 0) or 0)
    hours = int(request.form.get('interval_hours', 0) or 0)
    minutes = int(request.form.get('interval_minutes', 0) or 0)
    seconds = int(request.form.get('interval_seconds', 0) or 0)
    
    total_seconds = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds
    if total_seconds > 0:
        feeder.interval_seconds = total_seconds

    feeder.open_duration_ms = int(request.form.get('open_duration_ms', 1000) or 1000)
    feeder.target_weight = float(request.form.get('target_weight', 210.0))
    feeder.warning_weight = float(request.form.get('warning_weight', 80.0))
    feeder.critical_weight = float(request.form.get('critical_weight', 20.0))
    feeder.dose_count = int(request.form.get('dose_count', 1))
    
    feeder.food_tank_id = request.form.get('food_tank_id') or None
    feeder.water_tank_id = request.form.get('water_tank_id') or None
    
    feeder.avatar = request.form.get('avatar')
    feeder.mode = request.form.get('mode')
    
    # New Logic Fields
    feeder.block_name = request.form.get('block_name')
    feeder.water_mode = request.form.get('water_mode')
    
    feeder.is_locked = 'is_locked' in request.form
    feeder.water_locked = 'water_locked' in request.form
    feeder.maintenance_mode = 'maintenance_mode' in request.form
    
    # Manual Water Control
    if 'manual_water' in request.form:
        action = request.form.get('manual_water') # OPEN or CLOSE
        
        # If Manual Open, force mode to MANUAL? User said "Fechada pelo usuário = modo manual".
        # Let's respect the explicit mode toggle, but if they click Open/Close, we execute it.
        # If they click CLOSE, maybe switch to MANUAL?
        # "Quando o usuário abre novamente, o sistema volta a operar em automático." -> Wait, this logic is tricky.
        # "Aberta = modo automático (default). Fechada pelo usuário = modo manual."
        # Let's stick to the explicit Radio Button for Mode, and these buttons for immediate action.
        
        CommandBus.add_command(id, {
            'type': 'water_control',
            'action': action,
            'duration': 0 # Permanent until changed? Or timeout?
        })
        
        feeder.water_valve_state = action
        flash(f'Comando de Água enviado: {action}', 'info')

    if 'reset_trip' in request.form:
        feeder.status = 'NORMAL'
        feeder.sensor_state = 'LSH'
        feeder.trip_reason = None
        flash('Falha (TRIP) resetada com sucesso.', 'success')
    
    # Handle schedule times
    times = request.form.getlist('schedule_times')
    feeder.schedule_times = json.dumps(times)
    
    db.session.commit()
    flash('Configurações atualizadas!', 'success')
    return redirect(url_for('dashboard.feeder_detail', id=id))

@dashboard_bp.route('/feeder/<int:id>/feed', methods=['POST'])
@login_required
def feed_now(id):
    feeder = Feeder.query.get_or_404(id)
    
    if feeder.is_locked:
        flash('ERRO: O alimentador está travado (Safety Lock).', 'danger')
        return redirect(url_for('dashboard.feeder_detail', id=id))

    # 1. Command: Dispense Food (Open Bottom Gate)
    CommandBus.add_command(id, {'type': 'feed', 'duration': feeder.open_duration_ms})
    
    # 2. Command: Refill Drawer (Open Top Gate from Main Tank)
    CommandBus.add_command(id, {
        'type': 'refill', 
        'units': 1, # Refill 1 unit (target_weight)
        'duration': feeder.open_duration_ms # Or specific refill duration
    })
    
    flash('Ciclo de Alimentação Iniciado (Liberar + Reabastecer)!', 'info')
    return redirect(url_for('dashboard.feeder_detail', id=id))

@dashboard_bp.route('/logs')
@login_required
def logs():
    page = request.args.get('page', 1, type=int)
    logs = Log.query.order_by(Log.timestamp.desc()).paginate(page=page, per_page=20)
    return render_template('logs.html', logs=logs)

@dashboard_bp.route('/register', methods=['GET'])
@login_required
def register_page():
    tanks = Tank.query.all()
    return render_template('register.html', new_feeder=None, tanks=tanks)

@dashboard_bp.route('/register', methods=['POST'])
@login_required
def register_feeder_action():
    name = request.form.get('name')
    food_tank_id = request.form.get('food_tank_id') or None
    water_tank_id = request.form.get('water_tank_id') or None
    avatar = request.form.get('avatar')
    
    if not name:
        flash('Nome é obrigatório', 'danger')
        return redirect(url_for('dashboard.register_page'))
    
    feeder = Feeder(name=name, food_tank_id=food_tank_id, water_tank_id=water_tank_id, avatar=avatar)
    db.session.add(feeder)
    db.session.commit()
    
    tanks = Tank.query.all()
    return render_template('register.html', new_feeder=feeder, tanks=tanks)

@dashboard_bp.route('/settings')
@login_required
def settings():
    return render_template('register_admin.html')

@dashboard_bp.route('/firmware')
@login_required
def firmware():
    feeders = Feeder.query.all()
    return render_template('firmware.html', feeders=feeders)
