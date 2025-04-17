import os
import logging
import requests
import json
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# ElevenLabs API key
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

async def generate_speech(text: str, output_path: str, voice_id: str = "pNInz6obpgDQGcFmaJgB") -> str:
    """
    Generate speech from text using ElevenLabs API
    
    Args:
        text: The text to convert to speech
        output_path: The path to save the audio file
        voice_id: The ElevenLabs voice ID to use
        
    Returns:
        str: The path to the generated audio file
    """
    try:
        logger.info(f"Generating speech for text: {text[:50]}...")
        
        # If no API key, generate a mock audio file
        if not ELEVENLABS_API_KEY:
            logger.warning("Using mock TTS as ELEVENLABS_API_KEY is not set")
            return await generate_mock_audio(output_path)
        
        # Prepare the API request
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        # Make the API request
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the audio file
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Speech generated successfully and saved to {output_path}")
            return output_path
        else:
            logger.error(f"Error generating speech: {response.status_code} - {response.text}")
            # Fall back to mock audio
            return await generate_mock_audio(output_path)
            
    except Exception as e:
        logger.exception(f"Error generating speech: {str(e)}")
        # Fall back to mock audio
        return await generate_mock_audio(output_path)

async def generate_mock_audio(output_path: str) -> str:
    """
    Generate a mock audio file for development purposes
    
    Args:
        output_path: The path to save the audio file
        
    Returns:
        str: The path to the generated audio file
    """
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create an empty MP3 file
        with open(output_path, "wb") as f:
            # Write a minimal MP3 header (not a valid MP3, but enough for testing)
            f.write(b"\xFF\xFB\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        
        logger.info(f"Mock audio file created at {output_path}")
        return output_path
    except Exception as e:
        logger.exception(f"Error creating mock audio: {str(e)}")
        return output_path
