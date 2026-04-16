<template>
  <div>
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="12"><h2>我的课程</h2></el-col>
      <el-col :span="12" style="text-align: right">
        <el-button type="primary" @click="showCourseDialog = true">新建课程</el-button>
      </el-col>
    </el-row>

    <el-table :data="courses" border style="margin-bottom: 30px">
      <el-table-column prop="name" label="课程名称" />
      <el-table-column label="操作" width="250">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="startSession(row)">开始上课</el-button>
        </template>
      </el-table-column>
    </el-table>

    <h2 style="margin-bottom: 15px">进行中的课堂</h2>
    <el-empty v-if="activeSessions.length === 0" description="暂无进行中的课堂" />
    <el-row :gutter="20">
      <el-col :span="12" v-for="session in activeSessions" :key="session.id">
        <el-card shadow="hover" style="margin-bottom: 20px">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <strong>{{ session.course_name }}</strong>
              <div>
                <el-button size="small" type="primary" @click="viewStats(session)">查看统计</el-button>
                <el-button size="small" @click="goDiscussion(session)">讨论区</el-button>
                <el-button size="small" type="danger" @click="endSession(session)">结束</el-button>
              </div>
            </div>
          </template>
          <p>开始时间: {{ new Date(session.start_time).toLocaleString('zh-CN') }}</p>
          <p>刷新间隔: {{ session.refresh_interval }} 分钟</p>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showCourseDialog" title="新建课程" width="400px">
      <el-form :model="courseForm">
        <el-form-item label="课程名称">
          <el-input v-model="courseForm.name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCourseDialog = false">取消</el-button>
        <el-button type="primary" @click="createCourse">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showSessionDialog" title="开始上课" width="400px">
      <el-form :model="sessionForm">
        <el-form-item label="刷新间隔(分钟)">
          <el-input-number v-model="sessionForm.refresh_interval" :min="1" :max="30" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSessionDialog = false">取消</el-button>
        <el-button type="primary" @click="createSession">开始</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const router = useRouter()
const courses = ref([])
const activeSessions = ref([])
const showCourseDialog = ref(false)
const showSessionDialog = ref(false)
const courseForm = reactive({ name: '' })
const sessionForm = reactive({ course_id: null, refresh_interval: 5 })

onMounted(loadData)

async function loadData() {
  const [c, s] = await Promise.all([
    api.get('/feedback/courses/'),
    api.get('/feedback/sessions/'),
  ])
  courses.value = c.data.results || c.data
  activeSessions.value = (s.data.results || s.data).filter(s => s.is_active)
}

async function createCourse() {
  await api.post('/feedback/courses/', courseForm)
  ElMessage.success('课程创建成功')
  showCourseDialog.value = false
  courseForm.name = ''
  loadData()
}

function startSession(course) {
  sessionForm.course_id = course.id
  showSessionDialog.value = true
}

async function createSession() {
  await api.post('/feedback/sessions/', {
    course: sessionForm.course_id,
    start_time: new Date().toISOString(),
    refresh_interval: sessionForm.refresh_interval,
  })
  ElMessage.success('课堂已开始')
  showSessionDialog.value = false
  loadData()
}

async function endSession(session) {
  await ElMessageBox.confirm('确定结束这个课堂？', '提示')
  await api.post(`/feedback/sessions/${session.id}/end/`)
  ElMessage.success('课堂已结束')
  loadData()
}

function viewStats(session) {
  router.push(`/teacher/statistics/${session.id}`)
}

function goDiscussion(session) {
  router.push(`/teacher/discussion/${session.id}`)
}
</script>
