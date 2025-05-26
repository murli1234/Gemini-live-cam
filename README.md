# Gemini Live

A Python-based application that provides a user interface for interacting with Google's Gemini Live API. This project allows you to have real-time conversations with Gemini while capturing video input from your camera.

## Features

- Interactive Streamlit-based user interface
- Real-time video capture and processing
- Text-based conversation with Gemini AI
- Session management for Gemini Live interactions
- Camera feed display
- Easy API key configuration

## Prerequisites

- Python 3.8 or higher
- Google Cloud API key with Gemini API access
- Webcam or camera device

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gemini-live.git
cd gemini-live
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Set up your Google Cloud API key:
   - Create a `.env` file in the project root directory
   - Add your API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. The application will open in your default web browser with the following features:
   - API key input field (if not configured in .env)
   - Start/Stop session controls
   - Text input for conversation
   - Camera feed display
   - Conversation history

3. To interact with Gemini:
   - Click "Start Session" to begin
   - Type your message in the text input
   - Press Enter or click the send button
   - View the response in the conversation history

## Project Structure

```
gemini-live/
├── app.py              # Main Streamlit application
├── backend.py          # Core Gemini Live functionality
├── requirements.txt    # Project dependencies
├── .env               # Environment variables (API key)
└── README.md          # Project documentation
```

## Dependencies

- streamlit
- google-generativeai
- opencv-python
- python-dotenv
- numpy
- pillow

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini API
- Streamlit
- OpenCV 