import axios from 'axios';

export async function getTemplates() {
  const res = await axios.get('/api/templates');
  return res.data;
}

export async function createTask(data: { job_description: string; evaluation_criteria?: string }) {
  const res = await axios.post('/api/tasks', data);
  return res.data;
}

export async function uploadResumes(taskId: string, files: File[]) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  const res = await axios.post(`/api/tasks/${taskId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
}

export async function getResult(taskId: string) {
  const res = await axios.get(`/api/tasks/${taskId}/result`);
  return res.data;
}

export async function getDashboard(taskId: string) {
  const res = await axios.get(`/api/tasks/${taskId}/dashboard`);
  return res.data;
}
