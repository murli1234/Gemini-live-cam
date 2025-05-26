"""
Wrapper interface for Gemini Live AudioLoop functionality.
This module provides a simplified API to interact with the AudioLoop class.
"""

import asyncio
from gemini_live_cam import AudioLoop

# Global instance of AudioLoop
_audio_loop = None

def _ensure_audio_loop(mode="camera"):
    """Ensure AudioLoop instance exists and is initialized with the correct mode."""
    global _audio_loop
    if _audio_loop is None:
        _audio_loop = AudioLoop(video_mode=mode)
    return _audio_loop

async def GEMINI_RUN(mode="camera"):
    """Run the main AudioLoop instance."""
    loop = _ensure_audio_loop(mode)
    await loop.run()

async def GEMINI_SEND_TEXT():
    """Send text input to the AudioLoop instance."""
    loop = _ensure_audio_loop()
    await loop.send_text()

async def GEMINI_GET_FRAMES():
    """Get frames from the camera."""
    loop = _ensure_audio_loop()
    await loop.get_frames()

async def GEMINI_GET_SCREEN():
    """Get screen capture frames."""
    loop = _ensure_audio_loop(mode="screen")
    await loop.get_screen()

async def GEMINI_SEND_REALTIME():
    """Send realtime input to the AudioLoop instance."""
    loop = _ensure_audio_loop()
    await loop.send_realtime()

async def GEMINI_LISTEN_AUDIO():
    """Listen to audio input."""
    loop = _ensure_audio_loop()
    await loop.listen_audio()

async def GEMINI_RECEIVE_AUDIO():
    """Receive audio from the AudioLoop instance."""
    loop = _ensure_audio_loop()
    await loop.receive_audio()

async def GEMINI_PLAY_AUDIO():
    """Play audio output."""
    loop = _ensure_audio_loop()
    await loop.play_audio()

async def GEMINI_STOP():
    """Stop the AudioLoop instance."""
    global _audio_loop
    if _audio_loop is not None:
        success = await _audio_loop.stop()
        _audio_loop = None
        return success
    return True

# Helper function to run any of the async functions
def run_async(func, *args, **kwargs):
    """Helper function to run any of the async functions."""
    return asyncio.run(func(*args, **kwargs))

# Example usage:
if __name__ == "__main__":
    # Example: Run the main loop with camera mode
    run_async(GEMINI_RUN, mode="camera")
    
    # Example: Run with screen capture mode
    # run_async(GEMINI_RUN, mode="screen") 
