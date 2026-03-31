<template>
  <div>
    <h2 class="page-title">用户管理</h2>

    <el-card>
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索用户名或邮箱" clearable
          style="width:240px" @input="onSearch" />
      </div>

      <el-table :data="users" v-loading="loading" stripe style="width:100%">
        <el-table-column prop="id"       label="ID"   width="60" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email"    label="邮箱" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间">
          <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              v-if="row.role !== 'admin'"
              link type="primary" size="small"
              @click="setRole(row, 'admin')"
            >设为管理员</el-button>
            <el-button
              v-else
              link type="warning" size="small"
              @click="setRole(row, 'user')"
            >撤销管理员</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        style="margin-top:16px"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, total"
        @current-change="fetchUsers"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const users    = ref([])
const total    = ref(0)
const page     = ref(1)
const pageSize = 20
const loading  = ref(false)
const keyword  = ref('')
let searchTimer = null

onMounted(() => fetchUsers(1))

async function fetchUsers(p = 1) {
  page.value = p
  loading.value = true
  try {
    const res = await request.get('/api/admin/users', {
      params: { page: p, page_size: pageSize, keyword: keyword.value },
    })
    users.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => fetchUsers(1), 400)
}

async function setRole(row, role) {
  const label = role === 'admin' ? '设为管理员' : '撤销管理员权限'
  await ElMessageBox.confirm(`确认对用户「${row.username}」${label}？`, '提示', { type: 'warning' })
  await request.put(`/api/admin/users/${row.id}/role`, null, { params: { role } })
  ElMessage.success('操作成功')
  fetchUsers(page.value)
}
</script>

<style scoped>
.page-title { margin-bottom: 20px; font-size: 18px; color: #303133; }
.toolbar { margin-bottom: 16px; }
</style>
