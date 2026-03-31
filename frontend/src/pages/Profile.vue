<template>
  <div class="profile-page">
    <!-- 顶部导航 -->
    <div class="profile-header">
      <el-button link :icon="ArrowLeft" @click="$router.push('/')">返回首页</el-button>
      <span class="header-title">个人中心</span>
    </div>

    <div class="profile-body" v-loading="loading">
      <!-- 用户信息卡 -->
      <el-card class="user-card">
        <div class="user-info">
          <el-avatar :size="64" :icon="UserFilled" />
          <div>
            <h2>{{ auth.user?.username }}</h2>
            <p class="user-email">{{ auth.user?.email }}</p>
          </div>
        </div>
      </el-card>

      <el-row :gutter="20" style="margin-top:20px">
        <!-- 左：兴趣标签 + 雷达图 -->
        <el-col :xs="24" :md="12">
          <el-card>
            <template #header><span>当前兴趣画像</span></template>

            <!-- 进度条形式展示标签权重 -->
            <div v-for="tag in interests" :key="tag.tag" class="tag-row">
              <span class="tag-label">{{ tag.tag }}</span>
              <el-progress
                :percentage="Math.round(tag.weight * 100)"
                :stroke-width="10"
                :color="progressColor(tag.weight)"
                style="flex:1"
              />
              <span class="tag-weight">{{ (tag.weight * 100).toFixed(1) }}%</span>
            </div>
            <el-empty v-if="!loading && interests.length === 0"
              description="暂无兴趣数据，浏览内容后触发推理" style="padding:16px" />

            <!-- ECharts 雷达图 -->
            <div ref="radarRef" style="height:260px;margin-top:12px" />
          </el-card>
        </el-col>

        <!-- 右：兴趣演化折线图 -->
        <el-col :xs="24" :md="12">
          <el-card>
            <template #header>
              <span>兴趣演化趋势</span>
              <span class="header-sub">（历史推理记录）</span>
            </template>
            <div ref="lineRef" style="height:380px" />
            <el-empty v-if="!loading && history.length === 0"
              description="暂无演化数据" style="padding:16px" />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { ArrowLeft, UserFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useAuthStore } from '../stores/auth'
import request from '../utils/request'

const auth = useAuthStore()
const loading = ref(true)
const interests = ref([])
const history = ref([])

const radarRef = ref(null)
const lineRef = ref(null)
let radarChart = null
let lineChart = null

const CATEGORIES = ['科技','体育','娱乐','财经','教育','健康','游戏','旅游']
const COLORS = ['#5470c6','#91cc75','#fac858','#ee6666','#73c0de','#3ba272','#fc8452','#9a60b4']

onMounted(async () => {
  try {
    const [tags, hist] = await Promise.all([
      request.get('/api/recommend/interests'),
      request.get('/api/recommend/history', { params: { limit: 20 } }),
    ])
    interests.value = tags
    history.value = hist
  } finally {
    loading.value = false
  }
  await nextTick()
  renderRadar()
  renderLine()
})

// 雷达图
function renderRadar() {
  if (!radarRef.value || interests.value.length === 0) return
  radarChart = echarts.init(radarRef.value)
  radarChart.setOption({
    radar: {
      indicator: CATEGORIES.map(c => ({ name: c, max: 1 })),
      radius: '65%',
    },
    series: [{
      type: 'radar',
      data: [{
        value: CATEGORIES.map(c => {
          const t = interests.value.find(i => i.tag === c)
          return t ? t.weight : 0
        }),
        name: '兴趣权重',
        areaStyle: { opacity: 0.3 },
        lineStyle: { color: '#409eff' },
        itemStyle: { color: '#409eff' },
      }],
    }],
  })
}

// 演化折线图
function renderLine() {
  if (!lineRef.value || history.value.length === 0) return
  lineChart = echarts.init(lineRef.value)

  const times = history.value.map(r => r.snapshot_time.slice(0, 16).replace('T', ' '))

  // 取出权重最高的 top4 类别
  const lastRecord = history.value[history.value.length - 1]
  const topCats = (lastRecord?.tags || [])
    .sort((a, b) => b.score - a.score)
    .slice(0, 4)
    .map(t => t.tag)

  const series = topCats.map((cat, idx) => ({
    name: cat,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: { color: COLORS[idx] },
    itemStyle: { color: COLORS[idx] },
    data: history.value.map(r => {
      const t = (r.tags || []).find(x => x.tag === cat)
      return t ? +(t.score * 100).toFixed(2) : 0
    }),
  }))

  lineChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: topCats, bottom: 0 },
    grid: { left: 40, right: 20, top: 20, bottom: 60 },
    xAxis: {
      type: 'category',
      data: times,
      axisLabel: { rotate: 30, fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      name: '兴趣权重（%）',
      max: 100,
    },
    series,
  })
}

function progressColor(w) {
  if (w > 0.2) return '#409eff'
  if (w > 0.1) return '#67c23a'
  return '#e6a23c'
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: #f5f7fa;
}
.profile-header {
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.profile-body {
  max-width: 1100px;
  margin: 24px auto;
  padding: 0 24px;
}
.user-card .user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-info h2 {
  font-size: 20px;
  margin-bottom: 4px;
}
.user-email {
  color: #909399;
  font-size: 14px;
}
.tag-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.tag-label {
  width: 42px;
  font-size: 13px;
  color: #606266;
  flex-shrink: 0;
}
.tag-weight {
  width: 44px;
  text-align: right;
  font-size: 12px;
  color: #909399;
}
.header-sub {
  font-size: 12px;
  color: #909399;
  margin-left: 6px;
}
</style>
