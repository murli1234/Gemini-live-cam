"""
## Documentation
Quickstart: https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveAPI.py

## Setup

To install the dependencies for this script, run:

```
pip install google-genai opencv-python pyaudio pillow mss python-dotenv
```
"""

import asyncio
import base64
import io
import traceback
import sys

import cv2
import pyaudio
import PIL.Image
import mss

import argparse

from google import genai
from google.genai import types

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Validate API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables")
    print("Please create a .env file with your API key:")
    print("GEMINI_API_KEY=your_api_key_here")
    sys.exit(1)

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.0-flash-live-001"

DEFAULT_MODE = "camera"

try:
    client = genai.Client(http_options={"api_version": "v1alpha"}, api_key=api_key)
except Exception as e:
    print(f"Error initializing Gemini client: {str(e)}")
    sys.exit(1)

tools = [
    types.Tool(google_search=types.GoogleSearch()),
]

# While Gemini 2.0 Flash is in experimental preview mode, only one of AUDIO or
# TEXT may be passed here.
CONFIG = types.LiveConnectConfig(
    response_modalities=[
        types.Modality.AUDIO,
    ],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Leda")
        )
    ),
    tools=types.ToolListUnion(tools),
)

pya = pyaudio.PyAudio()


class AudioLoop:
    def __init__(self, video_mode=DEFAULT_MODE):
        self.video_mode = video_mode

        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue(maxsize=5)

        self.session = None  # Will be initialized in the run method

        self.send_text_task = None
        self.receive_audio_task = None
        self.play_audio_task = None

    async def send_text(self):
        while True:
            text = await asyncio.to_thread(
                input,
                "message > ",
            )
            if text.lower() == "q":
                break
            if self.session is not None:
                await self.session.send_client_content(
                    turns=types.Content(
                        role="user",
                        parts=[types.Part(text=text or ".")]
                    )
                )
            else:
                print("Session is not initialized. Unable to send text.")

    def _get_frame(self, cap):
        # Read the frame
        ret, frame = cap.read()
        # Check if the frame was read successfully
        if not ret:
            return None

        # Display the frame in an OpenCV window
        cv2.imshow('Gemini Live Camera', frame)

        # Check for ESC key press (27 is the ASCII code for ESC)
        key = cv2.waitKey(1)
        if key == 27:  # ESC key
            return "ESC_PRESSED"

        # Fix: Convert BGR to RGB color space
        # OpenCV captures in BGR but PIL expects RGB format
        # This prevents the blue tint in the video feed
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)  # Now using RGB frame
        img.thumbnail((1024, 1024))

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        mime_type = "image/jpeg"
        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_frames(self):
        try:
            cap = await asyncio.to_thread(
                cv2.VideoCapture, 0
            )  # 0 represents the default camera

            # Check if camera opened successfully
            if not cap.isOpened():
                print("Error: Could not open camera.")
                return

            while True:
                frame = await asyncio.to_thread(self._get_frame, cap)

                # Check if frame is None (camera disconnected) or ESC was pressed
                if frame is None:
                    print("Camera disconnected.")
                    break
                elif frame == "ESC_PRESSED":
                    print("ESC key pressed. Stopping camera feed.")
                    break

                await asyncio.sleep(1.0)
                await self.out_queue.put(frame)

        except Exception as e:
            print(f"Error in get_frames: {str(e)}")
        finally:
            # Release the VideoCapture object and destroy all OpenCV windows
            if 'cap' in locals() and cap is not None:
                cap.release()
            cv2.destroyAllWindows()
            print("Camera resources released.")

    def _get_screen(self):
        sct = mss.mss()
        monitor = sct.monitors[0]

        i = sct.grab(monitor)

        mime_type = "image/jpeg"
        image_bytes = i.rgb  # Directly use the RGB data from the screen capture
        img = PIL.Image.open(io.BytesIO(image_bytes))

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_screen(self):

        while True:
            frame = await asyncio.to_thread(self._get_screen)
            if frame is None:
                break

            await asyncio.sleep(1.0)

            await self.out_queue.put(frame)

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            if self.session is not None:
                # For audio: send as types.Blob
                await self.session.send_realtime_input(
                    media=types.Blob(data=msg["data"], mime_type=msg["mime_type"])
                )
            else:
                print("Session is not initialized. Unable to send message.")

    async def listen_audio(self):
        mic_info = pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=int(mic_info["index"]),
            frames_per_buffer=CHUNK_SIZE,
        )
        if __debug__:
            kwargs = {"exception_on_overflow": False}
        else:
            kwargs = {}
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def receive_audio(self):
        "Background task to reads from the websocket and write pcm chunks to the output queue"
        while True:
            if self.session is None:
                print("Session is not initialized. Unable to receive data.")
                await asyncio.sleep(1)  # Prevent tight loop if session is not ready
                continue

            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                    continue
                if text := response.text:
                    print(text, end="")

            # If you interrupt the model, it sends a turn_complete.
            # For interruptions to work, we need to stop playback.
            # So empty out the audio queue because it may have loaded
            # much more audio than has played yet.
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            bytestream = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, bytestream)

    async def run(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session

                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                if self.video_mode == "camera":
                    tg.create_task(self.get_frames())
                elif self.video_mode == "screen":
                    tg.create_task(self.get_screen())

                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await send_text_task
                raise asyncio.CancelledError("User requested exit")

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as EG:
            self.audio_stream.close()
            traceback.print_exception(EG)

    async def stop(self):
        """Stop the camera and microphone"""
        try:
            print("Stopping camera and microphone...")

            # Close any OpenCV windows
            try:
                cv2.destroyAllWindows()
                print("Closed OpenCV windows")
            except Exception as e:
                print(f"Error closing OpenCV windows: {str(e)}")

            # Stop audio stream if it exists
            if hasattr(self, 'audio_stream') and self.audio_stream:
                print("Stopping audio stream...")
                try:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except Exception as e:
                    print(f"Error stopping audio stream: {str(e)}")
                finally:
                    self.audio_stream = None

            # Clear all queues
            print("Clearing queues...")
            try:
                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()
                while not self.out_queue.empty():
                    self.out_queue.get_nowait()
            except Exception as e:
                print(f"Error clearing queues: {str(e)}")

            # Close session if it exists
            if self.session:
                print("Closing session...")
                try:
                    # Set a timeout for session closing to prevent hanging
                    close_task = asyncio.create_task(self.session.close())
                    try:
                        # Wait for up to 5 seconds for the session to close
                        await asyncio.wait_for(close_task, timeout=5.0)
                        print("Session closed successfully")
                    except asyncio.TimeoutError:
                        print("Session close timed out, forcing closure")
                except Exception as e:
                    print(f"Error closing session: {str(e)}")
                finally:
                    self.session = None

            # Cancel all running tasks
            print("Cancelling tasks...")
            try:
                # Get the current task to avoid cancelling ourselves
                current_task = asyncio.current_task()

                # Only cancel tasks that are part of our application
                # This is safer than cancelling all tasks in the event loop
                tasks_to_cancel = []
                for task in asyncio.all_tasks():
                    if task != current_task:
                        # Check if the task is related to our application
                        task_name = task.get_name()
                        if "gemini" in task_name.lower() or "audio" in task_name.lower() or "send" in task_name.lower() or "receive" in task_name.lower():
                            tasks_to_cancel.append(task)

                # Cancel the identified tasks
                for task in tasks_to_cancel:
                    print(f"Cancelling task: {task.get_name()}")
                    task.cancel()

                # Wait for all tasks to be cancelled
                if tasks_to_cancel:
                    await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

                print(f"Successfully cancelled {len(tasks_to_cancel)} tasks")
            except Exception as e:
                print(f"Error cancelling tasks: {str(e)}")

            print("Camera and microphone stopped successfully")
            return True
        except Exception as e:
            print(f"Error stopping camera and microphone: {str(e)}")
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        help="pixels to stream from",
        choices=["camera", "screen", "none"],
    )
    args = parser.parse_args()
    main = AudioLoop(video_mode=args.mode)
    asyncio.run(main.run())
