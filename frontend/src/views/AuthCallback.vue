<template>
  <div class="callback-container">
    <!-- 正在加载 -->
    <el-card v-if="!needBind" class="callback-card">
      <div style="text-align: center">
        <el-icon :size="32" class="is-loading" style="color: #409eff"><Loading /></el-icon>
        <p style="margin-top: 16px; color: #606266">正在处理 GitHub 登录...</p>
      </div>
    </el-card>

    <!-- 绑定已有账号 -->
    <el-card v-else class="callback-card">
      <template #header>
        <div style="text-align: center">
          <h3 style="margin: 0">关联系统账号</h3>
          <p style="margin: 8px 0 0; color: #909399; font-size: 13px">
            GitHub 账号 <strong>{{ githubName }}</strong> 尚未关联系统用户，请输入已有账号进行绑定
          </p>
        </div>
      </template>
      <el-form :model="bindForm" :rules="bindRules" ref="bindFormRef" label-width="0">
        <el-form-item prop="username">
          <el-input v-model="bindForm.username" placeholder="用户名" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="bindForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleBind"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width: 100%" :loading="bindLoading" @click="handleBind">
            绑定并登录
          </el-button>
        </el-form-item>
      </el-form>
      <div style="text-align: center">
        <el-button link type="info" @click="$router.replace('/login')">返回登录页</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import api from '../api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const needBind = ref(false)
const githubId = ref(null)
const githubName = ref('')
const bindLoading = ref(false)
const bindFormRef = ref()

const bindForm = reactive({ username: '', password: '' })
const bindRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

onMounted(async () => {
  const code = route.query.code
  if (!code) {
    ElMessage.error('授权失败：未收到授权码')
    router.replace('/login')
    return
  }

  try {
    const { data } = await api.post('/auth/github/', { code })

    if (data.need_bind) {
      // 未关联 — 显示绑定表单
      needBind.value = true
      githubId.value = data.github_id
      githubName.value = data.github_name
    } else {
      // 已关联 — 直接登录
      userStore.setAuth(data.user, data.access, data.refresh)
      ElMessage.success('GitHub 登录成功')
      router.replace(`/${data.user.role}`)
    }
  } catch (e) {
    const resp = e.response?.data
    const detail = (resp && typeof resp === 'object' && resp.detail) ? resp.detail : 'GitHub 登录失败，请检查网络后重试'
    ElMessage.error(detail)
    router.replace('/login')
  }
})

async function handleBind() {
  await bindFormRef.value.validate()
  bindLoading.value = true
  try {
    const { data } = await api.post('/auth/github/bind/', {
      github_id: githubId.value,
      username: bindForm.username,
      password: bindForm.password,
    })
    userStore.setAuth(data.user, data.access, data.refresh)
    ElMessage.success('绑定成功')
    router.replace(`/${data.user.role}`)
  } catch (e) {
    const resp = e.response?.data
    const detail = (resp && typeof resp === 'object' && resp.detail) ? resp.detail : '绑定失败'
    ElMessage.error(detail)
  } finally {
    bindLoading.value = false
  }
}
</script>

<style scoped>
.callback-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.callback-card {
  width: 400px;
}
</style>
