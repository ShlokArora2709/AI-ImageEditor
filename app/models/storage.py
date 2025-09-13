# app/models/storage.py
import os
import uuid
import json
from datetime import datetime
import cloudinary
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
load_dotenv()

cloudinary.config(
    url=os.getenv('CLOUDINARY_URL')
)
client = MongoClient(os.getenv('MONGODBURI'), server_api=ServerApi('1'))

class ImageStorage:
    def __init__(self):
        self.db = client['image_editor']
        self.collection = self.db['image_metadata']
        
    def save_image(self, image_file, original_filename):
        image_id = str(uuid.uuid4())
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            image_file,
            public_id=image_id,
            folder="originals"
        )
        
        # Save metadata to MongoDB
        metadata = {
            '_id': image_id,
            'original_filename': original_filename,
            'cloudinary_public_id': upload_result['public_id'],
            'cloudinary_url': upload_result['secure_url'],
            'uploaded_at': datetime.now(),
            'processed_versions': {}
        }
        
        self.collection.insert_one(metadata)
        return image_id
        
    def get_image_url(self, image_id):
        metadata = self.collection.find_one({'_id': image_id})
        if not metadata:
            return None
        return metadata['cloudinary_url']
        
    def save_processed_image(self, image_id, operation, image_data):
        metadata = self.collection.find_one({'_id': image_id})
        if not metadata:
            return None
            
        processed_public_id = f"{image_id}_{operation}"
        
        # Upload processed image to Cloudinary
        upload_result = cloudinary.uploader.upload(
            image_data,
            public_id=processed_public_id,
            folder="processed"
        )
        
        # Update metadata in MongoDB
        self.collection.update_one(
            {'_id': image_id},
            {
                '$set': {
                    f'processed_versions.{operation}': {
                        'cloudinary_public_id': upload_result['public_id'],
                        'cloudinary_url': upload_result['secure_url'],
                        'processed_at': datetime.now()
                    }
                }
            }
        )
        
        return upload_result['secure_url']
        
    def get_processed_image_url(self, image_id, operation):
        metadata = self.collection.find_one({'_id': image_id})
        if (not metadata or 
            'processed_versions' not in metadata or
            operation not in metadata['processed_versions']):
            return None
            
        return metadata['processed_versions'][operation]['cloudinary_url']
