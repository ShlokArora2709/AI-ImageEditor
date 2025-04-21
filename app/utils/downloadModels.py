import os
import requests
from tqdm import tqdm


WEIGHTS_DIR = "weights"
REAL_ESRGAN_WEIGHTS_FILE = "RealESRGAN_x4plus.pth"
REAL_ESRGAN_WEIGHTS_PATH = os.path.join(WEIGHTS_DIR, REAL_ESRGAN_WEIGHTS_FILE)
REAL_ESRGAN_WEIGHTS_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"

def download_models():
# Ensure weights directory exists
    if not os.path.exists(WEIGHTS_DIR):
        os.makedirs(WEIGHTS_DIR)

    # Download Real-ESRGAN weights if not already present
    if not os.path.exists(REAL_ESRGAN_WEIGHTS_PATH):
        print(f"Downloading {REAL_ESRGAN_WEIGHTS_FILE}...")
        response = requests.get(REAL_ESRGAN_WEIGHTS_URL, stream=True)
        if response.status_code == 200:
            with open(REAL_ESRGAN_WEIGHTS_PATH, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"{REAL_ESRGAN_WEIGHTS_FILE} downloaded successfully.")
        else:
            raise Exception(f"Failed to download {REAL_ESRGAN_WEIGHTS_FILE}. Status code: {response.status_code}")
    else:
        print(f"{REAL_ESRGAN_WEIGHTS_FILE} already exists.")
    

    url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
    file_path = os.path.join(WEIGHTS_DIR, "sam_vit_b_01ec64.pth")

    if os.path.exists(file_path):
        print("SAM ViT-B weights already downloaded.")
        return file_path

    print("Downloading SAM ViT-B weights...")
    response = requests.get(url, stream=True)
    total = int(response.headers.get("content-length", 0))

    with open(file_path, "wb") as file, tqdm(
        desc="Downloading",
        total=total,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

    print("Download complete.")
