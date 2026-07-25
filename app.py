from flask import Flask, Response, send_from_directory
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
        app.config.from_object(ProductionConfig())
    else:
        from config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig())
    
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

    # ── Google Search & Browser Favicon Route ──
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    
    # ── Security: security.txt (RFC 9116) ──
    @app.route('/.well-known/security.txt')
    def security_txt():
        content = (
            "Contact: mailto:code.mahibi@gmail.com\n"
            "Preferred-Languages: en, bn\n"
            "Canonical: https://gameon.bd/.well-known/security.txt\n"
            "Expires: 2027-06-27T00:00:00.000Z\n"
        )
        return Response(content, mimetype='text/plain')

    # ── Security: robots.txt (block AI crawlers) ──
    @app.route('/robots.txt')
    def robots_txt():
        content = (
            "User-agent: *\n"
            "Allow: /\n"
            "\n"
            "# Block AI crawlers and scrapers\n"
            "User-agent: GPTBot\n"
            "Disallow: /\n"
            "\n"
            "User-agent: ChatGPT-User\n"
            "Disallow: /\n"
            "\n"
            "User-agent: CCBot\n"
            "Disallow: /\n"
            "\n"
            "User-agent: Google-Extended\n"
            "Disallow: /\n"
            "\n"
            "User-agent: anthropic-ai\n"
            "Disallow: /\n"
            "\n"
            "User-agent: ClaudeBot\n"
            "Disallow: /\n"
            "\n"
            "User-agent: Bytespider\n"
            "Disallow: /\n"
            "\n"
            "User-agent: Meta-ExternalAgent\n"
            "Disallow: /\n"
            "\n"
            "User-agent: PerplexityBot\n"
            "Disallow: /\n"
            "\n"
            "User-agent: Applebot-Extended\n"
            "Disallow: /\n"
        )
        return Response(content, mimetype='text/plain')

    # ── Security: Response Headers ──
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        return response

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

