<template>
  <el-card class="task-create">
    <el-form :model="form" ref="formRef" label-width="120px">
      <el-form-item label="岗位需求">
        <el-input v-model="form.job_description" type="textarea" :rows="4" placeholder="请输入岗位需求" />
        <el-button type="text" @click="fillTemplate">使用评分标准模板</el-button>
      </el-form-item>
      <el-form-item label="评分标准">
        <el-collapse v-model="showCriteria">
          <el-collapse-item title="评分标准说明" name="criteria">
            <div v-if="criteria">
              <pre>{{ criteria }}</pre>
            </div>
            <div v-else>加载中...</div>
          </el-collapse-item>
        </el-collapse>
      </el-form-item>
      <el-form-item label="简历上传">
        <ResumeUploader v-model="files" :max-count="20" accept=".doc,.docx" />
        <div class="upload-tip">支持 .doc 和 .docx 格式，最多 20 份</div>
      </el-form-item>
      <!-- 进度条展示 -->
      <el-alert v-if="isPolling" title="任务处理中" type="info" :closable="false" show-icon class="progress-alert">
        <template #default>
          <div class="progress-content">
            <span>当前阶段：{{ currentStage }}</span>
            <el-progress :percentage="progressPercentage"
              :status="currentStage === 'completed' ? 'success' : undefined" />
            <span class="detail-text">{{ progressDetail }}</span>
          </div>
        </template>
      </el-alert>

      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :loading="loading || isPolling" :disabled="isPolling">
          {{ isPolling ? '处理中...' : '提交任务' }}
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { getTemplates, createTask, uploadResumes, getTaskStatus } from '@/api';
import ResumeUploader from '@/components/ResumeUploader.vue';
import { useRouter } from 'vue-router';

const form = ref({
  job_description: '',
  evaluation_criteria: ''
});
const criteria = ref('');
const showCriteria = ref(['criteria']);
const files = ref<File[]>([]);
const loading = ref(false);
const isPolling = ref(false); // 新增：轮询状态
const router = useRouter();

// 新增：轮询相关状态
const pollTimer = ref<number | null>(null);
const currentStage = ref('初始化');
const progressPercentage = ref(0);
const progressDetail = ref('准备提交...');
// 新增：轮询计数器和最大尝试次数
const pollCount = ref(0);
// 修改：增加最大轮询次数至 60 次 (约 3 分钟)，防止正常网络波动导致过早停止
const MAX_POLL_COUNT = 60;

onMounted(async () => {
  const res = await getTemplates();
  // 修改: 从 res.data 中获取实际业务数据
  if (res.data) {
    form.value.evaluation_criteria = res.data.evaluation_criteria;
    criteria.value = res.data.evaluation_criteria;
  }
});

function fillTemplate() {
  form.value.job_description = form.value.job_description || (criteria.value ? criteria.value : '');
}

async function handleSubmit() {
  if (!form.value.job_description) {
    ElMessage.error('请填写岗位需求');
    return;
  }

  loading.value = true;
  isPolling.value = false;
  stopPolling(); // 清除旧的轮询

  try {
    console.log('🚀 开始提交任务...');

    // 1. 创建任务
    const taskRes = await createTask(form.value);
    console.log('✅ 任务创建响应:', taskRes);

    // 修改: 从 taskRes.data 中获取实际业务数据
    const responseData = taskRes.data;
    // 兼容不同的后端返回字段名，优先使用 task_id，同时也支持 id
    const taskId = responseData?.task_id || responseData?.id;

    if (!taskId || typeof taskId !== 'string') {
      console.error('❌ 无效的任务 ID:', taskId);
      throw new Error('任务创建失败：未获取到有效的任务 ID');
    }
    console.log('🆔 提取到的 Task ID:', taskId);

    // 2. 上传文件 (如果有)
    if (files.value.length > 0) {
      console.log('📤 开始上传简历文件，数量:', files.value.length);
      await uploadResumes(taskId, files.value);
      console.log('✅ 文件上传成功');
      updateProgress('uploading', 25);
    } else {
      console.log('⚠️ 无文件需要上传，跳过上传步骤');
      updateProgress('extracting', 25);
    }

    ElMessage.success('任务已提交，正在后台处理...');

    // 3. 开始轮询任务状态
    startPolling(taskId);

  } catch (e: any) {
    console.error('💥 提交过程整体错误:', e);
    const errorMsg = e instanceof Error ? e.message : String(e);
    ElMessage.error(errorMsg || '提交失败');
    loading.value = false;
    isPolling.value = false;
  }
}

// 新增：更新进度显示
function updateProgress(stage: string, percent: number) {
  currentStage.value = getStageText(stage);
  progressPercentage.value = percent;
  progressDetail.value = `正在${getStageText(stage)}...`;
}

function getStageText(stage: string): string {
  const map: Record<string, string> = {
    uploading: '上传简历',
    extracting: '提取信息',
    evaluating: 'AI 评估',
    ranking: '生成排名',
    completed: '处理完成'
  };
  return map[stage] || stage;
}

// 新增：启动轮询
function startPolling(taskId: string) {
  loading.value = false; // 提交按钮 Loading 结束，转为进度条
  isPolling.value = true;
  pollCount.value = 0; // 重置计数器
  updateProgress('extracting', 30);

  const poll = async () => {
    // 检查是否超过最大轮询次数
    if (pollCount.value >= MAX_POLL_COUNT) {
      stopPolling();
      ElMessage.warning('处理时间较长，已自动停止轮询。正在跳转至结果页查看最新状态（数据可能尚未生成）。');
      isPolling.value = false;
      
      // 优化：达到最大次数后自动跳转
      setTimeout(() => {
        router.push(`/result/${taskId}`);
      }, 800);
      return;
    }
    
    pollCount.value++;

    try {
      const statusRes = await getTaskStatus(taskId);
      // 修改：从 statusRes.data 中获取实际业务数据
      const { status, progress } = statusRes.data;

      console.log('🔄 轮询状态:', status, progress, `次数:${pollCount.value}/${MAX_POLL_COUNT}`);

      if (progress) {
        const { stage, percentage, current, total } = progress;
        currentStage.value = getStageText(stage);
        progressPercentage.value = percentage || Math.round((current / total) * 100);
        progressDetail.value = `进度：${current}/${total}`;
      }

      // 修改：确保 status 是字符串比较
      if (status === 'completed') {
        stopPolling();
        ElMessage.success('分析完成！正在跳转结果页...');
        setTimeout(() => {
          router.push(`/result/${taskId}`);
        }, 800);
      } else if (status === 'failed') {
        stopPolling();
        ElMessage.error('任务处理失败，请稍后重试');
        isPolling.value = false;
      } else {
        // 继续轮询
        pollTimer.value = window.setTimeout(poll, 3000);
      }
    } catch (err) {
      console.error('轮询失败:', err);
      pollTimer.value = window.setTimeout(poll, 3000);
    }
  };

  poll();
}

// 新增：停止轮询
function stopPolling() {
  if (pollTimer.value) {
    clearTimeout(pollTimer.value);
    pollTimer.value = null;
  }
}

onUnmounted(() => {
  stopPolling();
});

</script>

<style scoped>
.task-create {
  max-width: 700px;
  margin: 40px auto;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.progress-alert {
  margin-bottom: 20px;
}

.progress-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-text {
  font-size: 12px;
  color: #606266;
  text-align: right;
}
</style>
