# AI-Powered Manim Video Generation API

A FastAPI-based service for generating mathematical animations using Manim, Gemini AI, and ElevenLabs.

## Features

- Generate educational video scripts with Gemini AI
- Convert script scenes into Manim animation code
- Generate narration audio with ElevenLabs Text-to-Speech
- Render animations with Manim
- Compose final videos with FFmpeg

## Prerequisites

- Python 3.9+
- Manim and its dependencies
- FFmpeg
- API keys for Gemini AI and ElevenLabs

## Installation

### Option 1: Using Docker (Recommended)

1. Clone this repository
2. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```
3. Add your API keys to the `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   ```
4. Build and run the Docker container:
   ```
   docker-compose up -d
   ```

### Option 2: Manual Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```
5. Add your API keys to the `.env` file
6. Run the application:
   ```
   python run.py
   ```

## API Endpoints

### Health Check

```
GET /health
```

Returns the health status of the API.

### Generate Video

```
POST /generate-video
```

Request body:
```json
{
  "prompt": "Explain the Pythagorean theorem with visual examples",
  "voice_id": "pNInz6obpgDQGcFmaJgB",
  "quality": "medium"
}
```

Parameters:
- `prompt` (string, required): Description of the video to generate
- `voice_id` (string, optional): ElevenLabs voice ID (default: "pNInz6obpgDQGcFmaJgB")
- `quality` (string, optional): Video quality (low, medium, high)

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Video generation job has been queued"
}
```

### Get Job Status

```
GET /job/{job_id}
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 0.6,
  "message": "Rendering animations...",
  "script": {
    "title": "Understanding the Pythagorean Theorem",
    "description": "An educational video explaining the Pythagorean theorem with visual examples",
    "scenes": [...]
  },
  "video_url": null,
  "error": null
}
```

When the job is completed, the response will include a `video_url` that can be used to access the generated video.

### Delete Job

```
DELETE /job/{job_id}
```

Deletes a job and its associated files.

## Integration with Frontend

To integrate this API with your frontend application:

1. Make a POST request to `/generate-video` with the video parameters
2. Poll the `/job/{job_id}` endpoint to track progress
3. When the job is completed, use the returned `video_url` to display the video

Example using JavaScript:

```javascript
async function generateVideo(prompt) {
  // Step 1: Submit the video generation request
  const response = await fetch('http://localhost:8000/generate-video', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt: prompt,
      quality: 'medium'
    }),
  });

  const data = await response.json();
  const jobId = data.job_id;

  // Step 2: Poll for job status
  const pollInterval = setInterval(async () => {
    const statusResponse = await fetch(`http://localhost:8000/job/${jobId}`);
    const statusData = await statusResponse.json();

    // Update UI with progress
    updateProgressUI(statusData.progress, statusData.message);

    if (statusData.status === 'completed') {
      clearInterval(pollInterval);
      // Display the video
      displayVideo(statusData.video_url, statusData.script);
    } else if (statusData.status === 'failed') {
      clearInterval(pollInterval);
      // Display error
      displayError(statusData.error);
    }
  }, 2000); // Poll every 2 seconds
}
```

## Deployment to Render.com

This project includes a `render.yaml` file for easy deployment to Render.com:

1. Create a Render.com account at https://render.com
2. Fork this repository to your GitHub account
3. In Render.com, go to the Dashboard and click "New" > "Blueprint"
4. Connect your GitHub account and select your forked repository
5. Render will detect the `render.yaml` file and set up the service
6. Add your API keys in the environment variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `ELEVENLABS_API_KEY`: Your ElevenLabs API key
7. Update the `ALLOWED_ORIGINS` to include your Intellect app's URL
8. Deploy the service

Once deployed, update the `MANIM_API_URL` in your Intellect app's `.env.local` file with the URL of your deployed Manim Video API.

## License

MIT
