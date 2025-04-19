# app/models/storage.py
import os
import uuid
import json
from datetime import datetime

class ImageStorage:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.metadata_file = os.path.join(upload_folder, 'metadata.json')
        self._load_metadata()
        
    def _load_metadata(self):
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
            self._save_metadata()
            
    def _save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
            
    def save_image(self, image_file, original_filename):
        image_id = str(uuid.uuid4())
        _, ext = os.path.splitext(original_filename)
        
        filename = f"{image_id}{ext}"
        filepath = os.path.join(self.upload_folder, filename)
        
        image_file.save(filepath)
        
        self.metadata[image_id] = {
            'original_filename': original_filename,
            'filename': filename,
            'uploaded_at': datetime.now().isoformat(),
            'processed_versions': {}
        }
        
        self._save_metadata()
        return image_id
        
    def get_image_path(self, image_id):
        if image_id not in self.metadata:
            return None
            
        filename = self.metadata[image_id]['filename']
        return os.path.join(self.upload_folder, filename)
        
    def save_processed_image(self, image_id, operation, image_data):
        if image_id not in self.metadata:
            return None
            
        base_filename = self.metadata[image_id]['filename']
        name, ext = os.path.splitext(base_filename)
        processed_filename = f"{name}_{operation}{ext}"
        processed_path = os.path.join(self.upload_folder, processed_filename)
        
        with open(processed_path, 'wb') as f:
            f.write(image_data.read())
            image_data.seek(0)
            
        self.metadata[image_id]['processed_versions'][operation] = {
            'filename': processed_filename,
            'processed_at': datetime.now().isoformat()
        }
        
        self._save_metadata()
        return processed_path
        
    def get_processed_image_path(self, image_id, operation):
        if (image_id not in self.metadata or 
            'processed_versions' not in self.metadata[image_id] or
            operation not in self.metadata[image_id]['processed_versions']):
            return None
            
        filename = self.metadata[image_id]['processed_versions'][operation]['filename']
        return os.path.join(self.upload_folder, filename)