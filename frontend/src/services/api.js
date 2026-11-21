import axios from 'axios';

export const BACKEND_URL = (import.meta.env.VITE_BACKEND_URL || '').replace(/\/$/, '');
const API_BASE = BACKEND_URL ? `${BACKEND_URL}/api` : '/api';

export const resolveMediaUrl = (path) => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return BACKEND_URL ? `${BACKEND_URL}${path}` : path;
};

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

export const getZipDownloadUrl = (jobId) => `${BACKEND_URL}/api/jobs/${jobId}/download`;
export const getClipDownloadUrl = (clipId) => `${BACKEND_URL}/api/clips/${clipId}/download`;
export const getSubtitleDownloadUrl = (clipId, format = 'srt') => `${BACKEND_URL}/api/clips/${clipId}/subtitles?format=${format}`;

export default api;
