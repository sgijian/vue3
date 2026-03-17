import axios from 'axios';

const request = axios.create({
  baseURL: '/api',
  timeout: 5000,
});

export interface TaskCreateData {
  job_description: string;
  evaluation_criteria: string;
}

export interface TaskResponse {
  task_id: string;
  id?: string; // 新增: 兼容后端可能返回的 id 字段
}

export interface UploadResponse {
  message: string;
  count: number;
}

export interface TaskStatusResponse {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: {
    total: number;
    current: number;
    stage: string;
    percentage: number;
  };
  created_at?: number | string;
}

export interface TemplateResponse {
  job_description: string;
  evaluation_criteria: string;
}

export interface ResultResponse {
  task_id: string;
  status: string;
  total_candidates?: number;
  top_3?: any[];
  all_candidates?: any[];
  score_distribution?: any;
  created_at?: string;
  completed_at?: string;
}

export interface DashboardResponse {
  task_id: string;
  status: string;
  score_distribution?: any;
  skill_radar?: any[];
  level_pie?: Record<string, number>;
}

// 获取模板
export const getTemplates = () => {
  return request.get<TemplateResponse>('/templates');
};

// 创建任务
export const createTask = (data: TaskCreateData) => {
  return request.post<TaskResponse>('/tasks', data);
};

// 上传简历
export const uploadResumes = (taskId: string, files: File[]) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });
  return request.post<UploadResponse>(`/tasks/${taskId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// 新增：获取任务状态（用于轮询）
export const getTaskStatus = (taskId: string) => {
  return request.get<TaskStatusResponse>(`/tasks/${taskId}`);
};

// 获取结果详情
export const getResult = (taskId: string) => {
  return request.get<ResultResponse>(`/tasks/${taskId}/result`);
};

// 获取仪表盘数据
export const getDashboard = (taskId: string) => {
  return request.get<DashboardResponse>(`/tasks/${taskId}/dashboard`);
};
