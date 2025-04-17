import requests
import json
import time
from typing import Dict, Any, Optional, List, Union

class ManimVideoAPIClient:
    """
    Client for interacting with the Manim Video Generation API
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client
        
        Args:
            base_url: The base URL of the Manim Video API
        """
        self.base_url = base_url.rstrip("/")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the API is healthy
        
        Returns:
            Dict[str, Any]: The health status
        """
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def generate_video(
        self,
        prompt: str,
        voice_id: Optional[str] = None,
        quality: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate a video
        
        Args:
            prompt: Description of the video to generate
            voice_id: Optional ElevenLabs voice ID
            quality: Video quality (low, medium, high)
            
        Returns:
            Dict[str, Any]: Response containing job information
        """
        payload = {
            "prompt": prompt,
            "quality": quality
        }
        
        if voice_id:
            payload["voice_id"] = voice_id
        
        response = requests.post(f"{self.base_url}/generate-video", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a job
        
        Args:
            job_id: The ID of the job
            
        Returns:
            Dict[str, Any]: The job status
        """
        response = requests.get(f"{self.base_url}/job/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def delete_job(self, job_id: str) -> Dict[str, Any]:
        """
        Delete a job
        
        Args:
            job_id: The ID of the job
            
        Returns:
            Dict[str, Any]: Response indicating success or failure
        """
        response = requests.delete(f"{self.base_url}/job/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def get_video_url(self, job_id: str) -> Optional[str]:
        """
        Get the URL for a completed video
        
        Args:
            job_id: The ID of the job
            
        Returns:
            Optional[str]: The URL to the video, or None if not available
        """
        status = self.get_job_status(job_id)
        return status.get("video_url")
    
    def wait_for_job_completion(
        self, 
        job_id: str, 
        timeout_seconds: int = 300,
        poll_interval_seconds: int = 5,
        progress_callback = None
    ) -> Dict[str, Any]:
        """
        Wait for a job to complete
        
        Args:
            job_id: The ID of the job
            timeout_seconds: Maximum time to wait in seconds
            poll_interval_seconds: Time between status checks in seconds
            progress_callback: Optional callback function that receives the job status
            
        Returns:
            Dict[str, Any]: The final job status
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            status = self.get_job_status(job_id)
            
            if progress_callback:
                progress_callback(status)
            
            if status["status"] in ["completed", "failed"]:
                return status
            
            time.sleep(poll_interval_seconds)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout_seconds} seconds")

# Example usage
if __name__ == "__main__":
    client = ManimVideoAPIClient()
    
    try:
        # Check if the API is healthy
        health = client.health_check()
        print(f"API health: {health}")
        
        # Generate a video
        result = client.generate_video(
            prompt="Explain the Pythagorean theorem with visual examples",
            quality="medium"
        )
        print(f"Video generation initiated: {json.dumps(result, indent=2)}")
        
        # Get the job ID
        job_id = result["job_id"]
        
        # Define a progress callback
        def show_progress(status):
            progress = status.get("progress", 0) * 100
            message = status.get("message", "")
            print(f"Progress: {progress:.1f}% - {message}")
        
        # Wait for the job to complete
        final_status = client.wait_for_job_completion(
            job_id,
            timeout_seconds=300,
            poll_interval_seconds=5,
            progress_callback=show_progress
        )
        
        print(f"Final status: {json.dumps(final_status, indent=2)}")
        
        # Get the video URL
        video_url = client.get_video_url(job_id)
        if video_url:
            print(f"Video URL: {client.base_url}{video_url}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
