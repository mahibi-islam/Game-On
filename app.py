from flask import Flask
import os
from db import mongo

def create_app(config_name='development'):
    """Application factory pattern"""
    # Get the root directory
    basedir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(basedir, 'templates')
    static_dir = os.path.join(basedir, 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Load configuration
    if config_name == 'production':
        from config import ProductionConfig
        app.config.from_object(ProductionConfig)
    else:
        from config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions
    mongo.init_app(app)
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/gallery', exist_ok=True)
    
    # Register blueprints (routes)
    from routes.user_routes import user_bp
    from routes.admin_routes import admin_bp
    from routes.api_routes import api_bp
    from routes.auth_routes import auth_bp
    
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)
    
    # Global context processor
    @app.context_processor 
    def inject_settings():
        from models.settings import Settings
        from models.location import Location
        settings = Settings.find_one()
        active_locations = Location.find_all({'enabled': True})
        return dict(settings=settings, active_locations=active_locations)
    
    # Initialize database
    from models.booking import Booking
    from models.slot import Slot
    from models.admin import Admin
    from models.settings import Settings
    from models.location import Location
    
    with app.app_context():
        Booking.init_excel()
        Location.init_defaults()
        Booking.init_defaults()
        Slot.init_defaults()
        Admin.init_defaults()
        Settings.init_defaults()
    
    return app
