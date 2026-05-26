"""
Application factory for StaySync.
"""
import os
import logging
from flask import Flask
from config import Config
from extensions import db, migrate, login_manager, socketio, mail, limiter, csrf, cors

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload directory exists
    os.makedirs(
        app.config.get(
            'UPLOAD_FOLDER',
            'static/uploads'),
        exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    mail.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    cors.init_app(app)

    # Exempt SocketIO and API from CSRF where needed
    from routes.api import api_bp
    csrf.exempt(api_bp)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.owner import owner_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(api_bp)

    # Register socket events
    from sockets.events import register_socket_events
    register_socket_events()

    # Landing page route
    @app.route('/')
    def landing():
        from flask import render_template
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.role == 'student':
                return render_template('landing.html', user=current_user)
            else:
                return render_template('landing.html', user=current_user)
        return render_template('landing.html')

    # Create tables and seed
    with app.app_context():
        import models  # noqa: ensure all models are imported
        db.create_all()

        from seed import seed_database
        seed_database()

    # Start scheduler
    from apscheduler.schedulers.background import BackgroundScheduler
    from services.scheduler_service import init_scheduler
    scheduler = BackgroundScheduler()
    init_scheduler(scheduler, app)

    logger.info('StaySync application created successfully')
    return app
