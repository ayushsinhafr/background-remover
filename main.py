from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove
from PIL import Image
import io
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Fix CORS Issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API Key
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"

def upload_to_imgbb(image_bytes):
    """Uploads image to ImgBB and returns the image URL."""
    response = requests.post(
        IMGBB_UPLOAD_URL,
        data={"key": IMGBB_API_KEY},
        files={"image": ("image.png", io.BytesIO(image_bytes), "image/png")}
    )
    
    if response.status_code == 200:
        return response.json()["data"]["url"]
    return None

@app.post("/remove-bg/")
async def remove_bg(file: UploadFile = File(...)):
    try:
        # Read image
        image_data = await file.read()
        input_image = Image.open(io.BytesIO(image_data))

        # Upload original image to ImgBB
        input_img_url = upload_to_imgbb(image_data)
        if not input_img_url:
            return JSONResponse(status_code=500, content={"error": "Failed to upload input image."})

        # Remove background
        output_image = remove(input_image)

        # Convert output image to bytes
        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format="PNG")
        output_bytes = output_buffer.getvalue()

        # Upload processed image to ImgBB
        output_img_url = upload_to_imgbb(output_bytes)
        if not output_img_url:
            return JSONResponse(status_code=500, content={"error": "Failed to upload output image."})

        return {
            "status": "success",
            "input_image_url": input_img_url,
            "output_image_url": output_img_url
        }

    except Exception as e:
        return {"error": str(e)}
