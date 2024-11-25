import flask
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Import extensions and utilities
from extensions import db, csrf, limiter  # Importing db, CSRF, and rate limiter
from utils import convert_pdf_to_image, allowed_file, resize_image  # Import utility functions

# Import models
from models import (
    User, Role, Expense, CashAdvance, OpexCapexRetirement,
    PettyCashAdvance, PettyCashRetirement, StationaryRequest, Notification
)  # Ensure all models are defined in models.py

# Import forms
from forms import (
    UserRegistrationForm,
    UserLoginForm,
    CashAdvanceForm,
    OpexCapexRetirementForm,
    PettyCashAdvanceForm,
    PettyCashRetirementForm,
    StationaryRequestForm
)  # Ensure all forms are defined in forms.py

# Import additional modules
from PIL import Image
import os
import logging

# Define the main blueprint
main_blueprint = Blueprint('main', __name__)

# Define the authentication blueprint
auth_blueprint = Blueprint('auth', __name__)

# Sample routes for demonstration
@main_blueprint.route('/')
def home():
    return "Welcome to the Ekondo Expense Management System"

@main_blueprint.route('/test_db')
def test_db():
    users = User.query.all()
    return jsonify([{'username': user.username, 'email': user.email} for user in users])

@auth_blueprint.route('/login')
def login():
    return "User login page"

# Set up the main Blueprint
main_bp = Blueprint('main', __name__)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'png', 'jpg', 'jpeg'}

# User registration route with form validation
@main_bp.route('/register', methods=['GET', 'POST'])
@csrf.exempt  # Apply CSRF protection
@limiter.limit("5 per minute")  # Rate limit for security
def register_user():
    form = UserRegistrationForm()
    if form.validate_on_submit():
        if User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first():
            flash("User already exists", "error")
            return redirect(url_for('main.register_user'))

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            role_id=form.role_id.data,
            password=generate_password_hash(form.password.data)
        )
        db.session.add(new_user)
        db.session.commit()
        flash("User registered successfully!", "success")
        return redirect(url_for('main.login_user'))
    return render_template('register.html', form=form)

# User login route with form validation
@main_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt  # Apply CSRF protection
@limiter.limit("10 per minute")  # Rate limit for security
def login_user():
    form = UserLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('main.dashboard'))
        flash("Invalid username or password", "error")
    return render_template('login.html', form=form)

# Dashboard route
@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# Route to handle cash advance request using form
@main_bp.route('/cash_advance', methods=['GET', 'POST'])
@login_required
@csrf.exempt  # CSRF protection
@limiter.limit("5 per minute")
def raise_cash_advance():
    form = CashAdvanceForm()
    if form.validate_on_submit():
        cash_advance = CashAdvance(
            officer_id=current_user.id,
            amount=form.amount.data,
            purpose=form.purpose.data,
            status="Pending"
        )
        db.session.add(cash_advance)
        db.session.commit()
        flash("Cash advance request submitted successfully!", "success")
        return redirect(url_for('main.dashboard'))
    return render_template('cash_advance.html', form=form)

# Route to upload and process files
@main_bp.route('/upload', methods=['POST'])
@csrf.exempt
@limiter.limit("3 per minute")
def upload_file():
    if 'file' not in request.files:
        flash("No file part", "error")
        return redirect(request.url)

    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)

        # Process file if it's a PDF (convert to image)
        if filename.lower().endswith('.pdf'):
            image_path = convert_pdf_to_image(filepath)
            flash("File uploaded and processed successfully!", "success")
            return send_file(image_path, as_attachment=True)

    flash("Invalid file type", "error")
    return redirect(request.url)

# Error handler examples
@main_bp.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_error(e):
    db.session.rollback()  # Ensure any incomplete transactions are rolled back
    return render_template('500.html'), 500

# Route for OPEX/CAPEX/Retirement requests
@main_bp.route('/opex_capex_retirement', methods=['GET', 'POST'])
@login_required
@csrf.exempt
@limiter.limit("5 per minute")
def raise_opex_capex_retirement():
    form = OpexCapexRetirementForm()
    if form.validate_on_submit():
        opex_capex = OpexCapexRetirement(
            officer_id=current_user.id,
            branch=form.branch.data,
            description=form.description.data,
            invoice_amount=form.invoice_amount.data,
            total_amount=form.total_amount.data,
            status="Pending"
        )
        db.session.add(opex_capex)
        db.session.commit()
        flash("OPEX/CAPEX/Retirement request submitted successfully!", "success")
        return redirect(url_for('main.dashboard'))
    return render_template('opex_capex_retirement.html', form=form)

# Route for petty cash advance requests
@main_bp.route('/petty_cash_advance', methods=['GET', 'POST'])
@login_required
@csrf.exempt
@limiter.limit("5 per minute")
def raise_petty_cash_advance():
    form = PettyCashAdvanceForm()
    if form.validate_on_submit():
        petty_cash_advance = PettyCashAdvance(
            officer_id=current_user.id,
            description=form.description.data,
            items=form.items.data,
            total_amount=form.total_amount.data,
            status="Pending"
        )
        db.session.add(petty_cash_advance)
        db.session.commit()
        flash("Petty cash advance request submitted successfully!", "success")
        return redirect(url_for('main.dashboard'))
    return render_template('petty_cash_advance.html', form=form)

# Route for petty cash retirement requests
@main_bp.route('/petty_cash_retirement', methods=['GET', 'POST'])
@login_required
@csrf.exempt
@limiter.limit("5 per minute")
def raise_petty_cash_retirement():
    form = PettyCashRetirementForm()
    if form.validate_on_submit():
        petty_cash_retirement = PettyCashRetirement(
            officer_id=current_user.id,
            description=form.description.data,
            items=form.items.data,
            total_amount=form.total_amount.data,
            status="Pending"
        )
        db.session.add(petty_cash_retirement)
        db.session.commit()
        flash("Petty cash retirement request submitted successfully!", "success")
        return redirect(url_for('main.dashboard'))
    return render_template('petty_cash_retirement.html', form=form)

# Route for stationery requests
@main_bp.route('/stationery_request', methods=['GET', 'POST'])
@login_required
@csrf.exempt
@limiter.limit("5 per minute")
def raise_stationery_request():
    form = StationaryRequestForm()
    if form.validate_on_submit():
        stationery_request = StationaryRequest(
            officer_id=current_user.id,
            branch=form.branch.data,
            items=form.items.data,
            status="Pending"
        )
        db.session.add(stationery_request)
        db.session.commit()
        flash("Stationery request submitted successfully!", "success")
        return redirect(url_for('main.dashboard'))
    return render_template('stationery_request.html', form=form)

# Route for notifications (example to fetch unread notifications for a user)
@main_bp.route('/notifications/<int:user_id>', methods=['GET'])
@login_required
def get_notifications(user_id):
    notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
    return jsonify([notification.to_dict() for notification in notifications])  # Assume to_dict method exists
