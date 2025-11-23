from flask import Flask
from config import Config
from database import db
from app.routes.api_feed import api_bp
from app.routes.dashboard import dashboard_bp

def create_app():
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
    app.config.from_object(Config)

    db.init_app(app)

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

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
