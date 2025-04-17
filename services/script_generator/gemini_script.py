import os
import json
import logging
import google.generativeai as genai
from typing import Dict, Any, List
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not found in environment variables")

async def generate_script(prompt: str) -> Dict[str, Any]:
    """
    Generate a script with scenes using Gemini AI
    
    Args:
        prompt: The user's prompt for the video
        
    Returns:
        Dict[str, Any]: The generated script with scenes
    """
    try:
        logger.info(f"Generating script for prompt: {prompt}")
        
        # If no API key, return a mock script for development
        if not GEMINI_API_KEY:
            logger.warning("Using mock script generator as GEMINI_API_KEY is not set")
            return generate_mock_script(prompt)
        
        # Configure the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Create the prompt for Gemini
        gemini_prompt = f"""Create an educational video script with precise timestamps for a video about: "{prompt}".
        Format the script as JSON with the following structure:
        {{
          "title": "Video Title",
          "description": "Brief description of the video",
          "scenes": [
            {{
              "startTime": "00:00",
              "endTime": "00:XX",
              "narration": "What should be spoken during this scene",
              "visualDescription": "Detailed description of what should be shown visually, suitable for generating Manim code"
            }}
          ]
        }}
        Make sure each scene has detailed visual descriptions that can be used to generate mathematical animations with Manim.
        Keep scenes between 5-20 seconds each.
        The visual descriptions should be very specific about what mathematical elements to show and how they should be animated.
        Include at least 3 scenes but no more than 6 scenes.
        """
        
        # Generate content
        response = await model.generate_content_async(gemini_prompt)
        
        # Extract the JSON from the response
        text_response = response.text
        
        # Try to extract JSON if it's wrapped in markdown code blocks
        json_match = re.search(r'```json\n([\s\S]*?)\n```', text_response) or \
                     re.search(r'```\n([\s\S]*?)\n```', text_response)
        
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = text_response
        
        # Parse the JSON
        script = json.loads(json_str)
        
        # Validate the script structure
        if not validate_script(script):
            raise ValueError("Generated script does not have the expected structure")
        
        logger.info(f"Successfully generated script with {len(script['scenes'])} scenes")
        return script
        
    except Exception as e:
        logger.exception(f"Error generating script: {str(e)}")
        # Fall back to mock script in case of error
        return generate_mock_script(prompt)

def validate_script(script: Dict[str, Any]) -> bool:
    """
    Validate that the script has the expected structure
    
    Args:
        script: The script to validate
        
    Returns:
        bool: True if the script is valid, False otherwise
    """
    if not isinstance(script, dict):
        return False
    
    required_keys = ["title", "description", "scenes"]
    if not all(key in script for key in required_keys):
        return False
    
    if not isinstance(script["scenes"], list) or len(script["scenes"]) == 0:
        return False
    
    scene_keys = ["startTime", "endTime", "narration", "visualDescription"]
    for scene in script["scenes"]:
        if not all(key in scene for key in scene_keys):
            return False
    
    return True

def generate_mock_script(prompt: str) -> Dict[str, Any]:
    """
    Generate a mock script for development purposes
    
    Args:
        prompt: The user's prompt for the video
        
    Returns:
        Dict[str, Any]: A mock script
    """
    return {
        "title": f"Understanding {prompt}",
        "description": f"An educational video explaining {prompt} with visual animations.",
        "scenes": [
            {
                "startTime": "00:00",
                "endTime": "00:10",
                "narration": f"Welcome to this video about {prompt}. We'll explore this concept with visual examples.",
                "visualDescription": "Show a title text with the prompt. Then animate it to move to the top of the screen. Create a circle in the center that pulses to draw attention."
            },
            {
                "startTime": "00:10",
                "endTime": "00:25",
                "narration": f"Let's start by understanding the basic principles of {prompt}. This concept is fundamental in mathematics.",
                "visualDescription": "Display a mathematical equation related to the topic. For example, if it's about circles, show the equation of a circle (x-h)² + (y-k)² = r². Animate each part of the equation appearing one by one, highlighting each term as it's mentioned."
            },
            {
                "startTime": "00:25",
                "endTime": "00:40",
                "narration": f"Now, let's see how {prompt} works in practice with a visual example.",
                "visualDescription": "Create a coordinate system. Plot a function or shape related to the topic. If it's about the Pythagorean theorem, show a right triangle and label the sides a, b, and c. Then show a² + b² = c² with squares growing from each side of the triangle."
            },
            {
                "startTime": "00:40",
                "endTime": "00:55",
                "narration": f"To summarize what we've learned about {prompt}, let's review the key points.",
                "visualDescription": "Create a bulleted list with 3 key points about the topic. Have each point appear one by one with a small animation. End with a final animation that brings back the main equation or diagram from earlier, but now with additional annotations or highlighting."
            }
        ]
    }
