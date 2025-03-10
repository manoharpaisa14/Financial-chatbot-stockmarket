import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
STOCK_API_KEY = os.getenv("STOCK_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")