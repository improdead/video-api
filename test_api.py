import requests
import json
import time
import os
import sys

# API endpoint
API_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    response = requests.get(f"{API_URL}/health")
    print(f"Health check status code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_generate_video():
    """Test the video generation endpoint"""
    payload = {
        "prompt": "Explain the Pythagorean theorem with visual examples",
        "quality": "low"  # Use low quality for faster testing
    }
    
    print(f"Sending request to generate video: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{API_URL}/generate-video", json=payload)
    print(f"Generate video status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        job_id = result.get("job_id")
        if job_id:
            print(f"Polling job status for job ID: {job_id}")
            
            # Poll for job status a few times
            for i in range(5):
                time.sleep(2)  # Wait 2 seconds between polls
                
                status_response = requests.get(f"{API_URL}/job/{job_id}")
                status = status_response.json()
                print(f"Job status ({i+1}/5): {json.dumps(status, indent=2)}")
                
                if status.get("status") in ["completed", "failed"]:
                    break
            
            # Test job deletion
            delete_response = requests.delete(f"{API_URL}/job/{job_id}")
            print(f"Job deletion status code: {delete_response.status_code}")
            print(f"Job deletion response: {delete_response.json()}")
    else:
        print(f"Error response: {response.text}")
        
    assert response.status_code == 200

if __name__ == "__main__":
    try:
        print("Testing API health...")
        test_health()
        print("\nTesting video generation...")
        test_generate_video()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"Test failed: {str(e)}")
        sys.exit(1)
