import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * Custom hook for interacting with the Manim Video API
 */
const useManimVideoAPI = (baseUrl = 'http://localhost:8000') => {
  const apiUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;

  /**
   * Generate a video
   */
  const generateVideo = async ({
    prompt,
    voiceId = null,
    quality = 'medium'
  }) => {
    const payload = {
      prompt,
      quality
    };

    if (voiceId) {
      payload.voice_id = voiceId;
    }

    const response = await axios.post(`${apiUrl}/generate-video`, payload);
    return response.data;
  };

  /**
   * Get the status of a job
   */
  const getJobStatus = async (jobId) => {
    const response = await axios.get(`${apiUrl}/job/${jobId}`);
    return response.data;
  };

  /**
   * Delete a job
   */
  const deleteJob = async (jobId) => {
    const response = await axios.delete(`${apiUrl}/job/${jobId}`);
    return response.data;
  };

  return {
    generateVideo,
    getJobStatus,
    deleteJob,
    apiUrl
  };
};

/**
 * Video Generator Component
 */
const VideoGenerator = () => {
  const [prompt, setPrompt] = useState('');
  const [quality, setQuality] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [pollInterval, setPollInterval] = useState(null);

  const { generateVideo, getJobStatus, deleteJob, apiUrl } = useManimVideoAPI();

  // Clean up polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [pollInterval]);

  // Start polling for job status when jobId changes
  useEffect(() => {
    if (jobId) {
      const interval = setInterval(async () => {
        try {
          const status = await getJobStatus(jobId);
          setJobStatus(status);
          
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(interval);
          }
        } catch (err) {
          console.error('Error polling job status:', err);
          clearInterval(interval);
          setError('Error polling job status');
        }
      }, 2000); // Poll every 2 seconds
      
      setPollInterval(interval);
      
      return () => clearInterval(interval);
    }
  }, [jobId, getJobStatus]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setJobStatus(null);
    
    try {
      const data = await generateVideo({
        prompt,
        quality
      });
      
      setJobId(data.job_id);
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred');
      console.error('Error generating video:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!jobId) return;
    
    try {
      await deleteJob(jobId);
      setJobId(null);
      setJobStatus(null);
    } catch (err) {
      console.error('Error deleting job:', err);
    }
  };

  return (
    <div className="video-generator">
      <h2>AI Math Animation Generator</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="prompt">What would you like to create a video about?</label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="E.g., Explain the Pythagorean theorem with visual examples"
            rows={4}
            disabled={loading || jobStatus?.status === 'processing'}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="quality">Quality:</label>
          <select
            id="quality"
            value={quality}
            onChange={(e) => setQuality(e.target.value)}
            disabled={loading || jobStatus?.status === 'processing'}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
        
        <button 
          type="submit" 
          disabled={loading || jobStatus?.status === 'processing'}
        >
          {loading ? 'Submitting...' : 'Generate Video'}
        </button>
      </form>
      
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}
      
      {jobStatus && (
        <div className="job-status">
          <h3>Job Status</h3>
          
          {jobStatus.status === 'processing' && (
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${(jobStatus.progress || 0) * 100}%` }}
                />
              </div>
              <p>{jobStatus.message || 'Processing...'}</p>
            </div>
          )}
          
          {jobStatus.status === 'completed' && jobStatus.video_url && (
            <div className="video-result">
              <h3>Your Video is Ready!</h3>
              
              <div className="video-player">
                <video 
                  controls 
                  src={`${apiUrl}${jobStatus.video_url}`} 
                  width="100%" 
                />
              </div>
              
              <div className="video-actions">
                <a 
                  href={`${apiUrl}${jobStatus.video_url}`} 
                  download
                  className="download-button"
                >
                  Download Video
                </a>
                
                <button 
                  onClick={handleDelete}
                  className="delete-button"
                >
                  Delete Video
                </button>
              </div>
              
              {jobStatus.script && (
                <div className="video-script">
                  <h3>Generated Script</h3>
                  <div className="script-content">
                    <h4>{jobStatus.script.title}</h4>
                    <p>{jobStatus.script.description}</p>
                    
                    <div className="scenes">
                      {jobStatus.script.scenes.map((scene, index) => (
                        <div key={index} className="scene">
                          <div className="scene-header">
                            <span className="scene-time">{scene.startTime} - {scene.endTime}</span>
                            <span className="scene-number">Scene {index + 1}</span>
                          </div>
                          <p className="scene-narration">{scene.narration}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {jobStatus.status === 'failed' && (
            <div className="error-message">
              <p>Video generation failed: {jobStatus.error || 'Unknown error'}</p>
              <button onClick={handleDelete}>Clear</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VideoGenerator;
