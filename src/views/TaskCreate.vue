<template>
  <el-card class="task-create">
    <el-form :model="form" ref="formRef" label-width="120px">
      <el-form-item label="岗位需求">
        <el-input
          v-model="form.job_description"
          type="textarea"
          rows="4"
          placeholder="请输入岗位需求"
        />
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
        <ResumeUploader
          v-model="files"
          :max-count="20"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :loading="loading">提交任务</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { getTemplates, createTask, uploadResumes } from '@/api';
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
const router = useRouter();

onMounted(async () => {
  const res = await getTemplates();
  if (res) {
    form.value.evaluation_criteria = res.evaluation_criteria;
    criteria.value = res.evaluation_criteria;
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
  try {
    const taskRes = await createTask(form.value);
    if (taskRes && taskRes.id) {
      if (files.value.length > 0) {
        await uploadResumes(taskRes.id, files.value);
      }
      ElMessage.success('任务创建成功');
      router.push(`/result/${taskRes.id}`);
    } else {
      throw new Error('任务创建失败');
    }
  } catch (e: any) {
    ElMessage.error(e.message || '提交失败');
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.task-create {
  max-width: 700px;
  margin: 40px auto;
}
</style>
