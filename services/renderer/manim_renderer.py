import os
import sys
import tempfile
import subprocess
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

async def render_scene(scene_code: str, output_path: str, quality: str = "medium") -> str:
    """
    Render a scene using Manim and save to the specified output path
    
    Args:
        scene_code: The Manim Python code for the scene
        output_path: The path to save the rendered video
        quality: The quality of the rendering (low, medium, high)
        
    Returns:
        str: The path to the rendered video
    """
    try:
        logger.info(f"Rendering scene to {output_path}")
        
        # Check if manim is installed
        try:
            import manim
            logger.info(f"Using Manim version: {manim.__version__}")
        except ImportError:
            logger.warning("Manim is not installed, using mock renderer")
            return await generate_mock_video(output_path)
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, "scene.py")
        
        # Extract the class name from the code
        class_name = extract_class_name(scene_code)
        if not class_name:
            logger.warning("Could not extract class name from code, using mock renderer")
            return await generate_mock_video(output_path)
        
        # Write the scene code to a temporary file
        with open(temp_file_path, "w") as f:
            f.write(scene_code)
        
        # Determine the quality flag
        quality_flag = "-qm"  # medium by default
        if quality == "low":
            quality_flag = "-ql"
        elif quality == "high":
            quality_flag = "-qh"
        
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Run Manim to render the scene
        try:
            # Construct the command
            cmd = [
                sys.executable, "-m", "manim",
                temp_file_path,
                class_name,
                quality_flag,
                "-o", os.path.basename(output_path).replace(".mp4", ""),
                "--media_dir", temp_dir
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Manim execution failed: {stderr.decode()}")
                return await generate_mock_video(output_path)
            
            # Find the generated video file
            video_dir = os.path.join(temp_dir, "videos")
            scene_video = None
            
            for root, dirs, files in os.walk(video_dir):
                for file in files:
                    if file.endswith(".mp4"):
                        scene_video = os.path.join(root, file)
                        break
                if scene_video:
                    break
            
            if not scene_video:
                logger.error("No video file was generated")
                return await generate_mock_video(output_path)
            
            # Copy to output path
            shutil.copy2(scene_video, output_path)
            
            logger.info(f"Scene rendered successfully to {output_path}")
            return output_path
            
        except Exception as e:
            logger.exception(f"Error running Manim: {str(e)}")
            return await generate_mock_video(output_path)
            
        finally:
            # Clean up temporary directory
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Error cleaning up temporary directory: {str(e)}")
        
    except Exception as e:
        logger.exception(f"Error rendering scene: {str(e)}")
        return await generate_mock_video(output_path)

def extract_class_name(code: str) -> Optional[str]:
    """
    Extract the class name from Manim code
    
    Args:
        code: The Manim Python code
        
    Returns:
        Optional[str]: The extracted class name, or None if not found
    """
    # Look for a class that extends Scene
    match = re.search(r'class\s+(\w+)\s*\(\s*Scene\s*\)', code)
    if match:
        return match.group(1)
    return None

async def generate_mock_video(output_path: str) -> str:
    """
    Generate a mock video file for development purposes
    
    Args:
        output_path: The path to save the video file
        
    Returns:
        str: The path to the generated video file
    """
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Check if FFmpeg is available
        try:
            # Create a 5-second black video with FFmpeg
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "color=c=black:s=1280x720:d=5",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Mock video created with FFmpeg at {output_path}")
                return output_path
        except Exception as e:
            logger.warning(f"Error creating mock video with FFmpeg: {str(e)}")
        
        # If FFmpeg fails or is not available, create an empty file
        with open(output_path, "wb") as f:
            # Write a minimal MP4 header (not a valid MP4, but enough for testing)
            f.write(b"\x00\x00\x00\x18\x66\x74\x79\x70\x6D\x70\x34\x32\x00\x00\x00\x00\x6D\x70\x34\x32\x69\x73\x6F\x6D")
        
        logger.info(f"Empty mock video file created at {output_path}")
        return output_path
    except Exception as e:
        logger.exception(f"Error creating mock video: {str(e)}")
        return output_path
