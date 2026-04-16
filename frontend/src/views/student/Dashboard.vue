<template>
  <div>
    <h2 style="margin-bottom: 20px">活跃课堂</h2>
    <el-empty v-if="sessions.length === 0" description="暂无活跃课堂" />
    <el-row :gutter="20">
      <el-col :span="8" v-for="session in sessions" :key="session.id">
        <el-card shadow="hover" style="margin-bottom: 20px">
          <template #header>
            <strong>{{ session.course_name }}</strong>
          </template>
          <p>开始时间: {{ session.start_time }}</p>
          <p>刷新间隔: {{ session.refresh_interval }} 分钟</p>
          <p style="margin-top: 10px; font-weight: bold">当前时段: {{ currentSlot(session) }}</p>
          <el-divider />
          <p style="margin-bottom: 10px">选择你的理解程度:</p>
          <div class="emoji-grid">
            <div
              v-for="i in 6"
              :key="i"
              class="emoji-btn"
              :class="{ active: selectedScores[session.id] === i }"
              @click="selectScore(session, i)"
            >
              <span class="emoji-icon">{{ emojis[i - 1] }}</span>
              <span class="emoji-label">{{ labels[i - 1] }}</span>
            </div>
          </div>
          <el-button
            type="primary"
            style="width: 100%; margin-top: 15px"
            :disabled="!selectedScores[session.id]"
            @click="submitReaction(session)"
          >
            提交反馈
          </el-button>
          <el-button style="width: 100%; margin-top: 10px" @click="goDiscussion(session)">
            进入讨论区
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../../api'

const router = useRouter()
const sessions = ref([])
const selectedScores = reactive({})
const emojis = ['😫', '😟', '😐', '🙂', '😊', '🤩']
const labels = ['完全不懂', '不太懂', '一般', '基本理解', '理解', '完全理解']

onMounted(async () => {
  const { data } = await api.get('/feedback/sessions/', { params: { is_active: true } })
  sessions.value = (data.results || data).filter(s => s.is_active)
})

function currentSlot(session) {
  const start = new Date(session.start_time).getTime()
  const now = Date.now()
  return Math.floor((now - start) / (session.refresh_interval * 60 * 1000))
}

function selectScore(session, score) {
  selectedScores[session.id] = score
}

async function submitReaction(session) {
  await api.post('/feedback/submit/', {
    session_id: session.id,
    score: selectedScores[session.id],
    time_slot: currentSlot(session),
  })
  ElMessage.success('反馈提交成功!')
}

function goDiscussion(session) {
  router.push(`/student/discussion/${session.id}`)
}
</script>

<style scoped>
.emoji-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.emoji-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.emoji-btn:hover {
  border-color: #409eff;
}
.emoji-btn.active {
  border-color: #409eff;
  background: #ecf5ff;
}
.emoji-icon {
  font-size: 32px;
}
.emoji-label {
  font-size: 12px;
  margin-top: 4px;
  color: #666;
}
</style>
