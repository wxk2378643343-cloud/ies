<template>
  <div v-loading="loading">
    <h2 class="page-title">数据看板</h2>

    <!-- 概览卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6" v-for="s in statCards" :key="s.label">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-value" :style="{color: s.color}">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:20px">
      <!-- 近30天行为趋势折线图 -->
      <el-col :xs="24" :md="16">
        <el-card>
          <template #header>近 30 天行为趋势</template>
          <div ref="lineRef" style="height:300px" />
        </el-card>
      </el-col>

      <!-- 各分类内容分布饼图 -->
      <el-col :xs="24" :md="8">
        <el-card>
          <template #header>内容分类分布</template>
          <div ref="pieRef" style="height:300px" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 行为类型柱图 -->
    <el-card style="margin-top:20px">
      <template #header>行为类型统计</template>
      <div ref="barRef" style="height:220px" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import request from '../../utils/request'

const loading = ref(true)
const statCards = ref([])
const lineRef = ref(null)
const pieRef  = ref(null)
const barRef  = ref(null)

onMounted(async () => {
  const [overview, trend, cats, actions] = await Promise.all([
    request.get('/api/admin/stats/overview'),
    request.get('/api/admin/stats/behaviors', { params: { days: 30 } }),
    request.get('/api/admin/stats/categories'),
    request.get('/api/admin/stats/action_summary'),
  ])
  loading.value = false

  statCards.value = [
    { label: '注册用户', value: overview.total_users,    color: '#409eff' },
    { label: '发布内容', value: overview.total_contents,  color: '#67c23a' },
    { label: '行为总量', value: overview.total_behaviors, color: '#e6a23c' },
    { label: '活跃用户', value: overview.active_users,   color: '#f56c6c' },
  ]

  await nextTick()
  renderLine(trend)
  renderPie(cats)
  renderBar(actions)
})

function renderLine(data) {
  const chart = echarts.init(lineRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['点击', '阅读', '收藏'], bottom: 0 },
    grid: { left: 40, right: 20, top: 10, bottom: 50 },
    xAxis: { type: 'category', data: data.dates, axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [
      { name: '点击', type: 'line', smooth: true, data: data.click,   lineStyle: { color: '#409eff' }, itemStyle: { color: '#409eff' } },
      { name: '阅读', type: 'line', smooth: true, data: data.read,    lineStyle: { color: '#67c23a' }, itemStyle: { color: '#67c23a' } },
      { name: '收藏', type: 'line', smooth: true, data: data.collect, lineStyle: { color: '#e6a23c' }, itemStyle: { color: '#e6a23c' } },
    ],
  })
}

function renderPie(cats) {
  const chart = echarts.init(pieRef.value)
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 10, top: 'center' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      data: cats.map(c => ({ name: c.category, value: c.count })),
      label: { show: false },
    }],
  })
}

function renderBar(actions) {
  const chart = echarts.init(barRef.value)
  const names = { click: '点击', read: '阅读', collect: '收藏' }
  const colors = { click: '#409eff', read: '#67c23a', collect: '#e6a23c' }
  chart.setOption({
    tooltip: {},
    grid: { left: 60, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: Object.keys(actions).map(k => names[k] || k) },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: Object.entries(actions).map(([k, v]) => ({ value: v, itemStyle: { color: colors[k] || '#909399' } })),
      barMaxWidth: 60,
    }],
  })
}
</script>

<style scoped>
.page-title { margin-bottom: 20px; font-size: 18px; color: #303133; }
.stat-row { margin-bottom: 4px; }
.stat-card { text-align: center; padding: 8px 0; }
.stat-value { font-size: 32px; font-weight: 700; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
</style>
