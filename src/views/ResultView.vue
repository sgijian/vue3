<template>
  <el-card class="result-view">
    <template #header>
      <div class="result-header">
        <span>筛选结果 (Task: {{ taskId }})</span>
      </div>
    </template>
    
    <!-- 修改：移除 el-loading 组件，使用原生 CSS 实现加载状态，避免组件未注册警告 -->
    <div v-if="loading" class="loading-box">
      <div class="spinner"></div>
      <div class="loading-text">加载分析结果...</div>
    </div>
    
    <!-- 修改：当无候选人数据时（包括加载失败、任务未完成、真正为空），统一显示空状态 -->
    <div v-else-if="allCandidates.length === 0" class="empty-box">
      <el-empty :description="emptyDescription" />
    </div>
    
    <div v-else>
      <el-table :data="allCandidates" style="width: 100%" border>
        <el-table-column label="姓名" width="120">
          <template #default="{ row }">{{ row.profile?.name || '-' }}</template>
        </el-table-column>
        <el-table-column label="学历" width="150">
          <template #default="{ row }">
            {{ row.profile?.education?.degree }} ({{ row.profile?.education?.school }})
          </template>
        </el-table-column>
        <el-table-column label="技能矩阵" min-width="200">
          <template #default="{ row }">
            <span v-for="(skill, index) in row.profile?.skill_matrix" :key="index">
              {{ Object.keys(skill)[0] }}:{{ Object.values(skill)[0] }}
              <span v-if="index < (row.profile?.skill_matrix?.length || 0) - 1">, </span>
            </span>
          </template>
        </el-table-column>
        <el-table-column label="期望薪资" width="120">
          <template #default="{ row }">{{ row.profile?.expected_salary || '-' }}</template>
        </el-table-column>
        <el-table-column label="评分" width="80" sortable>
          <template #default="{ row }">{{ row.evaluation?.score || 0 }}</template>
        </el-table-column>
        <el-table-column label="排名" width="80" sortable>
          <template #default="{ row }">{{ row.evaluation?.final_rank || '-' }}</template>
        </el-table-column>
        <el-table-column label="优势" min-width="150">
          <template #default="{ row }">{{ row.evaluation?.strength || '-' }}</template>
        </el-table-column>
      </el-table>

      <div class="dashboard-charts">
        <!-- 雷达图容器 -->
        <div id="radar" style="width:400px;height:300px;display:inline-block"></div>
        <!-- 饼图容器 -->
        <div id="pie" style="width:400px;height:300px;display:inline-block"></div>
      </div>
      
      <!-- 数据为空时的提示（此处逻辑已移至外层 v-else-if，此处在有表格数据但无图表数据时显示） -->
      <el-empty v-if="radarData.length === 0 && Object.keys(pieData).length === 0" description="暂无可视化图表数据" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts';
import { getResult, getDashboard } from '@/api';

const props = defineProps<{ id?: string }>();
const route = useRoute();
const taskId = props.id || (route.params.id as string);

const loading = ref(true);
const allCandidates = ref<any[]>([]);
const radarData = ref<any[]>([]);
const pieData = ref<Record<string, any>>({});
const errorMessage = ref<string>('');

let radarChartInstance: echarts.ECharts | null = null;
let pieChartInstance: echarts.ECharts | null = null;

// 计算属性：动态决定空状态的描述文字
const emptyDescription = computed(() => {
  if (errorMessage.value) {
    return `数据加载异常：${errorMessage.value}`;
  }
  // 如果是因为任务未完成导致的空数据
  return '任务尚未完成或暂无候选人数据，请稍后刷新查看。';
});

