<template>
  <el-card class="result-view">
    <template #header>
      <div class="result-header">
        <span>筛选结果 (Task: {{ taskId }})</span>
      </div>
    </template>
    <div v-if="loading" class="loading-box">
      <el-loading text="加载分析结果..." />
    </div>
    <div v-else-if="allCandidates.length === 0" class="empty-box">
      <el-empty description="暂无候选人数据" />
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
      
      <!-- 数据为空时的提示 -->
      <el-empty v-if="allCandidates.length > 0 && radarData.length === 0 && Object.keys(pieData).length === 0" description="暂无可视化图表数据" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts';
import { getResult, getDashboard } from '@/api';

const props = defineProps<{ id?: string }>();
const route = useRoute();
// 优先从 props 获取，其次从 route params 获取
const taskId = props.id || (route.params.id as string);

const loading = ref(true);
const allCandidates = ref<any[]>([]);
// 初始化为空，严禁预设假数据
const radarData = ref<any[]>([]);
const pieData = ref<Record<string, any>>({});

let radarChartInstance: echarts.ECharts | null = null;
let pieChartInstance: echarts.ECharts | null = null;

onMounted(async () => {
  console.log('📄 ResultView 挂载，Task ID:', taskId);
  
  if (!taskId) {
    console.error('❌ 缺少任务 ID');
    ElMessage.error('缺少任务 ID，无法加载结果');
    loading.value = false;
    return;
  }

  try {
    console.log('🔄 正在获取结果数据...');
    const resultRes = await getResult(taskId);
    const result = resultRes.data; // 修复：从 .data 中获取实际响应体
    console.log('📊 获取到的结果数据:', result);
    
    if (!result || !result.all_candidates || !Array.isArray(result.all_candidates)) {
      throw new Error('返回数据格式不正确或缺少候选人列表');
    }
    
    allCandidates.value = result.all_candidates;
    
    console.log('📈 正在获取仪表盘数据...');
    const dashboardRes = await getDashboard(taskId);
    const dashboard = dashboardRes.data; // 修复：从 .data 中获取实际响应体
    console.log('📉 获取到的仪表盘数据:', dashboard);
    
    // 【关键修改】仅当后端真正返回有效数据时才赋值，否则保持为空
    if (dashboard?.skill_radar && Array.isArray(dashboard.skill_radar) && dashboard.skill_radar.length > 0) {
      radarData.value = dashboard.skill_radar;
    } else {
      radarData.value = [];
      console.warn('⚠️ 雷达图数据为空');
    }
      
    if (dashboard?.level_pie && typeof dashboard.level_pie === 'object' && Object.keys(dashboard.level_pie).length > 0) {
      pieData.value = dashboard.level_pie;
    } else {
      pieData.value = {};
      console.warn('⚠️ 饼图数据为空');
    }
    
    loading.value = false;
    
    // 延迟渲染图表以确保 DOM 已就绪
    setTimeout(() => {
      renderCharts();
    }, 100);
  } catch (e: any) {
    console.error('❌ 结果页数据加载失败:', e);
    const msg = e instanceof Error ? e.message : '未知错误';
    ElMessage.error(`结果加载失败：${msg}`);
    loading.value = false;
    // 出错时清空所有数据
    allCandidates.value = [];
    radarData.value = [];
    pieData.value = {};
    clearCharts();
  }
});

function renderCharts() {
  const radarEl = document.getElementById('radar');
  const pieEl = document.getElementById('pie');

  // 【关键修改】严格检查：必须有 DOM 元素 且 数据非空 才渲染
  if (radarEl && radarData.value && radarData.value.length > 0) {
    if (radarChartInstance) {
      radarChartInstance.dispose();
    }
    radarChartInstance = echarts.init(radarEl);
    
    const firstPerson = radarData.value[0];
    const indicators = Object.keys(firstPerson || {})
      .filter(k => k !== 'name')
      .map(name => ({ name, max: 5 }));

    radarChartInstance.setOption({
      tooltip: {},
      legend: { data: radarData.value.map((item: any) => item.name), bottom: 0 },
      radar: {
        indicator: indicators,
        radius: '65%'
      },
      series: [{
        type: 'radar',
        data: radarData.value
      }]
    });
  } else if (radarEl) {
    // 数据为空，清空容器以防残留
    clearChartContainer(radarEl);
  }

  if (pieEl && pieData.value && Object.keys(pieData.value).length > 0) {
    if (pieChartInstance) {
      pieChartInstance.dispose();
    }
    pieChartInstance = echarts.init(pieEl);
    
    const pieSeriesData = Object.entries(pieData.value).map(([key, value]) => ({ name: key, value }));
    pieChartInstance.setOption({
      tooltip: { trigger: 'item' },
      legend: { top: '5%', left: 'center' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        data: pieSeriesData
      }]
    });
  } else if (pieEl) {
    // 数据为空，清空容器以防残留
    clearChartContainer(pieEl);
  }
}

function clearChartContainer(el: HTMLElement) {
  el.innerHTML = '';
  // 可选：在这里添加一个 "暂无数据" 的提示文字
  // el.innerHTML = '<div style="color:#999;text-align:center;line-height:300px;">暂无图表数据</div>';
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
}
.dashboard-charts {
  margin-top: 2rem;
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}
</style>