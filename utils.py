from models import User, Role
from sqlalchemy.exc import SQLAlchemyError
import logging
from flask_caching import Cache
from PIL import Image
import pdf2image
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize caching (assuming cache configuration is done elsewhere)
cache = Cache()

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_pdf_to_image(pdf_path, output_folder='converted_images'):
    """Convert a PDF to an image and save it."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    try:
        images = pdf2image.convert_from_path(pdf_path)
        image_path = os.path.join(output_folder, os.path.basename(pdf_path).replace(".pdf", ".jpg"))
        images[0].save(image_path, 'JPEG')
        return image_path
    except Exception as e:
        logging.error(f"Error converting PDF to image: {e}")
        raise

def resize_image(image_path, max_size=(800, 800)):
    """Resize an image to a maximum size while maintaining aspect ratio."""
    try:
        img = Image.open(image_path)
        img.thumbnail(max_size)
        img.save(image_path)
    except Exception as e:
        logging.error(f"Error resizing image: {e}")
        raise

@cache.cached(timeout=60, key_prefix='supervisor_by_department')
def get_supervisor(department_id):
    """Fetch the supervisor for a given department.

    Args:
        department_id (int): The ID of the department.

    Returns:
        User: The supervisor User object or None if not found.
    """
    try:
        # Fetching supervisor role ID dynamically
        SUPERVISOR_ROLE_ID = get_role_id_by_name('Supervisor')  # Assuming this function exists
        supervisor = User.query.filter_by(department_id=department_id, role_id=SUPERVISOR_ROLE_ID).first()
        if supervisor:
            logging.info(f"Supervisor found for department {department_id}: {supervisor.username}")
        else:
            logging.warning(f"No supervisor found for department {department_id}.")
        return supervisor
    except SQLAlchemyError as e:
        logging.error(f"Error fetching supervisor for department {department_id}: {e}")
        return None

def send_notification(user_id, message, notification_type='email'):
    """Send a notification to the user.

    Args:
        user_id (int): The ID of the user to notify.
        message (str): The message content.
        notification_type (str): The type of notification ('email', 'sms', 'in-app').
    """
    user = User.query.get(user_id)
    if user is None:
        logging.error(f"User with ID {user_id} not found. Notification not sent.")
        return

    try:
        if notification_type == 'email':
            # Logic to send email notification
            subject = "Important Notification"
            # Implement email sending logic using Flask-Mail or similar
            logging.info(f"Email sent to {user.email}: {message}")
        elif notification_type == 'sms':
            # Logic to send SMS notification
            logging.info(f"SMS sent to {user.phone_number}: {message}")  # Assuming phone_number exists in User
        elif notification_type == 'in-app':
            # Logic for in-app notifications
            logging.info(f"In-app notification sent to {user.username}: {message}")
        else:
            logging.warning(f"Unknown notification type: {notification_type}. No action taken.")
    except Exception as e:
        logging.error(f"Failed to send notification to user {user_id}: {e}")

def get_role_id_by_name(role_name):
    """Fetch role ID by role name.

    Args:
        role_name (str): The name of the role.

    Returns:
        int: The ID of the role or None if not found.
    """
    role = Role.query.filter_by(name=role_name).first()
    return role.id if role else None

def convert_pdf_to_image_v2(pdf_path):
    """Convert PDF to images and return paths of the images."""
    images = pdf2image.convert_from_path(pdf_path)
    image_paths = []
    for i, image in enumerate(images):
        image_path = f'uploads/page_{i + 1}.png'  # Save each page as a PNG
        image.save(image_path, 'PNG')
        image_paths.append(image_path)
    return image_paths
