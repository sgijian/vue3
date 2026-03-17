<template>
  <el-upload
    class="resume-uploader"
    action=""
    :auto-upload="false"
    :file-list="fileList"
    :limit="maxCount"
    :on-change="handleChange"
    :on-remove="handleRemove"
    :before-upload="beforeUpload"
    multiple
    drag
    accept=".docx"
    list-type="text"
  >
    <el-button type="primary">拖拽或点击上传（最多20份，仅.docx）</el-button>
  </el-upload>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
const props = defineProps<{ maxCount: number }>();
const emit = defineEmits(['update:modelValue']);
const fileList = ref<any[]>([]);

watch(fileList, () => {
  emit('update:modelValue', fileList.value.map(f => f.raw));
});

function handleChange(file: any, fileList_: any[]) {
  fileList.value = fileList_;
}
function handleRemove(file: any, fileList_: any[]) {
  fileList.value = fileList_;
}
function beforeUpload(file: File) {
  const isDocx = file.name.endsWith('.docx');
  if (!isDocx) {
    ElMessage.error('仅支持 .docx 格式');
  }
  return isDocx;
}
</script>

<style scoped>
.resume-uploader {
  width: 100%;
}
</style>
