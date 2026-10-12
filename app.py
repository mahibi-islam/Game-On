from flask import Flask, Response, send_from_directory, request, jsonify, flash, redirect
from flask_wtf.csrf import CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from urllib.parse import urlparse
from db import mongo, limiter, csrf

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
    
    # Trust X-Forwarded-For/-Proto from the hosting platform's proxy so the real
    # client IP is used for rate limiting. X-Forwarded-Host is deliberately not trusted.
    if app.config.get('PROXY_COUNT'):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config['PROXY_COUNT'],
                                x_proto=app.config['PROXY_COUNT'])

    # Initialize extensions
    mongo.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    def reject(message, status):
        """JSON error for API/fetch calls, otherwise flash and send the user back."""
        # csrf.js adds X-CSRFToken to every fetch() POST, so it marks script callers
        if request.path.startswith('/api/') or request.is_json or 'X-CSRFToken' in request.headers:
            return jsonify({'error': message}), status
        flash(message, 'error')
        referrer = urlparse(request.referrer or '')
        if referrer.netloc == request.host:
            return redirect(referrer.path + (f'?{referrer.query}' if referrer.query else ''))
        return redirect('/')

    @app.errorhandler(429)
    def too_many_requests(e):
        return reject('Too many attempts. Please wait a few minutes and try again.', 429)

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        return reject('Your session expired or the form was out of date. Please try again.', 400)
    
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

