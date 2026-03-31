<template>
  <div class="detail-page">
    <!-- 顶部导航 -->
    <div class="detail-header">
      <el-button link :icon="ArrowLeft" @click="$router.back()">返回</el-button>
    </div>

    <el-skeleton :loading="loading" animated>
      <template #template>
        <div style="padding: 32px">
          <el-skeleton-item variant="h1" style="width: 60%" />
          <el-skeleton-item variant="text" style="margin-top: 16px" />
          <el-skeleton-item variant="text" />
          <el-skeleton-item variant="text" />
        </div>
      </template>

      <template #default>
        <div v-if="content" class="detail-body">
          <el-tag :type="tagType(content.category)" style="margin-bottom: 12px">
            {{ content.category }}
          </el-tag>
          <h1 class="detail-title">{{ content.title }}</h1>
          <p class="detail-meta">发布时间：{{ content.created_at?.slice(0, 10) }}</p>
          <el-divider />
          <div class="detail-content">{{ content.body }}</div>
          <el-divider />

          <!-- 收藏按钮 -->
          <el-button
            :type="collected ? 'warning' : 'default'"
            :icon="Star"
            @click="toggleCollect"
          >
            {{ collected ? '已收藏' : '收藏' }}
          </el-button>
        </div>
        <el-empty v-else description="内容不存在" />
      </template>
    </el-skeleton>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const route = useRoute()
const content = ref(null)
const loading = ref(true)
const collected = ref(false)

let enterTime = null  // 进入页面时间戳，用于计算停留时长

onMounted(async () => {
  enterTime = Date.now()
  const id = Number(route.params.id)
  try {
    content.value = await request.get(`/api/content/${id}`)
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(async () => {
  // 离开时上报 read 行为，附带停留时长
  if (!content.value) return
  const duration = (Date.now() - enterTime) / 1000
  await request.post('/api/behavior/report', {
    content_id: content.value.id,
    action: 'read',
    duration_sec: duration,
  }).catch(() => {})
})

async function toggleCollect() {
  if (!content.value) return
  if (collected.value) {
    collected.value = false
    return
  }
  await request.post('/api/behavior/report', {
    content_id: content.value.id,
    action: 'collect',
  })
  collected.value = true
  ElMessage.success('已收藏')
}

const TAG_TYPES = ['', 'success', 'warning', 'danger', 'info']
function tagType(cat) {
  const idx = ['科技','体育','娱乐','财经','教育','健康','游戏','旅游'].indexOf(cat)
  return TAG_TYPES[idx % TAG_TYPES.length] || ''
}
</script>

<style scoped>
.detail-page {
  max-width: 800px;
  margin: 0 auto;
  min-height: 100vh;
  background: #fff;
}
.detail-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e4e7ed;
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 10;
}
.detail-body {
  padding: 32px 24px;
}
.detail-title {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
  line-height: 1.4;
}
.detail-meta {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}
.detail-content {
  font-size: 15px;
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
}
</style>
