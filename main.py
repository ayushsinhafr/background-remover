import os
import io
import base64
import requests
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from rembg import remove, new_session
from PIL import Image, ImageFilter
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://backgroundremove.tech"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMGBB API Key from environment variable
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
if not IMGBB_API_KEY:
    logger.error("IMGBB_API_KEY environment variable not set")
    raise ValueError("IMGBB_API_KEY environment variable not set")

# Initialize rembg session with pre-downloaded u2net model
try:
    session = new_session("u2net", low_memory=True, model_path=".u2net/u2net.onnx")
    logger.info("Successfully initialized rembg session with u2net model")
except Exception as e:
    logger.error(f"Failed to initialize rembg session: {str(e)}")
    raise Exception(f"Failed to initialize rembg session: {str(e)}")

# Function to upload image to IMGBB
def upload_to_imgbb(image: Image.Image) -> str:
    try:
        # Convert image to bytes
        buffered = io.BytesIO()
        image.save(buffered, format="PNG", quality=100)
        img_bytes = buffered.getvalue()

        # Encode image to base64
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        # Upload to IMGBB
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
            "image": img_base64,
            "expiration": 0
        }
        response = requests.post(url, payload)
        
        if response.status_code != 200:
            logger.error(f"Failed to upload image to IMGBB: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to upload image to IMGBB")
        
        data = response.json()
        logger.info(f"Successfully uploaded image to IMGBB: {data['data']['url']}")
        return data["data"]["url"]
    except Exception as e:
        logger.error(f"Error uploading image to IMGBB: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading image to IMGBB: {str(e)}")

# Endpoint to remove background
@app.post("/remove-bg/")
async def remove_background(file: UploadFile = File(...)):
    try:
        # Validate file size (limit to 2MB)
        contents = await file.read()
        if len(contents) > 2 * 1024 * 1024:  # 2MB limit
            logger.warning("Uploaded file too large")
            raise HTTPException(status_code=400, detail="File size exceeds 2MB limit")

        # Read the uploaded image
        logger.info("Processing uploaded image")
        input_image = Image.open(io.BytesIO(contents)).convert("RGBA")

        # Remove background using rembg
        logger.info("Removing background with rembg")
        output_image = remove(
            input_image,
            session=session,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )

        # Apply median filter to reduce noise
        logger.info("Applying median filter to output image")
        output_image = output_image.filter(ImageFilter.MedianFilter(size=3))

        # Upload input and output images to IMGBB
        logger.info("Uploading input image to IMGBB")
        input_url = upload_to_imgbb(input_image)
        logger.info("Uploading output image to IMGBB")
        output_url = upload_to_imgbb(output_image)

        logger.info("Background removal successful")
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "input_image_url": input_url,
                "output_image_url": output_url,
            },
        )
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)