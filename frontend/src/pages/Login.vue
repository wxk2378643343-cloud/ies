<template>
  <div class="page">

    <!-- 左侧品牌面板 -->
    <div class="left-panel">
      <div class="deco deco-a"></div>
      <div class="deco deco-b"></div>
      <div class="deco deco-c"></div>

      <div class="left-inner">
        <div class="brand">
          <div class="brand-logo">✦</div>
          <span class="brand-name">IES</span>
        </div>

        <h1 class="left-title">欢迎回来</h1>
        <p class="left-desc">
          基于注意力机制的<br>用户兴趣演化分析与预测系统
        </p>

        <ul class="feature-list">
          <li><span class="fi">🎯</span> 个性化内容推荐</li>
          <li><span class="fi">📈</span> 兴趣演化趋势可视化</li>
          <li><span class="fi">🤖</span> LSTM + Self-Attention 模型</li>
        </ul>
      </div>
    </div>

    <!-- 右侧表单面板 -->
    <div class="right-panel">
      <div class="form-box">
        <h2 class="form-title">登录账号</h2>
        <p class="form-sub">请输入您的邮箱与密码</p>

        <el-form :model="form" :rules="rules" ref="formRef" label-width="0">
          <div class="field">
            <label class="field-label">邮箱</label>
            <el-form-item prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱地址" size="large" />
            </el-form-item>
          </div>

          <div class="field">
            <label class="field-label">密码</label>
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="请输入密码"
                show-password size="large" @keyup.enter="submit" />
            </el-form-item>
          </div>

          <!-- 记住我 -->
          <div class="remember-row">
            <label class="remember-label">
              <input type="checkbox" v-model="remember" class="remember-check" />
              <span>记住密码</span>
            </label>
          </div>

          <button class="submit-btn" :disabled="loading" @click.prevent="submit">
            <span v-if="!loading">登 录</span>
            <span v-else class="spin-wrap">
              <i class="spin"></i> 登录中...
            </span>
          </button>
        </el-form>

        <p class="switch-tip">
          还没有账号？
          <router-link to="/register" class="switch-link">立即注册 →</router-link>
        </p>

        <!-- 测试账号小注 -->
        <div class="hint-box">
          <p class="hint-title">· 测试账号</p>
          <div class="hint-row">
            <span class="hint-badge admin">管理员</span>
            <span class="hint-text" @click="fillAdmin">admin@ies.com &nbsp;/&nbsp; admin123</span>
          </div>
          <div class="hint-row">
            <span class="hint-badge user">普通用户</span>
            <span class="hint-text" @click="fillUser">user01@ies.com &nbsp;/&nbsp; password123</span>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import request from '../utils/request'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref()
const loading = ref(false)
const remember = ref(false)

// 读取已保存的账号密码
const saved = JSON.parse(localStorage.getItem('saved_login') || 'null')
const form = ref({
  email:    saved?.email    || '',
  password: saved?.password || '',
})
if (saved) remember.value = true

