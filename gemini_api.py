from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
import asyncio
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
import os
from gemini_key import (
    GEMINI_RUN,
    GEMINI_SEND_TEXT,
    GEMINI_GET_FRAMES,
    GEMINI_GET_SCREEN,
    GEMINI_SEND_REALTIME,
    GEMINI_LISTEN_AUDIO,
    GEMINI_RECEIVE_AUDIO,
    GEMINI_PLAY_AUDIO,
    GEMINI_STOP
)

# Load environment variables
load_dotenv()

# Set up logging with file handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gemini_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Validate API key on startup
if not os.getenv("GEMINI_API_KEY"):
    logger.error("GEMINI_API_KEY not found in environment variables")
    raise SystemExit("Error: GEMINI_API_KEY not found. Please set it in your .env file")

app = FastAPI(
    title="Gemini Live API",
    description="API interface for Gemini Live functionality",
    version="1.0.0"
)

class ModeRequest(BaseModel):
    mode: Literal["camera", "screen"] = Field(
        default="camera",
        description="Mode to run Gemini Live in. Can be either 'camera' or 'screen'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "mode": "camera"
            }
        }

class ResponseModel(BaseModel):
    status: str
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

@app.get("/")
async def root():
    """Root endpoint that provides API information"""
    return {
        "status": "success",
        "message": "Welcome to Gemini Live API",
        "endpoints": {
            "/run": {
                "method": "POST",
                "description": "Start Gemini Live session",
                "body": {"mode": "camera|screen"}
            },
            "/send-text": {
                "method": "POST",
                "description": "Send text input"
            },
            "/get-frames": {
                "method": "POST",
                "description": "Get camera frames"
            },
            "/get-screen": {
                "method": "POST",
                "description": "Get screen capture"
            },
            "/send-realtime": {
                "method": "POST",
                "description": "Send realtime input"
            },
            "/listen-audio": {
                "method": "POST",
                "description": "Listen to audio"
            },
            "/receive-audio": {
                "method": "POST",
                "description": "Receive audio"
            },
            "/play-audio": {
                "method": "POST",
                "description": "Play audio"
            },
            "/stop": {
                "method": "POST",
                "description": "Stop the Gemini Live session"
            },
            "/stop-camera": {
                "method": "POST",
                "description": "Stop the camera and microphone"
            }
        },
        "timestamp": datetime.now().isoformat()
    }

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses for debugging"""
    request_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    logger.info(f"[{request_id}] Request started: {request.method} {request.url}")

    # Log request headers
    headers = dict(request.headers)
    logger.info(f"[{request_id}] Request headers: {json.dumps(headers, indent=2)}")

    # Log request body if present
    try:
        body = await request.body()
        if body:
            logger.info(f"[{request_id}] Request body: {body.decode()}")
    except Exception as e:
        logger.error(f"[{request_id}] Error reading request body: {str(e)}")

    # Process the request
    try:
        response = await call_next(request)
        logger.info(f"[{request_id}] Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"[{request_id}] Error processing request: {str(e)}")
        raise

@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    """Handle validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    return Response(
        content=json.dumps({
            "status": "error",
            "message": "Validation error",
            "details": exc.errors(),
            "timestamp": datetime.now().isoformat()
        }),
        status_code=422,
        media_type="application/json"
    )

@app.post("/run", response_model=ResponseModel)
async def run_gemini(req: ModeRequest):
    """
    Start the Gemini Live session with specified mode.

    - **mode**: Can be either "camera" or "screen"
    """
    try:
        logger.info(f"Starting Gemini Live with mode: {req.mode}")
        await GEMINI_RUN(mode=req.mode)
        return {
            "status": "success",
            "message": f"Started Gemini Live in {req.mode} mode",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in run_gemini: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-text", response_model=ResponseModel)
async def send_text():
    """Send text input to the Gemini Live session."""
    try:
        logger.info("Sending text input")
        await GEMINI_SEND_TEXT()
        return {
            "status": "success",
            "message": "Text input sent",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in send_text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-frames", response_model=ResponseModel)
async def get_frames():
    """Get frames from the camera."""
    try:
        logger.info("Getting frames from camera")
        await GEMINI_GET_FRAMES()
        return {
            "status": "success",
            "message": "Frames captured",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in get_frames: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-screen", response_model=ResponseModel)
async def get_screen():
    """Get screen capture frames."""
    try:
        logger.info("Getting screen capture")
        await GEMINI_GET_SCREEN()
        return {
            "status": "success",
            "message": "Screen captured",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in get_screen: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-realtime", response_model=ResponseModel)
async def send_realtime():
    """Send realtime input to the Gemini Live session."""
    try:
        logger.info("Sending realtime input")
        await GEMINI_SEND_REALTIME()
        return {
            "status": "success",
            "message": "Realtime input sent",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in send_realtime: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/listen-audio", response_model=ResponseModel)
async def listen_audio():
    """Listen to audio input."""
    try:
        logger.info("Starting audio listening")
        await GEMINI_LISTEN_AUDIO()
        return {
            "status": "success",
            "message": "Listening to audio",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in listen_audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/receive-audio", response_model=ResponseModel)
async def receive_audio():
    """Receive audio from the Gemini Live session."""
    try:
        logger.info("Receiving audio")
        await GEMINI_RECEIVE_AUDIO()
        return {
            "status": "success",
            "message": "Audio received",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in receive_audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/play-audio", response_model=ResponseModel)
async def play_audio():
    """Play audio output."""
    try:
        logger.info("Starting audio playback")
        await GEMINI_PLAY_AUDIO()
        return {
            "status": "success",
            "message": "Audio playback started",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in play_audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop", response_model=ResponseModel)
async def stop_gemini():
    """
    Stop the Gemini Live session.
    """
    try:
        # Check API key
        if not os.getenv("GEMINI_API_KEY"):
            logger.error("GEMINI_API_KEY not found when trying to stop session")
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY not found in environment variables"
            )

        logger.info("Stopping Gemini Live session")
        success = await GEMINI_STOP()  # Call the actual stop function
        if not success:
            logger.error("Failed to stop Gemini Live session")
            raise HTTPException(status_code=500, detail="Failed to stop session")
        return {
            "status": "success",
            "message": "Session ended successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in stop_gemini: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop session: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)