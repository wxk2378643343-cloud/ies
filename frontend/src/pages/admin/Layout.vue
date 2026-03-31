<template>
  <el-container style="min-height: 100vh;">
    <el-aside width="200px" class="aside">
      <div class="aside-logo">管理后台</div>
      <el-menu router :default-active="$route.path" background-color="#001529" text-color="#ffffffa0"
        active-text-color="#ffffff">
        <el-menu-item index="/admin/dashboard"><el-icon><DataAnalysis /></el-icon>数据看板</el-menu-item>
        <el-menu-item index="/admin/users"><el-icon><User /></el-icon>用户管理</el-menu-item>
        <el-menu-item index="/admin/contents"><el-icon><Document /></el-icon>内容管理</el-menu-item>
        <el-menu-item index="/admin/model"><el-icon><Cpu /></el-icon>模型监控</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="admin-header">
        <span />
        <el-button link @click="auth.logout(); $router.push('/login')">退出登录</el-button>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useAuthStore } from '../../stores/auth'
const auth = useAuthStore()
</script>

<style scoped>
.aside { background: #001529; }
.aside-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid #ffffff20;
}
.admin-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
