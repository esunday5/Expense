import os
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_dotenv import DotEnv
from flasgger import Swagger
from dotenv import load_dotenv
from config import Config
from extensions import db, csrf, limiter  # Import CSRF and Limiter extensions
from routes import main_blueprint as main_bp, auth_blueprint as auth_bp

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()  # Migrate object initialized here, it will be used later
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
swagger = Swagger()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Load configuration

    # Load environment variables from .env file
    DotEnv(app)

    # Enable CORS
    CORS(app)

    # Security Headers
    Talisman(app)  # Protect against common vulnerabilities

    # Initialize Flask-Limiter (with Redis storage)
    limiter.init_app(app)  # No Redis storage used

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)  # Set up Flask-Migrate for database migrations
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # Adjust this as needed
    csrf.init_app(app)  # CSRF protection
    swagger.init_app(app)  # Set up Swagger for API documentation

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # Register error handlers
    register_error_handlers(app)

    # Health check route
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health Check Endpoint
        ---
        responses:
          200:
            description: Service is healthy
        """
        return {"status": "healthy"}, 200

    # API data route for Next.js frontend
    @app.route('/api/data', methods=['GET'])
    def get_data():
        """API route to send data to the Next.js frontend"""
        return jsonify({"message": "Hello from Flask!"})

    # Example route with rate limiting (inside create_app)
    @app.route("/")
    @limiter.limit("5 per minute")  # Example: Rate limit of 5 requests per minute
    def index():
        return "Hello, Flask-Limiter is configured with Redis!"

    # Create the database tables if they don't exist
    with app.app_context():
        try:
            # Importing models to create tables in the database
            from models import User, Role, Department, Expense, CashAdvance, OpexCapexRetirement, \
                PettyCashAdvance, PettyCashRetirement, StationaryRequest, AuditLog, DocumentUploads, \
                Notification, Transaction, RequestHistory, NotificationSettings, FileMetadata, \
                ExpenseApprovalWorkflow

            # Create all tables
            db.create_all()

        except Exception as e:
            app.logger.error(f"Error creating database tables: {e}")

    return app

def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        logging.warning(f"Page not found: {request.path}")
        return {"error": "Page not found"}, 404

    @app.errorhandler(500)
    def internal_error(e):
        logging.error(f"Internal error: {e}")
        return {"error": "Internal server error"}, 500

# Initialize Flask-Migrate
def init_migrate():
    """ Initialize migration repository and run the migrations """
    from flask_migrate import Migrate
    migrate = Migrate()
    migrate.init_app(app, db)

    # Commands to initialize and apply migration
    # These need to be run in the terminal as Flask CLI commands:
    # flask db init     - Initializes migration repository
    # flask db migrate  - Creates migration script
    # flask db upgrade  - Applies the migration
    try:
        # Initialize migration repository (Run flask db init in terminal)
        print("Run the following commands in the terminal:")
        print("flask db init")
        print("flask db migrate -m 'Initial migration.'")
        print("flask db upgrade")
    except Exception as e:
        app.logger.error(f"Error setting up Flask-Migrate: {e}")

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    app = create_app()  # Create app instance
    app.run(host='0.0.0.0', port=5000, debug=True)  # Set debug=False in production
