import streamlit as st
import asyncio
import os
import subprocess
import sys
from dotenv import load_dotenv
from gemini_live_cam import AudioLoop, client
import threading
import queue
import cv2
import numpy as np
from PIL import Image
import io
import signal

# Initialize all session state variables at the start
def init_session_state():
    if 'session_started' not in st.session_state:
        st.session_state.session_started = False
    if 'process' not in st.session_state:
        st.session_state.process = None
    if 'text_input' not in st.session_state:
        st.session_state.text_input = ""
    if 'api_key_status' not in st.session_state:
        st.session_state.api_key_status = False
    if 'camera_placeholder' not in st.session_state:
        st.session_state.camera_placeholder = None
    if 'camera_thread' not in st.session_state:
        st.session_state.camera_thread = None
    if 'cap' not in st.session_state:
        st.session_state.cap = None

# Call initialization
init_session_state()

# Check API key status
def check_api_key():
    try:
        # Try to access the client to verify API key
        if client:
            st.session_state.api_key_status = True
            return True
    except Exception as e:
        st.session_state.api_key_status = False
        return False

def start_session():
    """Start the backend file as a subprocess"""
    if not check_api_key():
        st.error("API key not found or invalid. Please check your .env file.")
        return
        
    try:
        # Start the backend file as a subprocess with stdin/stdout pipes
        st.session_state.process = subprocess.Popen(
            [sys.executable, 'gemini_live_cam.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        st.session_state.session_started = True
        st.success("Session started successfully!")
        
        # Create camera placeholder
        st.session_state.camera_placeholder = st.empty()
        
        # Start camera feed update in a separate thread
        st.session_state.camera_thread = threading.Thread(target=update_camera_feed, daemon=True)
        st.session_state.camera_thread.start()
    except Exception as e:
        st.error(f"Error starting session: {str(e)}")
        st.session_state.session_started = False
        st.session_state.process = None

def stop_session():
    """Stop the session and clean up resources"""
    try:
        if st.session_state.process:
            # Send SIGTERM to the process
            st.session_state.process.send_signal(signal.SIGTERM)
            # Wait for the process to terminate
            st.session_state.process.wait(timeout=5)
            st.session_state.process = None

        # Stop the camera feed
        st.session_state.session_started = False
        
        # Release camera
        if st.session_state.cap is not None:
            st.session_state.cap.release()
            st.session_state.cap = None

        if st.session_state.camera_placeholder:
            st.session_state.camera_placeholder.empty()
            
        # Wait for camera thread to finish
        if st.session_state.camera_thread and st.session_state.camera_thread.is_alive():
            st.session_state.camera_thread.join(timeout=1)

        st.success("Session stopped successfully!")
    except Exception as e:
        st.error(f"Error stopping session: {str(e)}")
        # Force kill if normal termination fails
        if st.session_state.process:
            st.session_state.process.kill()
            st.session_state.process = None

def update_camera_feed():
    if st.session_state.session_started:
        try:
            # Initialize camera
            st.session_state.cap = cv2.VideoCapture(0)

            while st.session_state.session_started:
                ret, frame = st.session_state.cap.read()
                if ret:
                    # Convert frame to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Convert to PIL Image
                    image = Image.fromarray(frame_rgb)
                    # Display in Streamlit
                    st.session_state.camera_placeholder.image(image, channels="RGB", use_column_width=True)
                else:
                    break

        except Exception as e:
            st.error(f"Error updating camera feed: {str(e)}")
        finally:
            # Release camera when done
            if st.session_state.cap is not None:
                st.session_state.cap.release()
                st.session_state.cap = None

def send_text():
    if not st.session_state.session_started:
        st.error("Please start the session first!")
        return

    if st.session_state.text_input and st.session_state.process:
        try:
            # Send text to the running process
            st.session_state.process.stdin.write(f"{st.session_state.text_input}\n")
            st.session_state.process.stdin.flush()

            # Read any response
            response = st.session_state.process.stdout.readline()
            if response:
                st.write(f"Response: {response}")
                
            st.session_state.text_input = ""  # Clear the input
        except Exception as e:
            st.error(f"Error sending text: {str(e)}")

# Main UI
st.title("Gemini Live Interface")

# API Key Status Section
st.header("API Key Status")
if check_api_key():
    st.success("API Key is valid and loaded")
else:
    st.error("API Key not found or invalid. Please check your .env file.")

# Session Control Section
st.header("Session Control")
col1, col2 = st.columns(2)
with col1:
    if st.button("Start Session", disabled=st.session_state.session_started or not st.session_state.api_key_status):
        start_session()
with col2:
    if st.button("Stop Session", disabled=not st.session_state.session_started):
        stop_session()

# Camera Feed Section
st.header("Camera Feed")
if st.session_state.session_started:
    if st.session_state.camera_placeholder is None:
        st.session_state.camera_placeholder = st.empty()
else:
    st.info("Camera feed will appear here when session starts")

# Text Interaction Section
st.header("Text Interaction")
st.text_input("Enter your message", key="text_input", disabled=not st.session_state.session_started)
if st.button("Send Text", disabled=not st.session_state.session_started):
    send_text()

# Status Section
st.header("Session Status")
if st.session_state.session_started:
    st.success("Session is active")
else:
    st.info("Session is not started")

# Instructions
st.header("Instructions")
st.markdown("""
1. Make sure your API key is properly set in the .env file
2. Click 'Start Session' to begin (this will start the backend and camera feed)
3. Use the text input to send messages to Gemini
4. Click 'Stop Session' when done
""") 