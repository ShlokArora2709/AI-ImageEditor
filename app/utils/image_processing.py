from PIL import Image, ImageEnhance,ImageFilter
import io
import cv2
import numpy as np
from rembg import remove

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