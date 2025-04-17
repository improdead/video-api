import os
import logging
import asyncio
import tempfile
from typing import List
from pathlib import Path
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

async def combine_audio_video(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Combine audio and video files using FFmpeg
    
    Args:
        video_path: Path to the video file
        audio_path: Path to the audio file
        output_path: Path to save the combined file
        
    Returns:
        str: Path to the combined file
    """
    try:
        logger.info(f"Combining video {video_path} and audio {audio_path} to {output_path}")
        
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Check if FFmpeg is available
        try:
            # Combine audio and video with FFmpeg
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Audio and video combined successfully to {output_path}")
                return output_path
            else:
                logger.error(f"FFmpeg failed: {stderr.decode()}")
                # Fall back to just copying the video file
                return await fallback_copy(video_path, output_path)
                
        except Exception as e:
            logger.warning(f"Error combining audio and video with FFmpeg: {str(e)}")
            # Fall back to just copying the video file
            return await fallback_copy(video_path, output_path)
            
    except Exception as e:
        logger.exception(f"Error combining audio and video: {str(e)}")
        # Fall back to just copying the video file
        return await fallback_copy(video_path, output_path)

async def concat_videos(video_paths: List[str], output_path: str) -> str:
    """
    Concatenate multiple video files using FFmpeg
    
    Args:
        video_paths: List of paths to video files
        output_path: Path to save the concatenated file
        
    Returns:
        str: Path to the concatenated file
    """
    try:
        logger.info(f"Concatenating {len(video_paths)} videos to {output_path}")
        
        if not video_paths:
            logger.error("No video paths provided for concatenation")
            return ""
        
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # If there's only one video, just copy it
        if len(video_paths) == 1:
            return await fallback_copy(video_paths[0], output_path)
        
        # Check if FFmpeg is available
        try:
            # Create a temporary file listing all videos to concatenate
            temp_dir = tempfile.mkdtemp()
            list_file_path = os.path.join(temp_dir, "video_list.txt")
            
            with open(list_file_path, "w") as f:
                for video_path in video_paths:
                    f.write(f"file '{os.path.abspath(video_path)}'\n")
            
            # Concatenate videos with FFmpeg
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file_path,
                "-c", "copy",
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Clean up the temporary file
            try:
                os.remove(list_file_path)
                os.rmdir(temp_dir)
            except Exception as e:
                logger.warning(f"Error cleaning up temporary file: {str(e)}")
            
            if process.returncode == 0:
                logger.info(f"Videos concatenated successfully to {output_path}")
                return output_path
            else:
                logger.error(f"FFmpeg failed: {stderr.decode()}")
                # Fall back to just copying the first video file
                return await fallback_copy(video_paths[0], output_path)
                
        except Exception as e:
            logger.warning(f"Error concatenating videos with FFmpeg: {str(e)}")
            # Fall back to just copying the first video file
            return await fallback_copy(video_paths[0], output_path)
            
    except Exception as e:
        logger.exception(f"Error concatenating videos: {str(e)}")
        # Fall back to just copying the first video file if available
        if video_paths:
            return await fallback_copy(video_paths[0], output_path)
        return ""

async def fallback_copy(source_path: str, dest_path: str) -> str:
    """
    Fallback method to copy a file when FFmpeg operations fail
    
    Args:
        source_path: Path to the source file
        dest_path: Path to the destination file
        
    Returns:
        str: Path to the destination file
    """
    try:
        logger.info(f"Falling back to copying {source_path} to {dest_path}")
        
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Copy the file
        shutil.copy2(source_path, dest_path)
        
        logger.info(f"File copied successfully to {dest_path}")
        return dest_path
    except Exception as e:
        logger.exception(f"Error copying file: {str(e)}")
        return ""
