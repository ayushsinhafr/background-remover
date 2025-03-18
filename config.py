from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get API key from .env
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
