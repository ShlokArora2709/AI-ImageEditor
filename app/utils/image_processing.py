from PIL import Image
import io
import cv2
import numpy as np
import requests
import os
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet

WEIGHTS_DIR = "weights"
WEIGHTS_FILE = "RealESRGAN_x4plus.pth"
WEIGHTS_PATH = os.path.join(WEIGHTS_DIR, WEIGHTS_FILE)
WEIGHTS_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"

if not os.path.exists(WEIGHTS_DIR):
    os.makedirs(WEIGHTS_DIR) 

if not os.path.exists(WEIGHTS_PATH):  # Check if the weights file exists
    print(f"Downloading {WEIGHTS_FILE}...")
    response = requests.get(WEIGHTS_URL, stream=True)
    if response.status_code == 200:
        with open(WEIGHTS_PATH, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"{WEIGHTS_FILE} downloaded successfully.")
    else:
        raise Exception(f"Failed to download {WEIGHTS_FILE}. Status code: {response.status_code}")
else:
    print(f"{WEIGHTS_FILE} already exists.")

model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32)
upsampler = RealESRGANer(
    scale=4, 
    model_path='weights/RealESRGAN_x4plus.pth',  
    model=model,
    tile=0
)

def resize_image(img:Image, width:int, height:int)->io.BytesIO:
    resized_img = img.resize((width, height), Image.LANCZOS)
    
    # Create an in-memory image to return
    img_io = io.BytesIO()
    img_format = img.format if img.format else 'JPEG'
    resized_img.save(img_io, format=img_format)
    img_io.seek(0)
    
    return img_io

def remove_background(img: Image) -> io.BytesIO:
    # Convert PIL to OpenCV image
    img_np = np.array(img.convert("RGB"))
    mask = np.zeros(img_np.shape[:2], np.uint8)

    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    height, width = img_np.shape[:2]
    rect = (10, 10, width - 20, height - 20)  

    # Apply GrabCut
    cv2.grabCut(img_np, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)

    # Create mask where 0/2 are background, 1/3 are foreground
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    img_clean = img_np * mask2[:, :, np.newaxis]

    # Convert to RGBA with transparency
    result = np.zeros((height, width, 4), dtype=np.uint8)
    result[:, :, :3] = img_clean
    result[:, :, 3] = mask2 * 255

    result_pil = Image.fromarray(result)
    result_io = io.BytesIO()
    result_pil.save(result_io, format='PNG')
    result_io.seek(0)
    return result_io

def change_aspect_ratio(img, width_ratio, height_ratio):
    orig_width, orig_height = img.size
    target_ratio = width_ratio / height_ratio
    curr_ratio = orig_width / orig_height
    if curr_ratio > target_ratio:
        new_width = int(orig_height * target_ratio)
        new_height = orig_height
        left = (orig_width - new_width) // 2
        right = left + new_width
        top = 0
        bottom = orig_height
    else:
        new_width = orig_width
        new_height = int(orig_width / target_ratio)
        left = 0
        right = orig_width
        top = (orig_height - new_height) // 2
        bottom = top + new_height
    cropped_img = img.crop((left, top, right, bottom))
    img_io = io.BytesIO()
    img_format = img.format if img.format else 'JPEG'
    cropped_img.save(img_io, format=img_format)
    img_io.seek(0)
    return img_io

def remove_object(img, x, y, width, height):
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    mask = np.zeros(img_cv.shape[:2], dtype=np.uint8)
    mask[y:y+height, x:x+width] = 255
    result = cv2.inpaint(img_cv, mask, 3, cv2.INPAINT_TELEA)
    result_pil = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    img_io = io.BytesIO()
    img_format = img.format if img.format else 'JPEG'
    result_pil.save(img_io, format=img_format)
    img_io.seek(0)
    return img_io

def clean_noise(img: Image.Image):
    # Step 1: Validate the input image
    if img is None:
        raise ValueError("Image not found or corrupted.")
    
    # Step 2: Convert PIL Image to NumPy array (OpenCV format)
    img_np = np.array(img)
    if img_np.shape[2] == 4:  # Remove alpha channel if present
        img_np = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
    
    # Step 3: Upscale the image using RealESRGAN
    pred_image, _ = upsampler.enhance(img_np)
    print("Image cleaned")
    
    # Step 4: Convert the enhanced NumPy array back to PIL Image
    pred_image_pil = Image.fromarray(cv2.cvtColor(pred_image, cv2.COLOR_BGR2RGB))
    img_io = io.BytesIO()
    img_format = img.format if img.format else 'JPEG'
    pred_image_pil.save(img_io, format=img_format)
    img_io.seek(0)
    return img_io
