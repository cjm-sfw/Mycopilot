from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    # API Keys
    serpapi_key: str = os.getenv("SERPAPI_KEY", "")
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    
    # Redis Configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    
    # Application settings
    debug_mode: bool = os.getenv("DEBUG", "False").lower() == "true"

settings = Settings()
