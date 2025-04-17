import os
import shutil
import logging
import tempfile
from pathlib import Path
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

def ensure_dir_exists(dir_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        bool: True if the directory exists or was created, False otherwise
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        logger.exception(f"Error creating directory {dir_path}: {str(e)}")
        return False

def create_temp_dir() -> Optional[str]:
    """
    Create a temporary directory
    
    Returns:
        Optional[str]: Path to the temporary directory, or None if creation failed
    """
    try:
        return tempfile.mkdtemp()
    except Exception as e:
        logger.exception(f"Error creating temporary directory: {str(e)}")
        return None

def clean_dir(dir_path: str) -> bool:
    """
    Clean a directory by removing all files and subdirectories
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        bool: True if the directory was cleaned, False otherwise
    """
    try:
        if os.path.exists(dir_path):
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        return True
    except Exception as e:
        logger.exception(f"Error cleaning directory {dir_path}: {str(e)}")
        return False

def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes
    
    Args:
        file_path: Path to the file
        
    Returns:
        int: Size of the file in bytes, or 0 if the file doesn't exist
    """
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0
    except Exception as e:
        logger.exception(f"Error getting file size for {file_path}: {str(e)}")
        return 0

def get_file_extension(file_path: str) -> str:
    """
    Get the extension of a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: Extension of the file (without the dot)
    """
    try:
        return os.path.splitext(file_path)[1][1:]
    except Exception as e:
        logger.exception(f"Error getting file extension for {file_path}: {str(e)}")
        return ""
