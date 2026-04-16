<template>
  <div class="discussion-container">
    <el-page-header @back="$router.back()" content="讨论区" style="margin-bottom: 20px" />
    <div class="chat-box" ref="chatBox">
      <div v-for="msg in messages" :key="msg.id" class="chat-msg" :class="{ mine: msg.sender === userStore.user?.id }">
        <div class="msg-header">
          <el-tag :type="msg.sender_role === 'teacher' ? 'danger' : 'info'" size="small">
            {{ msg.sender_role === 'teacher' ? '教师' : '学生' }}
          </el-tag>
          <span class="msg-name">{{ msg.sender_name || '匿名' }}</span>
          <span class="msg-time">{{ formatTime(msg.created_at) }}</span>
        </div>
        <div class="msg-content">
          {{ msg.content }}
          <el-image v-if="msg.image_url" :src="msg.image_url" style="max-width: 300px; margin-top: 8px" fit="contain" :preview-src-list="[msg.image_url]" />
        </div>
      </div>
    </div>
    <div class="chat-input">
      <el-input v-model="newMessage" placeholder="输入消息..." @keyup.enter="sendMessage" />
      <el-upload :show-file-list="false" :before-upload="handleUpload" accept="image/*">
        <el-button>图片</el-button>
      </el-upload>
      <el-button type="primary" @click="sendMessage" :disabled="!newMessage.trim()">发送</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { ElMessage } from 'element-plus'
import api from '../../api'
import { createWebSocket } from '../../utils/websocket'

const route = useRoute()
const userStore = useUserStore()
const sessionId = route.params.sessionId
const messages = ref([])
const newMessage = ref('')
const chatBox = ref(null)
let ws = null

onMounted(async () => {
  const { data } = await api.get(`/discussion/messages/${sessionId}/`)
  messages.value = data.results || data
  ws = createWebSocket(`/ws/chat/${sessionId}/`, (data) => {
    messages.value.push(data)
    scrollToBottom()
  })
  scrollToBottom()
})

onUnmounted(() => { if (ws) ws.close() })

function sendMessage() {
  if (!newMessage.value.trim() || !ws) return
  ws.send(JSON.stringify({ content: newMessage.value }))
  newMessage.value = ''
}

async function handleUpload(file) {
  const formData = new FormData()
  formData.append('session', sessionId)
  formData.append('image', file)
  formData.append('content', '')
  await api.post('/discussion/send/', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
  ElMessage.success('图片已发送')
  return false
}

function scrollToBottom() {
  nextTick(() => { if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight })
}

function formatTime(t) { return new Date(t).toLocaleTimeString('zh-CN') }
</script>

<style scoped>
.discussion-container { display: flex; flex-direction: column; height: calc(100vh - 120px); }
.chat-box { flex: 1; overflow-y: auto; border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; background: #fff; }
.chat-msg { margin-bottom: 16px; }
.chat-msg.mine { text-align: right; }
.msg-header { margin-bottom: 4px; display: flex; align-items: center; gap: 8px; }
.chat-msg.mine .msg-header { justify-content: flex-end; }
.msg-name { font-weight: bold; font-size: 13px; }
.msg-time { font-size: 12px; color: #999; }
.msg-content { display: inline-block; background: #f0f2f5; padding: 8px 12px; border-radius: 8px; max-width: 70%; text-align: left; }
.chat-msg.mine .msg-content { background: #ecf5ff; }
.chat-input { display: flex; gap: 10px; margin-top: 12px; }
</style>