onMounted(async () => {
  if (!taskId) {
    console.error('❌ 缺少任务 ID');
    ElMessage.error('缺少任务 ID，无法加载结果');
    loading.value = false;
    errorMessage.value = '缺少任务 ID';
    return;
  }

  try {
    const resultRes = await getResult(taskId);
    const result = resultRes.data;
    
    // 处理后端返回 "processing" 或 "failed" 状态
    if (result?.status === 'processing' || result?.status === 'failed') {
      loading.value = false;
      // 如果是 processing，提示用户稍后刷新
      if(result?.status === 'processing') {
          errorMessage.value = '任务正在处理中，请稍后刷新页面查看结果。';
      } else {
          errorMessage.value = '任务处理失败。';
      }
      return; 
    }

    if (!result || !result.all_candidates || !Array.isArray(result.all_candidates)) {
      errorMessage.value = '返回数据格式不正确或未找到候选人';
      loading.value = false;
      return;
    }
    
    allCandidates.value = result.all_candidates;
    
    const dashboardRes = await getDashboard(taskId);
    const dashboard = dashboardRes.data;
    
    // 【优化】安全赋值，防止因字段缺失导致后续渲染报错
    if (dashboard?.skill_radar && Array.isArray(dashboard.skill_radar) && dashboard.skill_radar.length > 0) {
      radarData.value = dashboard.skill_radar;
    } else {
      radarData.value = [];
    }
      
    if (dashboard?.level_pie && typeof dashboard.level_pie === 'object' && Object.keys(dashboard.level_pie).length > 0) {
      pieData.value = dashboard.level_pie;
    } else {
      pieData.value = {};
    }
    
    loading.value = false;
    
    // 确保 DOM 渲染后再绘制图表
    setTimeout(() => {
      renderCharts();
    }, 100);
  } catch (e: any) {
    console.error('❌ 结果页数据加载失败:', e);
    const msg = e instanceof Error ? e.message : '网络请求失败';
    errorMessage.value = msg;
    ElMessage.warning(`数据加载不完整：${msg}`);
    loading.value = false;
    allCandidates.value = [];
    radarData.value = [];
    pieData.value = {};
    clearCharts();
  }
});

function renderCharts() {
  const radarEl = document.getElementById('radar');
  const pieEl = document.getElementById('pie');

  // 渲染雷达图
  if (radarEl && radarData.value && radarData.value.length > 0) {
    if (radarChartInstance) {
      radarChartInstance.dispose();
    }
    radarChartInstance = echarts.init(radarEl);
    
    // 动态提取指标，防止 key 不一致
    const firstPerson = radarData.value[0];
    if (!firstPerson) return;
    
    const indicators = Object.keys(firstPerson)
      .filter(k => k !== 'name')
      .map(name => ({ name, max: 5 }));

    radarChartInstance.setOption({
      tooltip: {},
      legend: { data: radarData.value.map((item: any) => item.name), bottom: 0, type: 'scroll' },
      radar: {
        indicator: indicators,
        radius: '65%'
      },
      series: [{
        type: 'radar',
        data: radarData.value,
        emphasis: {
            lineStyle: { width: 4 }
        }
      }]
    });
  } else if (radarEl) {
    clearChartContainer(radarEl);
  }

  // 渲染饼图
  if (pieEl && pieData.value && Object.keys(pieData.value).length > 0) {
    if (pieChartInstance) {
      pieChartInstance.dispose();
    }
    pieChartInstance = echarts.init(pieEl);
    
    const pieSeriesData = Object.entries(pieData.value).map(([key, value]) => ({ name: key, value }));
    pieChartInstance.setOption({
      tooltip: { trigger: 'item' },
      legend: { top: '5%', left: 'center', type: 'scroll' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        data: pieSeriesData,
        label: {
            show: true,
            formatter: '{b}: {c}'
        }
      }]
    });
  } else if (pieEl) {
    clearChartContainer(pieEl);
  }
}

function clearChartContainer(el: HTMLElement) {
  el.innerHTML = '';
}

function clearCharts() {
  if (radarChartInstance) {
    radarChartInstance.dispose();
    radarChartInstance = null;
  }
  if (pieChartInstance) {
    pieChartInstance.dispose();
    pieChartInstance = null;
  }
  const radarEl = document.getElementById('radar');
  const pieEl = document.getElementById('pie');
  if (radarEl) radarEl.innerHTML = '';
  if (pieEl) pieEl.innerHTML = '';
}

onBeforeUnmount(() => {
  clearCharts();
});
</script>

<style scoped>
.result-view {
  max-width: 1000px;
  margin: 40px auto;
}
.result-header {
  font-size: 1.3rem;
  font-weight: bold;
}
.loading-box, .empty-box {
  text-align: center;
  padding: 3rem;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
/* 新增：原生 Loading 样式 */
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}
.loading-text {
  color: #606266;
  font-size: 14px;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.dashboard-charts {
  margin-top: 2rem;
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}
</style>