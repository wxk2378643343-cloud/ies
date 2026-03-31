<template>
  <el-container style="min-height: 100vh;">
    <!-- 顶部导航 -->
    <el-header class="app-header">
      <span class="logo-text">IES 兴趣演化预测</span>
      <div class="header-right">
        <el-button link :icon="User" @click="$router.push('/profile')">
          {{ auth.user?.username }}
        </el-button>
        <el-button v-if="auth.isAdmin" link @click="$router.push('/admin/dashboard')">
          管理后台
        </el-button>
        <el-button link @click="handleLogout">退出</el-button>
      </div>
    </el-header>

    <el-main class="main-content">

      <!-- 个性化推荐区块 -->
      <section class="section">
        <div class="section-title">
          <el-icon><MagicStick /></el-icon> 为你推荐
          <el-button link size="small" @click="refreshRec" :loading="recLoading" style="margin-left:8px">
            刷新
          </el-button>
        </div>
        <el-row :gutter="16" v-loading="recLoading">
          <el-col v-for="item in recList" :key="item.id" :xs="24" :sm="12" :md="8" :lg="6">
            <el-card class="content-card rec-card" shadow="hover" @click="goDetail(item)">
              <el-tag size="small" :type="tagType(item.category)" style="margin-bottom:8px">
                {{ item.category }}
              </el-tag>
              <h3 class="card-title">{{ item.title }}</h3>
              <p class="card-date">{{ formatDate(item.created_at) }}</p>
            </el-card>
          </el-col>
        </el-row>
        <el-empty v-if="!recLoading && recList.length === 0" description="暂无推荐，浏览更多内容后再来" />
      </section>

      <el-divider />

      <!-- 全部内容区块 -->
      <section class="section">
        <div class="section-title"><el-icon><List /></el-icon> 全部内容</div>
        <!-- 筛选栏 -->
        <div class="filter-bar">
          <el-input v-model="keyword" placeholder="搜索内容..." clearable style="width:240px" @input="onSearch" />
          <el-select v-model="category" placeholder="全部分类" clearable style="width:140px" @change="fetchList(1)">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </div>

        <el-row :gutter="16" v-loading="loading">
          <el-col v-for="item in list" :key="item.id" :xs="24" :sm="12" :md="8" :lg="6">
            <el-card class="content-card" shadow="hover" @click="goDetail(item)">
              <el-tag size="small" :type="tagType(item.category)" style="margin-bottom:8px">
                {{ item.category }}
              </el-tag>
              <h3 class="card-title">{{ item.title }}</h3>
              <p class="card-date">{{ formatDate(item.created_at) }}</p>
            </el-card>
          </el-col>
        </el-row>
        <el-empty v-if="!loading && list.length === 0" description="暂无内容" />

        <el-pagination v-if="total > pageSize" class="pagination"
          :current-page="page" :page-size="pageSize" :total="total"
          layout="prev, pager, next" @current-change="fetchList" />
      </section>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, MagicStick, List } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import request from '../utils/request'

const router = useRouter()
const auth = useAuthStore()

// 推荐
const recList = ref([])
const recLoading = ref(false)

// 全部内容
const list = ref([])
const categories = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const loading = ref(false)
const keyword = ref('')
const category = ref('')

let searchTimer = null

onMounted(async () => {
  const cats = await request.get('/api/content/categories')
  categories.value = cats
  await Promise.all([fetchRec(), fetchList(1)])
})

async function fetchRec() {
  recLoading.value = true
  try {
    recList.value = await request.get('/api/recommend', { params: { top_n: 8 } })
  } catch {
    recList.value = []
  } finally {
    recLoading.value = false
  }
}

function refreshRec() {
  fetchRec()
}

async function fetchList(p = 1) {
  page.value = p
  loading.value = true
  try {
    const params = { page: p, page_size: pageSize }
    if (keyword.value) params.keyword = keyword.value
    if (category.value) params.category = category.value
    const res = await request.get('/api/content/list', { params })
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => fetchList(1), 400)
}

async function goDetail(item) {
  // 先上报 click 行为，再跳转
  await request.post('/api/behavior/report', { content_id: item.id, action: 'click' })
  router.push(`/content/${item.id}`)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

function formatDate(iso) {
  return iso ? iso.slice(0, 10) : ''
}

const TAG_TYPES = ['', 'success', 'warning', 'danger', 'info']
function tagType(cat) {
  const idx = ['科技','体育','娱乐','财经','教育','健康','游戏','旅游'].indexOf(cat)
  return TAG_TYPES[idx % TAG_TYPES.length] || ''
}
</script>

<style scoped>
.app-header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 10;
}
.logo-text {
  font-weight: 700;
  font-size: 18px;
  color: #409eff;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
.section {
  margin-bottom: 8px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.rec-card {
  border: 1px solid #c6e2ff;
}
.content-card {
  cursor: pointer;
  margin-bottom: 16px;
  border-radius: 8px;
  transition: transform 0.2s;
}
.content-card:hover {
  transform: translateY(-2px);
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-date {
  font-size: 12px;
  color: #909399;
}
.pagination {
  margin-top: 24px;
  justify-content: center;
}
</style>
