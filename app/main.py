from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
import shutil
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import asyncio
from datetime import datetime

# Import services
from services.script_generator.gemini_script import generate_script
from services.code_generator.manim_code_generator import generate_manim_code
from services.tts.elevenlabs_tts import generate_speech
from services.renderer.manim_renderer import render_scene
from services.composer.video_composer import combine_audio_video, concat_videos

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="Manim Video Generation API",
    description="API for generating mathematical animations using Manim, Gemini AI, and ElevenLabs",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for storing generated content
JOBS_DIR = Path("./jobs")
JOBS_DIR.mkdir(exist_ok=True)

# Mount the jobs directory for static file access
app.mount("/jobs", StaticFiles(directory=str(JOBS_DIR)), name="jobs")

class VideoRequest(BaseModel):
    """Request model for video generation"""
    prompt: str
    voice_id: Optional[str] = "pNInz6obpgDQGcFmaJgB"  # Default ElevenLabs voice ID
    quality: str = "medium"  # low, medium, high

class JobStatus(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str
    progress: float
    message: str
    video_url: Optional[str] = None
    script: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Manim Video Generation API"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Dictionary to store job status
job_statuses = {}

async def generate_video_task(job_id: str, request: VideoRequest):
    """
    Background task to generate a video
    
    Args:
        job_id: The unique job ID
        request: The video generation request
    """
    job_dir = JOBS_DIR / job_id
    script_dir = job_dir / "script"
    audio_dir = job_dir / "audio"
    video_dir = job_dir / "video"
    output_dir = job_dir / "output"
    
    # Create directories
    for dir_path in [script_dir, audio_dir, video_dir, output_dir]:
        dir_path.mkdir(exist_ok=True)
    
    try:
        # Update job status
        job_statuses[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "progress": 0.05,
            "message": "Generating script...",
            "script": None,
            "video_url": None,
            "error": None
        }
        
        # 1. Generate script
        script = await generate_script(request.prompt)
        script_path = script_dir / "script.json"
        with open(script_path, "w") as f:
            json.dump(script, f, indent=2)
        
        # Update job status
        job_statuses[job_id]["progress"] = 0.2
        job_statuses[job_id]["message"] = "Generating Manim code..."
        job_statuses[job_id]["script"] = script
        
        # 2. Generate Manim code for each scene
        scene_codes = []
        for i, scene in enumerate(script["scenes"]):
            code = await generate_manim_code(scene, i)
            code_path = script_dir / f"scene_{i+1}.py"
            with open(code_path, "w") as f:
                f.write(code)
            scene_codes.append(code)
        
        # Update job status
        job_statuses[job_id]["progress"] = 0.4
        job_statuses[job_id]["message"] = "Generating audio..."
        
        # 3. Generate audio for each scene
        audio_paths = []
        for i, scene in enumerate(script["scenes"]):
            audio_path = audio_dir / f"scene_{i+1}.mp3"
            await generate_speech(scene["narration"], str(audio_path), request.voice_id)
            audio_paths.append(audio_path)
        
        # Update job status
        job_statuses[job_id]["progress"] = 0.6
        job_statuses[job_id]["message"] = "Rendering animations..."
        
        # 4. Render video for each scene
        video_paths = []
        for i, code in enumerate(scene_codes):
            video_path = video_dir / f"scene_{i+1}.mp4"
            await render_scene(code, str(video_path), request.quality)
            video_paths.append(video_path)
        
        # Update job status
        job_statuses[job_id]["progress"] = 0.8
        job_statuses[job_id]["message"] = "Composing final video..."
        
        # 5. Combine audio and video for each scene
        combined_paths = []
        for i in range(len(script["scenes"])):
            combined_path = output_dir / f"combined_scene_{i+1}.mp4"
            await combine_audio_video(
                str(video_paths[i]), 
                str(audio_paths[i]), 
                str(combined_path)
            )
            combined_paths.append(combined_path)
        
        # 6. Concatenate all scenes
        final_path = output_dir / "final_video.mp4"
        await concat_videos([str(p) for p in combined_paths], str(final_path))
        
        # Update job status
        job_statuses[job_id]["status"] = "completed"
        job_statuses[job_id]["progress"] = 1.0
        job_statuses[job_id]["message"] = "Video generation completed"
        job_statuses[job_id]["video_url"] = f"/jobs/{job_id}/output/final_video.mp4"
        
    except Exception as e:
        logger.exception(f"Error generating video: {str(e)}")
        job_statuses[job_id]["status"] = "failed"
        job_statuses[job_id]["message"] = "Video generation failed"
        job_statuses[job_id]["error"] = str(e)

@app.post("/generate-video")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """
    Generate a video based on the provided prompt
    
    Args:
        request: The video generation request
        background_tasks: FastAPI background tasks
        
    Returns:
        dict: Response containing job ID and initial status
    """
    job_id = str(uuid.uuid4())
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    
    # Initialize job status
    job_statuses[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "message": "Job queued",
        "script": None,
        "video_url": None,
        "error": None
    }
    
    # Start the video generation task in the background
    background_tasks.add_task(generate_video_task, job_id, request)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Video generation job has been queued"
    }

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a video generation job
    
    Args:
        job_id: The unique job ID
        
    Returns:
        JobStatus: The current status of the job
    """
    if job_id not in job_statuses:
        raise HTTPException(
            status_code=404,
            detail=f"Job with ID {job_id} not found"
        )
    
    return job_statuses[job_id]

@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job and its associated files
    
    Args:
        job_id: The unique job ID
        
    Returns:
        dict: Response indicating success or failure
    """
    if job_id not in job_statuses:
        raise HTTPException(
            status_code=404,
            detail=f"Job with ID {job_id} not found"
        )
    
    job_dir = JOBS_DIR / job_id
    
    if job_dir.exists():
        try:
            shutil.rmtree(job_dir)
            del job_statuses[job_id]
            return {"message": f"Job {job_id} deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting job: {str(e)}"
            )
    else:
        del job_statuses[job_id]
        return {"message": f"Job {job_id} deleted (files not found)"}
