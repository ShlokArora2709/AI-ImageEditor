from PIL import Image
import io

def resize_image(img:Image, width:int, height:int)->io.BytesIO:
    resized_img = img.resize((width, height), Image.LANCZOS)
    
    # Create an in-memory image to return
    img_io = io.BytesIO()
    img_format = img.format if img.format else 'JPEG'
    resized_img.save(img_io, format=img_format)
    img_io.seek(0)
    
    return img_io