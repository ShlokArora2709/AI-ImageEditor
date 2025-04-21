from PIL import Image
import io
import cv2
import numpy as np
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
from .downloadModels import download_models
from segment_anything import sam_model_registry, SamPredictor
import torch
import traceback
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

download_models()
print("Models downloaded successfully.")
device = "cuda" if torch.cuda.is_available() else "cpu"
sam_model=sam_model_registry["vit_b"](checkpoint="weights/sam_vit_b_01ec64.pth").to("cpu")
predictor = SamPredictor(sam_model)

model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32)
upsampler = RealESRGANer(
    scale=4, 
    model_path='weights/RealESRGAN_x4plus.pth',  
    model=model,
    tile=0,
    device=device,
)
print(" model loaded successfully.")
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

def replace_bg(img: Image.Image, bg: Image.Image) -> io.BytesIO:
    if predictor is None:
        raise ValueError("Predictor object is None. Initialize it before calling replace_bg.")
    try:
        image = np.array(img)
        
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif len(image.shape) == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
                
        MAX_DIM = 1024
        if max(image.shape[:2]) > MAX_DIM:
            scale = MAX_DIM / max(image.shape[:2])
            new_size = (int(image.shape[1] * scale), int(image.shape[0] * scale))
            image = cv2.resize(image, new_size)
        
        if image.size == 0 or image is None:
            raise ValueError("Invalid image after preprocessing.")
            
        predictor.set_image(image)
        input_point = np.array([[image.shape[1] // 2, image.shape[0] // 2]])
        input_label = np.array([1])  
        masks, scores, _ = predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=True,
        )

        if bg.mode != "RGB":
            bg = bg.convert("RGB")
        bg_np = np.array(bg)
        background = cv2.resize(bg_np, (image.shape[1], image.shape[0]))

        best_mask = masks[np.argmax(scores)]
        background = cv2.resize(bg_np, (image.shape[1], image.shape[0]))
        mask_3ch = np.repeat(best_mask[:, :, np.newaxis], 3, axis=2)
        foreground = np.where(mask_3ch, image, 0)
        final_result = np.where(mask_3ch, foreground, background)
    except Exception as e:
        return str(e)
    pil_res = Image.fromarray(cv2.cvtColor(final_result, cv2.COLOR_BGR2RGB))
    img_io = io.BytesIO()
    img_format = img.format if img.format else 'JPEG'
    pil_res.save(img_io, format=img_format)
    img_io.seek(0)
    return img_io

