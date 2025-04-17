const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');
const pipeline = promisify(require('stream').pipeline);

/**
 * Client for interacting with the Manim Video Generation API
 */
class ManimVideoAPIClient {
  /**
   * Initialize the client
   * @param {string} baseUrl - The base URL of the Manim Video API
   */
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  }

  /**
   * Check if the API is healthy
   * @returns {Promise<Object>} The health status
   */
  async healthCheck() {
    const response = await axios.get(`${this.baseUrl}/health`);
    return response.data;
  }

  /**
   * Generate a video
   * @param {Object} options - Video generation options
   * @param {string} options.prompt - Description of the video to generate
   * @param {string} [options.voiceId] - Optional ElevenLabs voice ID
   * @param {string} [options.quality='medium'] - Video quality (low, medium, high)
   * @returns {Promise<Object>} Response containing job information
   */
  async generateVideo({
    prompt,
    voiceId = null,
    quality = 'medium'
  }) {
    const payload = {
      prompt,
      quality
    };

    if (voiceId) {
      payload.voice_id = voiceId;
    }

    const response = await axios.post(`${this.baseUrl}/generate-video`, payload);
    return response.data;
  }

  /**
   * Get the status of a job
   * @param {string} jobId - The ID of the job
   * @returns {Promise<Object>} The job status
   */
  async getJobStatus(jobId) {
    const response = await axios.get(`${this.baseUrl}/job/${jobId}`);
    return response.data;
  }

  /**
   * Delete a job
   * @param {string} jobId - The ID of the job
   * @returns {Promise<Object>} Response indicating success or failure
   */
  async deleteJob(jobId) {
    const response = await axios.delete(`${this.baseUrl}/job/${jobId}`);
    return response.data;
  }

  /**
   * Get the URL for a completed video
   * @param {string} jobId - The ID of the job
   * @returns {Promise<string|null>} The URL to the video, or null if not available
   */
  async getVideoUrl(jobId) {
    const status = await this.getJobStatus(jobId);
    return status.video_url;
  }

  /**
   * Wait for a job to complete
   * @param {string} jobId - The ID of the job
   * @param {Object} options - Options for waiting
   * @param {number} [options.timeoutSeconds=300] - Maximum time to wait in seconds
   * @param {number} [options.pollIntervalSeconds=5] - Time between status checks in seconds
   * @param {Function} [options.progressCallback] - Optional callback function that receives the job status
   * @returns {Promise<Object>} The final job status
   */
  async waitForJobCompletion(jobId, {
    timeoutSeconds = 300,
    pollIntervalSeconds = 5,
    progressCallback = null
  } = {}) {
    const startTime = Date.now();
    
    while ((Date.now() - startTime) / 1000 < timeoutSeconds) {
      const status = await this.getJobStatus(jobId);
      
      if (progressCallback) {
        progressCallback(status);
      }
      
      if (status.status === 'completed' || status.status === 'failed') {
        return status;
      }
      
      await new Promise(resolve => setTimeout(resolve, pollIntervalSeconds * 1000));
    }
    
    throw new Error(`Job ${jobId} did not complete within ${timeoutSeconds} seconds`);
  }

  /**
   * Download a video to a local file
   * @param {string} jobId - The ID of the job
   * @param {string} outputPath - The path where the video should be saved
   * @returns {Promise<string>} The path to the downloaded video
   */
  async downloadVideo(jobId, outputPath) {
    const videoUrl = await this.getVideoUrl(jobId);
    
    if (!videoUrl) {
      throw new Error('Video URL not available');
    }
    
    const url = `${this.baseUrl}${videoUrl}`;
    const response = await axios({
      method: 'get',
      url,
      responseType: 'stream'
    });

    await pipeline(response.data, fs.createWriteStream(outputPath));
    return outputPath;
  }
}

/**
 * Example usage of the Manim Video API client
 */
async function main() {
  const client = new ManimVideoAPIClient();

  try {
    // Check if the API is healthy
    const health = await client.healthCheck();
    console.log('API health:', health);

    // Generate a video
    const result = await client.generateVideo({
      prompt: 'Explain the Pythagorean theorem with visual examples',
      quality: 'medium'
    });
    console.log('Video generation initiated:', result);

    // Get the job ID
    const jobId = result.job_id;

    // Define a progress callback
    const showProgress = (status) => {
      const progress = (status.progress || 0) * 100;
      const message = status.message || '';
      console.log(`Progress: ${progress.toFixed(1)}% - ${message}`);
    };

    // Wait for the job to complete
    console.log('Waiting for job to complete...');
    const finalStatus = await client.waitForJobCompletion(jobId, {
      timeoutSeconds: 300,
      pollIntervalSeconds: 5,
      progressCallback: showProgress
    });

    console.log('Final status:', finalStatus);

    // Get the video URL
    const videoUrl = await client.getVideoUrl(jobId);
    if (videoUrl) {
      console.log('Video URL:', `${client.baseUrl}${videoUrl}`);
      
      // Download the video
      const outputPath = path.join(__dirname, `${jobId}.mp4`);
      await client.downloadVideo(jobId, outputPath);
      console.log('Video downloaded to:', outputPath);
    }

  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Run the example
main().catch(console.error);