const rules = {
  email:    [{ required: true, type: 'email', message: '请输入有效邮箱', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
}

function fillAdmin() {
  form.value.email = 'admin@ies.com'
  form.value.password = 'admin123'
}
function fillUser() {
  form.value.email = 'user01@ies.com'
  form.value.password = 'password123'
}

async function submit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await auth.login(form.value.email, form.value.password)
    if (remember.value) {
      localStorage.setItem('saved_login', JSON.stringify({
        email: form.value.email, password: form.value.password,
      }))
    } else {
      localStorage.removeItem('saved_login')
    }
    if (auth.isAdmin) {
      router.push('/admin/dashboard')
    } else {
      const { has_interests } = await request.get('/api/recommend/has_interests')
      router.push(has_interests ? '/' : '/onboarding')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ── 整体布局 ─────────────────────────────── */
.page {
  display: flex;
  min-height: 100vh;
}

/* ── 左侧 ────────────────────────────────── */
.left-panel {
  position: relative;
  width: 52%;
  background: linear-gradient(145deg, #0f1b3d 0%, #1a3a6b 55%, #1e5fa8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* 装饰圆 */
.deco {
  position: absolute;
  border-radius: 50%;
  opacity: 0.12;
}
.deco-a {
  width: 420px; height: 420px;
  background: #5b9cf6;
  top: -120px; right: -100px;
}
.deco-b {
  width: 280px; height: 280px;
  background: #93c5fd;
  bottom: -60px; left: -80px;
}
.deco-c {
  width: 160px; height: 160px;
  background: #fff;
  bottom: 120px; right: 60px;
}

.left-inner {
  position: relative;
  z-index: 1;
  padding: 48px;
  color: #fff;
  max-width: 400px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 48px;
}
.brand-logo {
  width: 40px; height: 40px;
  background: rgba(255,255,255,0.15);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  backdrop-filter: blur(4px);
}
.brand-name {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 4px;
  color: #fff;
}

.left-title {
  font-size: 40px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 16px;
  color: #fff;
}
.left-desc {
  font-size: 15px;
  line-height: 1.8;
  color: rgba(255,255,255,0.65);
  margin-bottom: 40px;
}

.feature-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.feature-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: rgba(255,255,255,0.8);
  background: rgba(255,255,255,0.07);
  padding: 12px 18px;
  border-radius: 10px;
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255,255,255,0.1);
}
.fi { font-size: 18px; }

/* ── 右侧 ────────────────────────────────── */
.right-panel {
  flex: 1;
  background: #f7f8fc;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-box {
  width: 360px;
  padding: 48px 40px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 8px 40px rgba(15, 27, 61, 0.08);
}

.form-title {
  font-size: 26px;
  font-weight: 700;
  color: #0f1b3d;
  margin-bottom: 6px;
}
.form-sub {
  font-size: 14px;
  color: #94a3b8;
  margin-bottom: 32px;
}

/* 表单字段 */
.field {
  margin-bottom: 4px;
}
.field-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
  letter-spacing: 0.3px;
}

/* 覆盖 Element Plus 输入框样式 */
:deep(.el-form-item) {
  margin-bottom: 20px;
}
:deep(.el-form-item__error) {
  font-size: 12px;
}
:deep(.el-input__wrapper) {
  border-radius: 10px !important;
  border: 1.5px solid #e2e8f0 !important;
  box-shadow: none !important;
  background: #f8faff !important;
  padding: 0 14px !important;
  height: 48px;
  transition: border-color 0.2s, background 0.2s;
}
:deep(.el-input__wrapper:hover) {
  border-color: #93c5fd !important;
}
:deep(.el-input__wrapper.is-focus) {
  border-color: #3b82f6 !important;
  background: #fff !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}
:deep(.el-input__inner) {
  font-size: 14px !important;
  color: #1e293b !important;
}
:deep(.el-input__inner::placeholder) {
  color: #cbd5e1 !important;
}

/* 提交按钮 */
.submit-btn {
  width: 100%;
  height: 50px;
  margin-top: 8px;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 3px;
  cursor: pointer;
  transition: all 0.25s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(59, 130, 246, 0.38);
}
.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}
.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* loading 动画 */
.spin-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  letter-spacing: 1px;
}
.spin {
  display: inline-block;
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 底部跳转 */
.switch-tip {
  text-align: center;
  margin-top: 24px;
  font-size: 13px;
  color: #94a3b8;
}
.switch-link {
  color: #3b82f6;
  font-weight: 600;
  transition: color 0.2s;
}
.switch-link:hover { color: #2563eb; }

/* 记住我 */
.remember-row {
  margin-bottom: 16px;
}
.remember-label {
  display: flex;
  align-items: center;
  gap: 7px;
  cursor: pointer;
  font-size: 13px;
  color: #64748b;
  user-select: none;
}
.remember-check {
  width: 15px;
  height: 15px;
  accent-color: #3b82f6;
  cursor: pointer;
}

/* 测试账号小注 */
.hint-box {
  margin-top: 20px;
  padding: 12px 14px;
  background: #f8faff;
  border: 1px dashed #c7d9f8;
  border-radius: 10px;
}
.hint-title {
  font-size: 11px;
  color: #94a3b8;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}
.hint-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.hint-row:last-child { margin-bottom: 0; }
.hint-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  flex-shrink: 0;
  letter-spacing: 0.3px;
}
.hint-badge.admin {
  background: #fef3c7;
  color: #92400e;
}
.hint-badge.user {
  background: #dbeafe;
  color: #1e40af;
}
.hint-text {
  font-size: 12px;
  color: #64748b;
  font-family: 'Courier New', monospace;
  cursor: pointer;
  transition: color 0.15s;
}
.hint-text:hover { color: #3b82f6; }

/* ── 移动端：隐藏左侧 ───────────────────── */
@media (max-width: 768px) {
  .left-panel { display: none; }
  .right-panel { background: linear-gradient(145deg, #0f1b3d, #1a3a6b); }
  .form-box { width: 320px; padding: 36px 28px; }
}
</style>
