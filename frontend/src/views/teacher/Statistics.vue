<template>
  <div>
    <el-page-header @back="$router.back()" style="margin-bottom: 20px">
      <template #content>课堂统计</template>
    </el-page-header>

    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="6"><el-statistic title="参与人数" :value="stats.total_students" /></el-col>
      <el-col :span="6"><el-statistic title="平均分" :value="stats.average" :precision="2" /></el-col>
      <el-col :span="6"><el-statistic title="方差" :value="stats.variance" :precision="2" /></el-col>
      <el-col :span="6"><el-statistic title="当前时段" :value="currentTimeSlot" /></el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>各分数段人数分布 (柱状图)</template>
          <div ref="barChartRef" style="height: 350px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>各分数段比例 (饼状图)</template>
          <div ref="pieChartRef" style="height: 350px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <template #header>各时段平均分趋势</template>
      <div ref="lineChartRef" style="height: 300px"></div>
    </el-card>

    <div style="margin-top: 20px; text-align: right">
      <el-button type="success" @click="exportExcel">导出Excel</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import api from '../../api'
import { createWebSocket } from '../../utils/websocket'

const route = useRoute()
const sessionId = route.params.sessionId
const barChartRef = ref(null)
const pieChartRef = ref(null)
const lineChartRef = ref(null)
let barChart, pieChart, lineChart
let ws = null
let interval = null

const emojis = ['😫', '😟', '😐', '🙂', '😊', '🤩']
const labels = ['完全不懂', '不太懂', '一般', '基本理解', '理解', '完全理解']

const stats = reactive({
  total_students: 0, average: 0, variance: 0,
  distribution: { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0 },
})
const currentTimeSlot = ref(0)
const slotsData = ref([])

onMounted(async () => {
  barChart = echarts.init(barChartRef.value)
  pieChart = echarts.init(pieChartRef.value)
  lineChart = echarts.init(lineChartRef.value)

  await loadStats()
  await loadSlots()

  ws = createWebSocket(`/ws/feedback/${sessionId}/`, (data) => {
    if (data.type === 'statistics') {
      Object.assign(stats, data.data)
      updateCharts()
    }
  })

  interval = setInterval(async () => {
    await loadStats()
    await loadSlots()
  }, 30000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
  if (ws) ws.close()
  barChart?.dispose()
  pieChart?.dispose()
  lineChart?.dispose()
})

async function loadStats() {
  const { data } = await api.get(`/feedback/statistics/${sessionId}/`)
  Object.assign(stats, data)
  updateCharts()
}

async function loadSlots() {
  const { data } = await api.get(`/feedback/statistics/${sessionId}/slots/`)
  slotsData.value = data
  if (data.length > 0) currentTimeSlot.value = data[data.length - 1].time_slot
  updateLineChart()
}

function updateCharts() {
  const dist = stats.distribution
  const values = [1, 2, 3, 4, 5, 6].map(i => dist[String(i)] || 0)
  const colors = ['#f56c6c', '#e6a23c', '#909399', '#67c23a', '#409eff', '#6f42c1']

  barChart.setOption({
    xAxis: { type: 'category', data: labels.map((l, i) => `${i + 1}分\n${emojis[i]}`) },
    yAxis: { type: 'value', name: '人数' },
    series: [{ type: 'bar', data: values, itemStyle: { color: (p) => colors[p.dataIndex] } }],
    tooltip: { trigger: 'axis' },
  })

  const pieData = labels.map((l, i) => ({ name: `${i + 1}分 ${l}`, value: values[i] })).filter(d => d.value > 0)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{ type: 'pie', radius: ['40%', '70%'], data: pieData, emphasis: { itemStyle: { shadowBlur: 10 } } }],
  })
}

function updateLineChart() {
  if (!slotsData.value.length) return
  lineChart.setOption({
    xAxis: { type: 'category', data: slotsData.value.map(s => `时段${s.time_slot}`) },
    yAxis: { type: 'value', name: '平均分', min: 0, max: 6 },
    series: [{ type: 'line', data: slotsData.value.map(s => s.average), smooth: true, markLine: { data: [{ type: 'average', name: '总平均' }] } }],
    tooltip: { trigger: 'axis' },
  })
}

async function exportExcel() {
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
