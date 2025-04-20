from flask import Blueprint, request, jsonify, current_app, send_file
from PIL import Image
from app.models.storage import ImageStorage
from app.utils.image_processing import remove_background, remove_object,clean_noise


cleanup_bp = Blueprint('cleanup', __name__)


# taking lot of time def need to impliment job queue for this
@cleanup_bp.route('/remove-background', methods=['POST'])
def remove_background_route():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    image_id = data.get('image_id')
    if not image_id:
        return jsonify({'error': 'Image ID is required'}), 400

    storage = ImageStorage(current_app.config['UPLOAD_FOLDER'])
    image_path = storage.get_image_path(image_id)
    if not image_path:
        return jsonify({'error': 'Image not found'}), 404

    try:
        operation = "remove_bg"
        existing_path = storage.get_processed_image_path(image_id, operation)
        if existing_path:
            return send_file(existing_path)

        img = Image.open(image_path)
        processed_img = remove_background(img)
        processed_path = storage.save_processed_image(image_id, operation, processed_img)
        return send_file(processed_path)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cleanup_bp.route('/remove-object', methods=['POST'])
def remove_object_route():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    image_id = data.get('image_id')
    x = data.get('x')
    y = data.get('y')
    width = data.get('width')
    height = data.get('height')

    if not image_id:
        return jsonify({'error': 'Image ID is required'}), 400
    if x is None or y is None or width is None or height is None:
        return jsonify({'error': 'Object coordinates are required'}), 400

    storage = ImageStorage(current_app.config['UPLOAD_FOLDER'])
    image_path = storage.get_image_path(image_id)
    if not image_path:
        return jsonify({'error': 'Image not found'}), 404

    try:
        operation = f"remove_obj_{x}_{y}_{width}_{height}"
        existing_path = storage.get_processed_image_path(image_id, operation)
        if existing_path:
            return send_file(existing_path)

        img = Image.open(image_path)
        processed_img = remove_object(img, x, y, width, height)
        processed_path = storage.save_processed_image(image_id, operation, processed_img)
        return send_file(processed_path)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cleanup_bp.route("/remove-noise", methods=["POST"])
def noise():
    data=request.json

    if not data:
        return jsonify({"error":"No data provided"}),400
    
    image_id=data.get("image_id")
    if not image_id:
        return jsonify({"error":"Image ID is required"}),400
    
    storage=ImageStorage(current_app.config["UPLOAD_FOLDER"])
    image_path=storage.get_image_path(image_id)
    if not image_path:
        return jsonify({"error":"Image not found"}),404
    try:
        operation="remove_noise"
        existing_path=storage.get_processed_image_path(image_id,operation)
        if existing_path:
            return send_file(existing_path)
        
        img=Image.open(image_path)
        processed_img=clean_noise(img)
        processed_path=storage.save_processed_image(image_id,operation,processed_img)
        return send_file(processed_path)
    except Exception as e:
        return jsonify({"error":e}),500
    
