from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from app.models.storage import ImageStorage

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return jsonify({'error': 'Invalid file type'}), 400
    filename = secure_filename(file.filename)
    storage = ImageStorage(current_app.config['UPLOAD_FOLDER'])
    image_id = storage.save_image(file, filename)
    
    return jsonify({
        'success': True,
        'image_id': image_id,
        'message': 'Image uploaded successfully'
    }), 201