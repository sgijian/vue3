<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import { Document, InfoFilled, UploadFilled } from '@element-plus/icons-vue'
import type { UploadUserFile, UploadProps } from 'element-plus'

const router = useRouter()

// 状态定义
const jobDescription = ref('')
const evaluationCriteria = ref('')
const showCriteria = ref(false)
const fileList = ref<UploadUserFile[]>([])
const loading = ref(false)
const taskId = ref<string | null>(null)
const uploadRef = ref()

const triggerUpload = () => {
  // 兼容 Element Plus 3.x/2.x
  const input = uploadRef.value?.$el?.querySelector?.('input[type=file]') || uploadRef.value?.$refs?.input || uploadRef.value?.$el?.querySelector?.('input');
  input && input.click();
}

// 获取默认模板
const fetchTemplate = async () => {
  try {
    const res = await axios.get('/api/templates')
    jobDescription.value = res.data.job_description || ''
    evaluationCriteria.value = res.data.evaluation_criteria || ''
    ElMessage.success('模板加载成功')
  } catch (error) {
    ElMessage.error('获取模板失败')
  }
}

// 文件上传校验
const beforeUpload: UploadProps['beforeUpload'] = (rawFile) => {
  if (!rawFile.name.endsWith('.docx')) {
    ElMessage.error('只能上传 .docx 格式的简历文件!')
    return false
  }
  if (fileList.value.length >= 20) {
    ElMessage.warning('最多只能上传 20 份简历')
    return false
  }
  return true
}

// 提交任务
const submitTask = async () => {
  if (!jobDescription.value.trim()) {
    ElMessage.warning('请输入岗位需求')
    return
  }
  if (fileList.value.length === 0) {
    ElMessage.warning('请至少上传一份简历')
    return
  }

  const loadingInstance = ElLoading.service({ lock: true, text: '正在创建任务并上传简历...' })
  
  try {
    // 1. 创建任务 (对应 API 1.2)
    const taskRes = await axios.post('/api/tasks', {
      job_description: jobDescription.value,
      evaluation_criteria: evaluationCriteria.value || undefined
    })
    
    // 兼容不同的后端返回字段名
    const currentTaskId = taskRes.data.id || taskRes.data.task_id
    if (!currentTaskId) {
      throw new Error('后端未返回有效的任务 ID')
    }

    // 2. 上传文件 (对应 API 1.3)
    const formData = new FormData()
    fileList.value.forEach((file) => {
      if (file.raw) {
        formData.append('files', file.raw)
      }
    })

    await axios.post(`/api/tasks/${currentTaskId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    ElMessage.success('任务创建成功！正在跳转至结果页...')
    
    // 使用路由跳转至结果页 (对应 API 2.1, 2.2, 3.1, 3.2 的展示页)
    router.push(`/result/${currentTaskId}`)
    
  } catch (error: any) {
    const errorMsg = error.response?.data?.message || error.message || '任务创建或文件上传失败'
    ElMessage.error(errorMsg)
    console.error('API Error:', error)
  } finally {
    loadingInstance.close()
  }
}
</script>

<template>
  <div class="app-container">
    <header class="page-header">
      <h1>AI 简历筛选系统</h1>
      <p class="subtitle">智能分析简历画像 · 自动生成排名 · 数据可视化 Dashboard</p>
    </header>

    <main class="content-wrapper">
      <el-card class="task-card">
        <template #header>
          <div class="card-header">
            <span>创建新任务</span>
            <el-button type="primary" link @click="fetchTemplate">
              <el-icon><Document /></el-icon> 获取默认模板
            </el-button>
          </div>
        </template>

        <!-- 岗位需求输入 -->
        <el-form label-position="top">
          <el-form-item label="岗位需求 (Job Description)" required>
            <el-input
              v-model="jobDescription"
              type="textarea"
              :rows="5"
              placeholder="请输入岗位职责、任职要求等信息..."
            />
          </el-form-item>

          <!-- 评分标准 (可展开) -->
          <el-form-item label="评分标准 (Evaluation Criteria)">
            <el-button type="info" text @click="showCriteria = !showCriteria">
              {{ showCriteria ? '收起' : '展开' }}评分标准说明
            </el-button>
            <el-collapse-transition>
              <div v-show="showCriteria" class="criteria-box">
                <el-input
                  v-model="evaluationCriteria"
                  type="textarea"
                  :rows="4"
                  placeholder="可选：输入具体的评分维度，如技能匹配度、学历权重等..."
                />
                <div class="tips">
                  <el-icon><InfoFilled /></el-icon> 
                  留空将使用系统默认评分算法。
                </div>
              </div>
            </el-collapse-transition>
          </el-form-item>

          <!-- 文件上传 -->
          <el-form-item label="上传简历 (.docx)" required>
            <div class="upload-row">
              <el-upload
                ref="uploadRef"
                drag
                action="#"
                :auto-upload="false"
                :on-change="(file: UploadUserFile) => fileList.push(file)"
                :on-remove="(file: UploadUserFile) => fileList = fileList.filter(f => f.uid !== file.uid)"
                :before-upload="beforeUpload"
                multiple
                :limit="20"
                accept=".docx"
                v-model:file-list="fileList"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">
                  拖拽文件到此处或 <em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    仅支持 .docx 格式，最多 20 份文件
                  </div>
                </template>
              </el-upload>
              <el-button class="upload-btn" type="primary" @click="triggerUpload">选择文件</el-button>
            </div>
            <div v-if="fileList.length > 0" class="file-count">
              已选择 {{ fileList.length }} 份简历
            </div>
          </el-form-item>

          <!-- 提交按钮 -->
          <div class="action-bar">
            <el-button type="primary" size="large" @click="submitTask" :loading="loading">
              开始筛选分析
            </el-button>
          </div>
        </el-form>
      </el-card>
    </main>
  </div>
</template>

<style scoped>
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
}

.page-header h1 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  font-size: 1.1rem;
}

.content-wrapper {
  display: flex;
  justify-content: center;
}

.task-card {
  width: 100%;
  max-width: 800px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 1.2rem;
}

.criteria-box {
  margin-top: 1rem;
  background-color: #f9fafc;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.tips {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}


.upload-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}
.upload-btn {
  height: 40px;
  margin-top: 8px;
}
.file-count {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #67c23a;
  font-weight: 500;
}

.action-bar {
  margin-top: 2rem;
  text-align: center;
}

/* 覆盖部分 Element Plus 默认样式以适配布局 */
:deep(.el-upload-dragger) {
  padding: 2rem 0;
  border-color: #dcdfe6;
  transition: border-color 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
}

:deep(.el-icon--upload) {
  font-size: 48px;
  color: #909399;
  margin-bottom: 16px;
}
</style>