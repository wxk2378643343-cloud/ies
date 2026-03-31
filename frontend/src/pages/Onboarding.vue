<template>
  <div class="ob-page">
    <!-- 顶部 -->
    <div class="ob-header">
      <div class="brand">✦ IES</div>
    </div>

    <div class="ob-body">
      <div class="ob-card">
        <h2 class="ob-title">你对哪些内容感兴趣？</h2>
        <p class="ob-sub">选择感兴趣的分类，系统将为你推荐个性化内容（至少选 1 个）</p>

        <div class="cat-grid">
          <div
            v-for="cat in categories"
            :key="cat.name"
            class="cat-item"
            :class="{ selected: selected.includes(cat.name) }"
            @click="toggle(cat.name)"
          >
            <span class="cat-icon">{{ cat.icon }}</span>
            <span class="cat-name">{{ cat.name }}</span>
            <div class="check-mark">✓</div>
          </div>
        </div>

        <div class="ob-footer">
          <span class="selected-tip">
            已选 <strong>{{ selected.length }}</strong> 个分类
          </span>
          <button
            class="ob-btn"
            :disabled="selected.length === 0 || loading"
            @click="confirm"
          >
            <span v-if="!loading">开始探索 →</span>
            <span v-else class="spin-wrap"><i class="spin"></i> 保存中...</span>
          </button>
        </div>

        <p class="skip-tip">
          <span @click="skip">跳过，稍后设置</span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const router = useRouter()
const loading = ref(false)
const selected = ref([])

const categories = [
  { name: '科技', icon: '💻' },
  { name: '体育', icon: '⚽' },
  { name: '娱乐', icon: '🎬' },
  { name: '财经', icon: '📊' },
  { name: '教育', icon: '📚' },
  { name: '健康', icon: '🏃' },
  { name: '游戏', icon: '🎮' },
  { name: '旅游', icon: '✈️' },
]

function toggle(name) {
  const idx = selected.value.indexOf(name)
  if (idx === -1) selected.value.push(name)
  else selected.value.splice(idx, 1)
}

async function confirm() {
  if (selected.value.length === 0) return
  loading.value = true
  try {
    await request.post('/api/recommend/interests/init', { tags: selected.value })
    ElMessage.success('兴趣设置成功，正在为你推荐内容...')
    router.push('/')
  } finally {
    loading.value = false
  }
}

function skip() {
  router.push('/')
}
</script>

<style scoped>
.ob-page {
  min-height: 100vh;
  background: linear-gradient(145deg, #0f1b3d 0%, #1a3a6b 60%, #1e5fa8 100%);
  display: flex;
  flex-direction: column;
}

.ob-header {
  padding: 24px 36px;
}
.brand {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 3px;
}

.ob-body {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.ob-card {
  background: #fff;
  border-radius: 24px;
  padding: 44px 48px;
  max-width: 680px;
  width: 100%;
  box-shadow: 0 24px 60px rgba(0,0,0,0.25);
}

.ob-title {
  font-size: 26px;
  font-weight: 700;
  color: #0f1b3d;
  margin-bottom: 8px;
}
.ob-sub {
  font-size: 14px;
  color: #94a3b8;
  margin-bottom: 32px;
}

/* 分类网格 */
.cat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 32px;
}

.cat-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 12px;
  border-radius: 16px;
  border: 2px solid #e2e8f0;
  background: #f8faff;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}
.cat-item:hover {
  border-color: #93c5fd;
  background: #eff6ff;
  transform: translateY(-2px);
}
.cat-item.selected {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.cat-icon { font-size: 28px; }
.cat-name { font-size: 13px; font-weight: 600; color: #334155; }

/* 选中对勾 */
.check-mark {
  position: absolute;
  top: 8px; right: 10px;
  font-size: 12px;
  font-weight: 700;
  color: #3b82f6;
  opacity: 0;
  transition: opacity 0.15s;
}
.cat-item.selected .check-mark { opacity: 1; }

/* 底部操作栏 */
.ob-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.selected-tip {
  font-size: 13px;
  color: #94a3b8;
}
.selected-tip strong {
  color: #3b82f6;
  font-size: 16px;
}

.ob-btn {
  height: 48px;
  padding: 0 32px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s;
  display: flex;
  align-items: center;
  gap: 8px;
}
.ob-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
}
.ob-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.spin-wrap { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.spin {
  display: inline-block;
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.skip-tip {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: #cbd5e1;
}
.skip-tip span {
  cursor: pointer;
  transition: color 0.2s;
}
.skip-tip span:hover { color: #94a3b8; }

@media (max-width: 600px) {
  .ob-card { padding: 32px 24px; }
  .cat-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
