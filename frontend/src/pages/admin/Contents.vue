<template>
  <div>
    <h2 class="page-title">内容管理</h2>

    <el-card>
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索标题" clearable
          style="width:200px" @input="onSearch" />
        <el-select v-model="statusFilter" placeholder="全部状态" clearable
          style="width:130px" @change="fetchContents(1)">
          <el-option label="已发布" value="published" />
          <el-option label="草稿"   value="draft" />
          <el-option label="已下架" value="removed" />
        </el-select>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增内容</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe style="width:100%">
        <el-table-column prop="id"       label="ID"   width="60" />
        <el-table-column prop="title"    label="标题" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="80" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发布时间" width="110">
          <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button v-if="row.status !== 'published'" link type="success" size="small"
              @click="updateStatus(row, 'published')">发布</el-button>
            <el-button v-if="row.status === 'published'" link type="warning" size="small"
              @click="updateStatus(row, 'removed')">下架</el-button>
            <el-button link type="danger" size="small"
              @click="updateStatus(row, 'draft')">设为草稿</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination v-if="total > pageSize" style="margin-top:16px"
        :current-page="page" :page-size="pageSize" :total="total"
        layout="prev, pager, next, total" @current-change="fetchContents" />
    </el-card>

    <!-- 新增内容对话框 -->
    <el-dialog v-model="dialogVisible" title="新增内容" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="70px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" style="width:100%">
            <el-option v-for="c in CATEGORIES" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签" prop="tags_json">
          <el-input v-model="form.tags_json" placeholder='如: ["科技","AI"]' />
        </el-form-item>
        <el-form-item label="正文" prop="body">
          <el-input v-model="form.body" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '../../utils/request'

const CATEGORIES = ['科技','体育','娱乐','财经','教育','健康','游戏','旅游']

const list         = ref([])
const total        = ref(0)
const page         = ref(1)
const pageSize     = 20
const loading      = ref(false)
const keyword      = ref('')
const statusFilter = ref('')
let searchTimer = null

const dialogVisible = ref(false)
const submitting    = ref(false)
const formRef       = ref()
const form          = ref({ title: '', category: '', tags_json: '[]', body: '' })
const rules = {
  title:    [{ required: true, message: '请输入标题' }],
  category: [{ required: true, message: '请选择分类' }],
  body:     [{ required: true, message: '请输入正文' }],
}

onMounted(() => fetchContents(1))

async function fetchContents(p = 1) {
  page.value = p
  loading.value = true
  try {
    const params = { page: p, page_size: pageSize }
    if (keyword.value) params.keyword = keyword.value
    const res = await request.get('/api/content/admin/all', { params })
    // 客户端按状态二次过滤（后端没加状态筛选参数，简单处理）
    list.value = statusFilter.value
      ? res.items.filter(i => i.status === statusFilter.value)
      : res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => fetchContents(1), 400)
}

async function updateStatus(row, status) {
  await request.put(`/api/content/${row.id}/status`, null, { params: { status } })
  ElMessage.success('状态已更新')
  fetchContents(page.value)
}

function openCreate() {
  form.value = { title: '', category: '', tags_json: '[]', body: '' }
  dialogVisible.value = true
}

async function submitCreate() {
  await formRef.value.validate()
  submitting.value = true
  try {
    await request.post('/api/content/', form.value)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    fetchContents(1)
  } finally {
    submitting.value = false
  }
}

const STATUS_TYPE  = { published: 'success', draft: 'info', removed: 'danger' }
const STATUS_LABEL = { published: '已发布',  draft: '草稿',  removed: '已下架' }
function statusType(s)  { return STATUS_TYPE[s]  || '' }
function statusLabel(s) { return STATUS_LABEL[s] || s  }
</script>

<style scoped>
.page-title { margin-bottom: 20px; font-size: 18px; color: #303133; }
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
</style>
