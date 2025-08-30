from flask import Blueprint, request, jsonify, current_app, send_file
from PIL import Image
from app.models.storage import ImageStorage
from app.utils.image_processing import replace_bg,edit_prompt


editing_bp = Blueprint('editing', __name__)

@editing_bp.route('/replace-bg', methods=['POST'])
def replace_background():
    if "bg" not in request.files:
        return jsonify({"error": "No background image provided"}), 400
    
    if "image_id" not in request.form:
        return jsonify({"error": "No image provided"}), 400
    
    image_id = request.form["image_id"]
    bg_image = request.files["bg"]
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    if not ('.' in bg_image.filename and bg_image.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return jsonify({'error': 'Invalid file type'}), 400
    
    
    storage = ImageStorage(current_app.config['UPLOAD_FOLDER'])
    image_path =storage.get_image_path(image_id)
    if not image_path:
        return jsonify({"error": "Image not found"}), 404
    try:
        operation = f"replace_{bg_image.filename}"
        existing_path= storage.get_processed_image_path(image_id,operation )
        if existing_path:
            return send_file(existing_path, mimetype='image/png')
        else:
            image = Image.open(image_path)
            bg_image = Image.open(bg_image)
            result = replace_bg(image, bg_image)
            processed_path = storage.save_processed_image(image_id, operation, result)
            return send_file(processed_path, mimetype='image/png')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@editing_bp.route('/prompt-edit', methods=['POST'])
def edit_image_prompt():
    data:dict = request.json # type: ignore

    if "image_id" not in data or "prompt" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    image_id = data["image_id"]
    prompt = data["prompt"]

    try:
        storage = ImageStorage(current_app.config['UPLOAD_FOLDER'])
        image_path = storage.get_image_path(image_id)
        if not image_path:
            return jsonify({"error": "Image not found"}), 404
        
        operation = f"edit_{prompt}"
        existing_path = storage.get_processed_image_path(image_id, operation)
        if existing_path:
            return send_file(existing_path, mimetype='image/png')
        
        image = Image.open(image_path)
        result = edit_prompt(image, prompt)
        processed_path = storage.save_processed_image(image_id, operation, result)
        return send_file(processed_path, mimetype='image/png') # type: ignore

    except Exception as e:
        return jsonify({"error": str(e)}), 500

