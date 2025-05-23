from flask import Blueprint, request, jsonify, current_app, send_file
from PIL import Image
import os
from app.models.storage import ImageStorage
from app.utils.image_processing import resize_image, change_aspect_ratio

resize_bp = Blueprint('resize', __name__)

@resize_bp.route('/resize', methods=['POST'])
def resize_image_route():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    image_id = data.get('image_id')
    width = data.get('width')
    height = data.get('height')
    
    if not image_id:
        return jsonify({'error': 'Image ID is required'}), 400
    if not width or not height:
        return jsonify({'error': 'Width and height are required'}), 400
    
    try:
        width = int(width)
        height = int(height)
    except ValueError:
        return jsonify({'error': 'Width and height must be integers'}), 400
        

    storage = ImageStorage(current_app.config['UPLOAD_FOLDER'])
    image_path = storage.get_image_path(image_id)
    
    if not image_path:
        return jsonify({'error': 'Image not found'}), 404
        
    try:
        operation = f"resize_{width}x{height}"
        
        
        existing_path = storage.get_processed_image_path(image_id, operation)
        if existing_path:
            return send_file(existing_path)
        img = Image.open(image_path)
        resized_img = resize_image(img, width, height)
        processed_path = storage.save_processed_image(image_id, operation, resized_img)

        return send_file(processed_path)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@resize_bp.route('/aspect-ratio', methods=['POST'])
def change_aspect_ratio_route():
    # Validate request data
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    image_id = data.get('image_id')
    ratio = data.get('ratio') 

    if not image_id:
        return jsonify({'error': 'Image ID is required'}), 400
    if not ratio:
        return jsonify({'error': 'Aspect ratio is required'}), 400
    try:
        width_ratio, height_ratio = map(int, ratio.split(':'))
    except ValueError:
        return jsonify({'error': 'Invalid aspect ratio format. Use "width:height" (e.g., "16:9")'}), 400
    storage = ImageStorage(current_app.config['UPLOAD_FOLDER'])
    image_path = storage.get_image_path(image_id)
    
    if not image_path:
        return jsonify({'error': 'Image not found'}), 404
        
    try:
        operation = f"aspect_{ratio.replace(':', 'x')}"
        
        existing_path = storage.get_processed_image_path(image_id, operation)
        if existing_path:
            return send_file(existing_path)
        img = Image.open(image_path)
        processed_img = change_aspect_ratio(img, width_ratio, height_ratio)  # type: ignore
        processed_path = storage.save_processed_image(image_id, operation, processed_img)

        return send_file(processed_path)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
