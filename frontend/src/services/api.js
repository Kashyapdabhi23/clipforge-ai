import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const getStats = async () => {
  const res = await api.get('/stats');
  return res.data;
};

export const uploadVideoFile = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const res = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });
  return res.data;
};

export const uploadVideoUrl = async (url, rapidapiKey = null) => {
  const res = await api.post('/upload/url', { url, rapidapi_key: rapidapiKey });
  return res.data;
};

export const createClippingJob = async (jobData) => {
  const res = await api.post('/jobs', jobData);
  return res.data;
};

export const listJobs = async () => {
  const res = await api.get('/jobs');
  return res.data;
};

export const getJobDetails = async (jobId) => {
  const res = await api.get(`/jobs/${jobId}`);
  return res.data;
};

export const listProjects = async () => {
  const res = await api.get('/projects');
  return res.data;
};

export const getProjectDetails = async (projectId) => {
  const res = await api.get(`/projects/${projectId}`);
  return res.data;
};

export const deleteProject = async (projectId) => {
  const res = await api.delete(`/projects/${projectId}`);
  return res.data;
};

export const listClips = async () => {
  const res = await api.get('/clips');
  return res.data;
};

export const getClipDetails = async (clipId) => {
  const res = await api.get(`/clips/${clipId}`);
  return res.data;
};

export const deleteClip = async (clipId) => {
  const res = await api.delete(`/clips/${clipId}`);
  return res.data;
};

export const getZipDownloadUrl = (jobId) => `/api/jobs/${jobId}/download`;
export const getClipDownloadUrl = (clipId) => `/api/clips/${clipId}/download`;
export const getSubtitleDownloadUrl = (clipId, format = 'srt') => `/api/clips/${clipId}/subtitles?format=${format}`;

export default api;
