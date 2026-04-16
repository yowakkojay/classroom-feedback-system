<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2 style="text-align: center; margin: 0">课堂学情监控系统</h2>
      </template>

      <el-tabs v-model="activeTab" stretch>
        <!-- 密码登录 -->
        <el-tab-pane label="密码登录" name="password">
          <el-form :model="form" :rules="rules" ref="formRef" label-width="0">
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password @keyup.enter="handleLogin" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="handleLogin">登 录</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 第三方登录 -->
        <el-tab-pane label="第三方登录" name="oauth">
          <div class="oauth-section">
            <p style="color: #909399; text-align: center; margin-bottom: 20px">使用第三方账号快速登录</p>
            <el-button class="oauth-btn github-btn" size="large" @click="loginWithGithub">
              <svg viewBox="0 0 16 16" width="20" height="20" style="margin-right: 8px; fill: #fff"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
              GitHub 登录
            </el-button>
            <el-button class="oauth-btn wechat-btn" size="large" disabled>
              微信登录（暂未开放）
            </el-button>
            <el-button class="oauth-btn qq-btn" size="large" disabled>
              QQ 登录（暂未开放）
            </el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import api from '../api'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const activeTab = ref('password')

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const GITHUB_CLIENT_ID = 'REDACTED_GITHUB_ID'

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    const { data } = await api.post('/auth/login/', form)
    userStore.setAuth(data.user, data.access, data.refresh)
    router.push(`/${data.user.role}`)
  } finally {
    loading.value = false
  }
}

function loginWithGithub() {
  const redirectUri = `${window.location.origin}/auth/callback/github`
  const url = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=user:email`
  window.location.href = url
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 420px;
}
.oauth-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px 0;
}
.oauth-btn {
  width: 100%;
  color: #fff;
  font-size: 15px;
}
.github-btn {
  background: #24292e;
  border-color: #24292e;
}
.github-btn:hover {
  background: #2f363d;
  border-color: #2f363d;
}
.wechat-btn {
  background: #07c160;
  border-color: #07c160;
}
.qq-btn {
  background: #12b7f5;
  border-color: #12b7f5;
}
</style>
