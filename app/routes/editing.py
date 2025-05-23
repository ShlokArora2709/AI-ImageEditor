from flask import Blueprint, request, jsonify, current_app, send_file
from PIL import Image
from app.models.storage import ImageStorage
from app.utils.image_processing import replace_bg,edit_prompt
from app.Mycelery import celery
from celery.result import AsyncResult

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

@celery.task(name='run_prompt_edit')
def run_prompt_edit(image_id, prompt, upload_folder):
    try:
        storage = ImageStorage(upload_folder)
        image_path = storage.get_image_path(image_id)
        if not image_path:
            return {"error": "Image not found"}
        
        operation = f"edit_{prompt}"
        existing_path = storage.get_processed_image_path(image_id, operation)
        if existing_path:
            return {"result_path": existing_path}
        
        image = Image.open(image_path)
        result = edit_prompt(image, prompt)
        processed_path = storage.save_processed_image(image_id, operation, result)
        return {"result_path": processed_path}

    except Exception as e:
        return {"error": str(e)}

@editing_bp.route('/prompt-edit', methods=['POST'])
def edit_image_prompt():
    data = request.json

    if "image_id" not in data or "prompt" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    image_id = data["image_id"]
    prompt = data["prompt"]

    task = run_prompt_edit.apply_async(args=[image_id, prompt, current_app.config['UPLOAD_FOLDER']])
    return jsonify({"task_id": task.id}), 202

@editing_bp.route('/task-status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = AsyncResult(task_id)

    if task.state == 'PENDING':
        return jsonify({"status": "pending"}), 202
    elif task.state == 'SUCCESS':
        result = task.result
        if 'error' in result:
            return jsonify({"status": "failed", "error": result['error']}), 500
        return send_file(result['result_path'], mimetype='image/png')
    elif task.state == 'FAILURE':
        return jsonify({"status": "failed", "error": str(task.info)}), 500
    else:
        return jsonify({"status": task.state}), 202