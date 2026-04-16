<template>
  <div>
    <h2 style="margin-bottom: 20px">历史查询</h2>
    <el-form inline>
      <el-form-item label="课程名称">
        <el-input v-model="query.course_name" placeholder="搜索课程" clearable />
      </el-form-item>
      <el-form-item label="日期范围">
        <el-date-picker v-model="dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="search">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="results" border style="margin-top: 20px">
      <el-table-column prop="session.course_name" label="课程" />
      <el-table-column label="开始时间">
        <template #default="{ row }">{{ new Date(row.session.start_time).toLocaleString('zh-CN') }}</template>
      </el-table-column>
      <el-table-column label="结束时间">
        <template #default="{ row }">{{ row.session.end_time ? new Date(row.session.end_time).toLocaleString('zh-CN') : '进行中' }}</template>
      </el-table-column>
      <el-table-column prop="total_students" label="参与人数" width="100" />
      <el-table-column prop="average" label="平均分" width="100" />
      <el-table-column prop="variance" label="方差" width="100" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="$router.push(`/teacher/statistics/${row.session.id}`)">详细统计</el-button>
          <el-button size="small" type="success" @click="exportExcel(row.session.id)">导出</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import api from '../../api'

const query = reactive({ course_name: '' })
const dateRange = ref(null)
const results = ref([])

async function search() {
  const params = { course_name: query.course_name }
  if (dateRange.value) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  const { data } = await api.get('/feedback/history/', { params })
  results.value = data
}

async function exportExcel(sessionId) {
  const response = await api.get(`/feedback/export/${sessionId}/`, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `session_${sessionId}.xlsx`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
</script>
