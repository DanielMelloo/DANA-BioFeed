from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from database import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        
        flash('Usuário ou senha inválidos.', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register_admin', methods=['GET', 'POST'])
@login_required
def register_admin():
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem criar novos usuários.', 'error')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'error')
        else:
            new_user = User(username=username, is_admin=True)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash(f'Administrador {username} criado com sucesso!', 'success')
            return redirect(url_for('dashboard.index'))
            
    return render_template('register_admin.html')
