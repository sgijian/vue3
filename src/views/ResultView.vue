<template>
  <el-card class="result-view">
    <template #header>
      <div class="result-header">
        <span>筛选结果</span>
      </div>
    </template>
    <div v-if="loading" class="loading-box">
      <el-skeleton :rows="3" animated />
    </div>
    <div v-else>
      <!-- Top 3 候选人卡片 -->
      <div class="top-candidates-section">
        <h3 class="section-title">🏆 Top 3 候选人</h3>
        <el-row :gutter="20">
          <el-col :span="8" v-for="(cand, index) in top3Candidates" :key="cand.id">
            <el-card shadow="hover" class="top-card">
              <div class="rank-badge">{{ index + 1 }}</div>
              <div class="cand-name">{{ cand.name }}</div>
              <div class="cand-score">{{ cand.score }} 分</div>
              <el-divider />
              <div class="cand-reason">
                <strong>核心优势：</strong>
                {{ cand.reason }}
              </div>
              <el-button link type="primary" @click="openDetail(cand)">查看详情</el-button>
            </el-card>
          </el-col>
          <el-col v-if="top3Candidates.length === 0" :span="24">
            <div class="empty-card">暂无候选人数据</div>
          </el-col>
        </el-row>
      </div>

      <!-- Dashboard 图表 -->
      <div class="dashboard-charts">
        <div ref="barChartRef" style="width:400px;height:300px;display:inline-block"></div>
        <div ref="radarChartRef" style="width:400px;height:300px;display:inline-block"></div>
        <div ref="pieChartRef" style="width:400px;height:300px;display:inline-block"></div>
      </div>

      <!-- 全员排名表格 -->
      <el-card class="table-card">
        <template #header>
          <span>全员排名详情</span>
        </template>
        <el-table :data="allCandidates" stripe style="width: 100%">
          <el-table-column prop="final_rank" label="排名" width="60" align="center">
            <template #default="{ row }">
              <el-tag :type="row.final_rank <= 3 ? 'success' : 'info'" effect="dark">
                {{ row.final_rank }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="姓名" width="100" />
          <el-table-column prop="education" label="学历" width="100" />
          <el-table-column prop="skills" label="核心技能" min-width="150">
            <template #default="{ row }">
              <el-tag v-for="skill in (Array.isArray(row.skills) ? row.skills.slice(0, 3) : [])" :key="skill" size="small" style="margin-right: 4px">
                {{ skill }}
              </el-tag>
              <span v-if="Array.isArray(row.skills) && row.skills.length > 3" style="color: #999; font-size: 12px">+{{ row.skills.length - 3 }}</span>
              <span v-if="!Array.isArray(row.skills) || row.skills.length === 0" style="color: #bbb; font-size: 12px">无</span>
            </template>
          </el-table-column>
          <el-table-column prop="projects" label="项目经验" min-width="150" show-overflow-tooltip />
          <el-table-column prop="salary_expectation" label="期望薪资" width="100" />
          <el-table-column prop="stability" label="稳定性" width="80" align="center">
             <template #default="{ row }">
               <el-icon :color="row.stability && row.stability.includes('高') ? '#67C23A' : '#E6A23C'">
                 <Check v-if="row.stability && row.stability.includes('高')" />
                 <Warning v-else />
               </el-icon>
             </template>
          </el-table-column>
          <el-table-column prop="score" label="综合得分" width="90" sortable>
            <template #default="{ row }">
              <span style="font-weight: bold; color: #409EFF">{{ row.score }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDetail(row)">查看详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="allCandidates.length === 0" class="empty-table">暂无数据</div>
      </el-card>

      <!-- 候选人详情抽屉 -->
      <el-drawer v-model="drawerVisible" title="候选人详细画像" size="50%">
        <div v-if="currentCandidate" class="detail-content">
          <div class="detail-header">
            <h3>{{ currentCandidate.name }} <span class="score-tag">{{ currentCandidate.score }}分</span></h3>
            <p>排名：NO.{{ currentCandidate.final_rank }}</p>
          </div>
          <el-descriptions title="基本信息" :column="2" border>
            <el-descriptions-item label="学历">{{ currentCandidate.education }}</el-descriptions-item>
            <el-descriptions-item label="期望薪资">{{ currentCandidate.salary_expectation }}</el-descriptions-item>
            <el-descriptions-item label="稳定性" :span="2">{{ currentCandidate.stability }}</el-descriptions-item>
          </el-descriptions>
          <h4 class="sub-title">技能矩阵</h4>
          <div class="skill-bars">
            <div v-for="(val, key) in currentCandidate.skill_matrix" :key="key" class="skill-item">
              <span class="skill-name">{{ key }}</span>
              <el-progress :percentage="val" :status="val > 80 ? 'success' : 'normal'" />
            </div>
            <div v-if="!currentCandidate.skill_matrix || Object.keys(currentCandidate.skill_matrix).length === 0" class="empty-skill">暂无技能数据</div>
          </div>
          <h4 class="sub-title">项目成果</h4>
          <el-alert type="info" :closable="false" show-icon>
            {{ currentCandidate.project_details || currentCandidate.projects || '暂无项目数据' }}
          </el-alert>
          <h4 class="sub-title">AI 评估结论</h4>
          <p class="eval-text">{{ currentCandidate.evaluation_summary || currentCandidate.reason || '暂无评估结论' }}</p>
        </div>
      </el-drawer>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, Warning } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getResult, getDashboard } from '@/api'

