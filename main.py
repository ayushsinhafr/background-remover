import os
import io
import base64
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from rembg import remove, new_session
from PIL import Image
import uvicorn

# FastAPI app
app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMGBB API Key from environment variable
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
if not IMGBB_API_KEY:
    raise ValueError("IMGBB_API_KEY environment variable not set")

# Initialize rembg session in low-memory mode
session = new_session("u2net", low_memory=True)

# Function to upload image to IMGBB
def upload_to_imgbb(image: Image.Image) -> str:
    # Convert image to bytes
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()

    # Encode image to base64
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")

    # Upload to IMGBB
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": IMGBB_API_KEY,
        "image": img_base64,
    }
    response = requests.post(url, payload)
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to upload image to IMGBB")
    
    data = response.json()
    return data["data"]["url"]

# Endpoint to remove background
@app.post("/remove-bg/")
async def remove_background(file: UploadFile = File(...)):
    try:
        # Read the uploaded image
        contents = await file.read()
        input_image = Image.open(io.BytesIO(contents)).convert("RGBA")

        # Remove background using rembg in low-memory mode
        output_image = remove(input_image, session=session)

        # Upload input and output images to IMGBB
        input_url = upload_to_imgbb(input_image)
        output_url = upload_to_imgbb(output_image)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "input_image_url": input_url,
                "output_image_url": output_url,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)