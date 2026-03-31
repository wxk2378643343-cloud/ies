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

        <h1 class="left-title">加入我们</h1>
        <p class="left-desc">
          创建账号，开启你的<br>个性化内容探索之旅
        </p>

        <div class="step-list">
          <div class="step">
            <div class="step-num">01</div>
            <div>
              <div class="step-title">注册账号</div>
              <div class="step-desc">填写基本信息完成注册</div>
            </div>
          </div>
          <div class="step-line"></div>
          <div class="step">
            <div class="step-num">02</div>
            <div>
              <div class="step-title">浏览内容</div>
              <div class="step-desc">系统自动记录兴趣偏好</div>
            </div>
          </div>
          <div class="step-line"></div>
          <div class="step">
            <div class="step-num">03</div>
            <div>
              <div class="step-title">获取推荐</div>
              <div class="step-desc">AI 驱动的个性化推荐</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧表单面板 -->
    <div class="right-panel">
      <div class="form-box">
        <h2 class="form-title">创建账号</h2>
        <p class="form-sub">填写以下信息完成注册</p>

        <el-form :model="form" :rules="rules" ref="formRef" label-width="0">
          <div class="field">
            <label class="field-label">用户名</label>
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="请输入用户名（2-20位）" size="large" />
            </el-form-item>
          </div>

          <div class="field">
            <label class="field-label">邮箱</label>
            <el-form-item prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱地址" size="large" />
            </el-form-item>
          </div>

          <div class="field">
            <label class="field-label">密码</label>
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="请输入密码（至少 6 位）"
                show-password size="large" @keyup.enter="submit" />
            </el-form-item>
          </div>

          <button class="submit-btn" :disabled="loading" @click.prevent="submit">
            <span v-if="!loading">注 册</span>
            <span v-else class="spin-wrap">
              <i class="spin"></i> 注册中...
            </span>
          </button>
        </el-form>

        <p class="switch-tip">
          已有账号？
          <router-link to="/login" class="switch-link">返回登录 →</router-link>
        </p>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref()
const loading = ref(false)
const form = ref({ username: '', email: '', password: '' })

const rules = {
  username: [{ required: true, min: 2, max: 20, message: '用户名 2-20 位', trigger: 'blur' }],
  email:    [{ required: true, type: 'email', message: '请输入有效邮箱', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
}

async function submit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await auth.register(form.value.username, form.value.email, form.value.password)
    router.push('/onboarding')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
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
.deco {
  position: absolute;
  border-radius: 50%;
  opacity: 0.12;
}
.deco-a { width: 380px; height: 380px; background: #5b9cf6; top: -100px; right: -80px; }
.deco-b { width: 250px; height: 250px; background: #93c5fd; bottom: -50px; left: -60px; }
.deco-c { width: 140px; height: 140px; background: #fff; bottom: 100px; right: 80px; }

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
}
.brand-name {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 4px;
}
.left-title {
  font-size: 40px;
  font-weight: 700;
  margin-bottom: 14px;
}
.left-desc {
  font-size: 15px;
  line-height: 1.8;
  color: rgba(255,255,255,0.6);
  margin-bottom: 44px;
}

/* 步骤引导 */
.step-list {
  display: flex;
  flex-direction: column;
}
.step {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}
.step-num {
  width: 36px; height: 36px;
  background: rgba(255,255,255,0.15);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid rgba(255,255,255,0.2);
}
.step-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 2px;
}
.step-desc {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
}
.step-line {
  width: 1px;
  height: 20px;
  background: rgba(255,255,255,0.2);
  margin-left: 17px;
}

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
  padding: 44px 40px;
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
  margin-bottom: 28px;
}
.field { margin-bottom: 4px; }
.field-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
  letter-spacing: 0.3px;
}

:deep(.el-form-item) { margin-bottom: 18px; }
:deep(.el-form-item__error) { font-size: 12px; }
:deep(.el-input__wrapper) {
  border-radius: 10px !important;
  border: 1.5px solid #e2e8f0 !important;
  box-shadow: none !important;
  background: #f8faff !important;
  padding: 0 14px !important;
  height: 48px;
  transition: border-color 0.2s, background 0.2s;
}
:deep(.el-input__wrapper:hover) { border-color: #93c5fd !important; }
:deep(.el-input__wrapper.is-focus) {
  border-color: #3b82f6 !important;
  background: #fff !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}
:deep(.el-input__inner) { font-size: 14px !important; color: #1e293b !important; }
:deep(.el-input__inner::placeholder) { color: #cbd5e1 !important; }

.submit-btn {
  width: 100%;
  height: 50px;
  margin-top: 6px;
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
.submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.spin-wrap { display: flex; align-items: center; gap: 8px; font-size: 14px; letter-spacing: 1px; }
.spin {
  display: inline-block;
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.switch-tip { text-align: center; margin-top: 22px; font-size: 13px; color: #94a3b8; }
.switch-link { color: #3b82f6; font-weight: 600; transition: color 0.2s; }
.switch-link:hover { color: #2563eb; }

@media (max-width: 768px) {
  .left-panel { display: none; }
  .right-panel { background: linear-gradient(145deg, #0f1b3d, #1a3a6b); }
  .form-box { width: 320px; padding: 36px 28px; }
}
</style>
