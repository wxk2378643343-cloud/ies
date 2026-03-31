<template>
  <div>
    <h2 class="page-title">模型训练与监控</h2>

    <el-row :gutter="20">
      <!-- 左：训练控制 + 最新指标 -->
      <el-col :xs="24" :md="10">
        <el-card>
          <template #header>触发训练</template>
          <el-form label-width="80px">
            <el-form-item label="训练轮数">
              <el-input-number v-model="epochs" :min="5" :max="100" style="width:140px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="trainStatus.running"
                @click="triggerTrain" :disabled="trainStatus.running">
                {{ trainStatus.running ? '训练中...' : '开始训练' }}
              </el-button>
              <el-button @click="pollStatus">刷新状态</el-button>
            </el-form-item>
          </el-form>

          <!-- 训练状态 -->
          <el-alert v-if="trainStatus.running"
            title="模型训练中，请稍候..." type="info" :closable="false" show-icon />
          <el-alert v-if="trainStatus.error"
            :title="'训练出错：' + trainStatus.error" type="error" :closable="false" show-icon />

          <!-- 最新指标 -->
          <template v-if="trainStatus.last_result">
            <el-divider>最新训练结果</el-divider>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="版本">{{ trainStatus.last_result.version }}</el-descriptions-item>
              <el-descriptions-item label="Val Loss">{{ trainStatus.last_result.val_loss }}</el-descriptions-item>
              <el-descriptions-item label="Accuracy">{{ trainStatus.last_result.val_accuracy }}</el-descriptions-item>
              <el-descriptions-item label="Precision@1">{{ trainStatus.last_result['precision@1'] }}</el-descriptions-item>
              <el-descriptions-item label="Recall@1">{{ trainStatus.last_result['recall@1'] }}</el-descriptions-item>
              <el-descriptions-item label="NDCG@1">{{ trainStatus.last_result['ndcg@1'] }}</el-descriptions-item>
            </el-descriptions>
          </template>
        </el-card>

        <!-- 损失曲线 -->
        <el-card style="margin-top:16px" v-show="trainStatus.last_result?.history">
          <template #header>本次训练损失曲线</template>
          <div ref="lossRef" style="height:220px" />
        </el-card>
      </el-col>

      <!-- 右：版本历史表格 -->
      <el-col :xs="24" :md="14">
        <el-card>
          <template #header>
            模型版本历史
            <el-button link size="small" style="float:right" @click="fetchVersions">刷新</el-button>
          </template>
          <el-table :data="versions" v-loading="vLoading" stripe size="small">
            <el-table-column prop="version"    label="版本"       width="160" />
            <el-table-column prop="loss"       label="Val Loss"   width="90" />
            <el-table-column prop="accuracy"   label="Accuracy"   width="90" />
            <el-table-column prop="ndcg"       label="NDCG@1"     width="90" />
            <el-table-column label="训练时间" show-overflow-tooltip>
              <template #default="{ row }">{{ row.trained_at?.slice(0, 19).replace('T',' ') }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!vLoading && versions.length === 0" description="暂无训练记录" />
        </el-card>

        <!-- 多版本 Loss 对比折线图 -->
        <el-card style="margin-top:16px" v-show="versions.length > 1">
          <template #header>各版本 Val Loss 对比</template>
          <div ref="versionRef" style="height:220px" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import request from '../../utils/request'

const epochs     = ref(20)
const trainStatus = ref({ running: false, last_result: null, error: null })
const versions   = ref([])
const vLoading   = ref(false)
const lossRef    = ref(null)
const versionRef = ref(null)

let lossChart    = null
let versionChart = null
let pollTimer    = null
let alive        = false

// versions 数据变化后，用 setTimeout 推出当前 JS 任务队列
// 确保浏览器完成布局（clientWidth/clientHeight 有值）再 init ECharts
watch(versions, () => {
  setTimeout(renderVersionChart, 0)
}, { flush: 'post' })

// trainStatus.last_result 变化后渲染 loss 曲线
watch(() => trainStatus.value.last_result, (val) => {
  if (val?.history) setTimeout(() => renderLossChart(val.history), 0)
}, { flush: 'post' })

onMounted(() => {
  alive = true
  // 用 setTimeout 将数据请求推到路由导航完全结束之后
  // 避免 ElTable doLayout 在 Vue 初始渲染未完成时触发 vnode null 错误
  setTimeout(async () => {
    if (!alive) return
    await Promise.all([fetchVersions(), pollStatus()])
  }, 0)
})

onUnmounted(() => {
  alive = false
  clearTimeout(pollTimer)
  lossChart?.dispose()
  versionChart?.dispose()
  lossChart = null
  versionChart = null
})

async function fetchVersions() {
  vLoading.value = true
  try {
    versions.value = await request.get('/api/admin/model/versions')
  } finally {
    vLoading.value = false
  }
}

async function pollStatus() {
  if (!alive) return
  trainStatus.value = await request.get('/api/admin/model/status')
  if (!alive) return
  if (trainStatus.value.running) {
    pollTimer = setTimeout(pollStatus, 3000)
  } else {
    clearTimeout(pollTimer)
    if (trainStatus.value.last_result) fetchVersions()
  }
}

async function triggerTrain() {
  await request.post('/api/admin/model/train', null, { params: { epochs: epochs.value } })
  ElMessage.success(`训练任务已启动（${epochs.value} 轮）`)
  setTimeout(pollStatus, 1000)
}

function renderLossChart(history) {
  if (!lossRef.value || !history) return
  if (!lossChart) lossChart = echarts.init(lossRef.value)
  const xs = history.train_loss.map((_, i) => `Epoch ${i + 1}`)
  lossChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['训练损失', '验证损失'], bottom: 0 },
    grid: { left: 45, right: 10, top: 10, bottom: 50 },
    xAxis: { type: 'category', data: xs, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', name: 'Loss' },
    series: [
      { name: '训练损失', type: 'line', smooth: true, data: history.train_loss, itemStyle: { color: '#409eff' } },
      { name: '验证损失', type: 'line', smooth: true, data: history.val_loss,   itemStyle: { color: '#f56c6c' } },
    ],
  })
}

function renderVersionChart() {
  if (!versionRef.value || versions.value.length < 2) return
  if (!versionChart) versionChart = echarts.init(versionRef.value)
  const sorted = [...versions.value].reverse()  // 按时间正序
  versionChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 60 },
    xAxis: { type: 'category', data: sorted.map(v => v.version.slice(-8)), axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: 'value', name: 'Val Loss' },
    series: [{
      type: 'line', smooth: true,
      data: sorted.map(v => v.loss),
      itemStyle: { color: '#409eff' },
      markPoint: {
        data: [{ type: 'min', name: '最低' }],
        symbol: 'pin',
      },
    }],
  })
}
</script>

<style scoped>
.page-title { margin-bottom: 20px; font-size: 18px; color: #303133; }
</style>
