from dotenv import load_dotenv
from fastapi import FastAPI

# Load environment variables from .env file
load_dotenv()

from .routers import audio

app = FastAPI()

app.include_router(audio.router)
