from flask import Flask
from config import Config
from database import db
from app.routes.api_feed import api_bp
from app.routes.dashboard import dashboard_bp

def create_app():
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
    app.config.from_object(Config)

    db.init_app(app)

    # Login Manager Setup
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Faça login para acessar esta página."
    login_manager.login_message_category = "info"

    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp)

    with app.app_context():
        db.create_all()
        
        # Initialize default tanks if none exist
        from app.models.tank import Tank
        if not Tank.query.first():
            db.session.add(Tank(name="Tanque de Ração Principal", type="food", capacity="5kg"))
            db.session.add(Tank(name="Bebedouro Principal", type="water", capacity="3L"))
            db.session.commit()
            print("Default tanks created.")

        # Initialize Default Admin
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123') # Default password
            db.session.add(admin)
            db.session.commit()
            print("Default admin created (admin/admin123).")

        # Initialize Daniel User
        if not User.query.filter_by(username='Daniel').first():
            daniel = User(username='Daniel', is_admin=True)
            daniel.set_password('codeez4ever')
            db.session.add(daniel)
            db.session.commit()
            print("User Daniel created.")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