const route = useRoute()
const props = defineProps<{ id?: string }>();
const taskId = props.id || route.params.id as string

const loading = ref(true)
const allCandidates = ref<any[]>([])
const top3Candidates = ref<any[]>([])
const drawerVisible = ref(false)
const currentCandidate = ref<any | null>(null)
const barChartRef = ref(null)
const radarChartRef = ref(null)
const pieChartRef = ref(null)

onMounted(async () => {
  try {
    const result = await getResult(taskId)
    allCandidates.value = result.all_candidates || []
    top3Candidates.value = [...allCandidates.value].sort((a, b) => b.score - a.score).slice(0, 3)
    const dashboard = await getDashboard(taskId)
    await nextTick()
    renderCharts(dashboard)
  } catch (e) {
    allCandidates.value = []
    top3Candidates.value = []
    await nextTick()
    renderCharts()
    loading.value = false
    ElMessage.warning('无数据，已显示空白分析图')
  } finally {
    loading.value = false
  }
})

function renderCharts(data?: any) {
  // 分数分布柱状图
  if (barChartRef.value) {
    const bar = echarts.init(barChartRef.value)
    const barOption = data?.score_distribution ? {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['高分 (>85)', '中等 (60-85)', '待改进 (<60)'] },
      yAxis: { type: 'value' },
      series: [{
        data: [data.score_distribution.high, data.score_distribution.medium, data.score_distribution.low],
        type: 'bar',
        itemStyle: { color: ['#67C23A', '#E6A23C', '#F56C6C'] },
        showBackground: true,
        backgroundStyle: { color: 'rgba(180, 180, 180, 0.2)' }
      }]
    } : {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['高分 (>85)', '中等 (60-85)', '待改进 (<60)'] },
      yAxis: { type: 'value' },
      series: [{
        data: [0, 0, 0],
        type: 'bar',
        itemStyle: { color: ['#67C23A', '#E6A23C', '#F56C6C'] },
        showBackground: true,
        backgroundStyle: { color: 'rgba(180, 180, 180, 0.2)' }
      }]
    }
    bar.setOption(barOption)
  }

  // 技能雷达图
  if (radarChartRef.value) {
    const radar = echarts.init(radarChartRef.value)
    radar.setOption(data?.skill_radar || {
      radar: { indicator: [{ name: 'Java', max: 100 }, { name: 'Vue', max: 100 }, { name: 'Python', max: 100 }, { name: '沟通', max: 100 }, { name: '管理', max: 100 }] },
      series: [{ type: 'radar', data: [] }]
    })
  }

  // 熟练度饼图
  if (pieChartRef.value) {
    const pie = echarts.init(pieChartRef.value)
    pie.setOption(data?.level_pie || {
      series: [{
        type: 'pie',
        radius: '50%',
        data: [
          { value: 0, name: '专家级' },
          { value: 0, name: '熟练工' },
          { value: 0, name: '入门级' }
        ]
      }]
    })
  }
}

function openDetail(cand: any) {
  currentCandidate.value = cand
  drawerVisible.value = true
}
</script>

<style scoped>
.result-view {
  max-width: 1100px;
  margin: 40px auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  padding: 32px;
}
.result-header {
  font-size: 1.3rem;
  font-weight: bold;
  color: #409EFF;
}
.loading-box {
  text-align: center;
  padding: 2rem;
}
.dashboard-charts {
  margin-top: 2rem;
  display: flex;
  justify-content: space-between;
  gap: 24px;
}
.dashboard-charts > div {
  background: #f9fafc;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 16px;
}
/* 饼图样式优化 */
#pieChart {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.top-candidates-section {
  margin-bottom: 20px;
}
.section-title {
  margin-bottom: 15px;
  font-size: 1.2rem;
  border-left: 4px solid #409EFF;
  padding-left: 10px;
}
.top-card {
  position: relative;
  text-align: center;
}
.rank-badge {
  position: absolute;
  top: -10px;
  left: -10px;
  width: 30px;
  height: 30px;
  background: #E6A23C;
  color: white;
  border-radius: 50%;
  line-height: 30px;
  font-weight: bold;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}
.cand-name {
  font-size: 1.2rem;
  font-weight: bold;
  margin-top: 10px;
}
.cand-score {
  color: #F56C6C;
  font-size: 1.5rem;
  font-weight: bold;
  margin: 5px 0;
}
.cand-reason {
  font-size: 0.9rem;
  color: #606266;
  text-align: left;
  line-height: 1.5;
}
.empty-card {
  text-align: center;
  color: #bbb;
  font-size: 1rem;
  padding: 2rem 0;
}
.table-card {
  margin-top: 20px;
}
.empty-table {
  text-align: center;
  color: #bbb;
  font-size: 1rem;
  padding: 1rem 0;
}
.detail-content {
  padding: 10px;
}
.detail-header {
  text-align: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}
.score-tag {
  color: #409EFF;
  font-weight: bold;
  font-size: 1.2rem;
}
.sub-title {
  margin: 20px 0 10px;
  font-weight: bold;
  color: #303133;
}
.skill-item {
  margin-bottom: 15px;
}
.skill-name {
  display: block;
  margin-bottom: 5px;
  font-size: 0.9rem;
  color: #606266;
}
.empty-skill {
  text-align: center;
  color: #bbb;
  font-size: 1rem;
  padding: 1rem 0;
}
.eval-text {
  background: #f4f4f5;
  padding: 15px;
  border-radius: 4px;
  line-height: 1.6;
  color: #333;
}
</style>
