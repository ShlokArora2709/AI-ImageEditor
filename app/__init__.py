from flask import Flask
import os
from .routes.resize import resize_bp
from .routes.upload import upload_bp
from .routes.cleanup import cleanup_bp
from .routes.editing import editing_bp
from .Mycelery import configure_celery

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    configure_celery(app)
    app.register_blueprint(upload_bp)
    app.register_blueprint(resize_bp)
    app.register_blueprint(cleanup_bp)
    app.register_blueprint(editing_bp)
    return app