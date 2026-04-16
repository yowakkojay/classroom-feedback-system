<template>
  <div>
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-input v-model="keyword" placeholder="搜索用户名/姓名/手机" clearable @clear="loadUsers" @keyup.enter="loadUsers" />
      </el-col>
      <el-col :span="4">
        <el-select v-model="roleFilter" placeholder="筛选角色" clearable @change="loadUsers">
          <el-option label="学生" value="student" />
          <el-option label="教师" value="teacher" />
          <el-option label="管理员" value="admin" />
        </el-select>
      </el-col>
      <el-col :span="4">
        <el-button type="primary" @click="loadUsers">搜索</el-button>
        <el-button type="success" @click="openAdd">添加用户</el-button>
      </el-col>
    </el-row>

    <el-table :data="users" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column label="姓名">
        <template #default="{ row }">{{ row.last_name }}{{ row.first_name }}</template>
      </el-table-column>
      <el-table-column prop="role" label="角色" width="80">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'teacher' ? 'warning' : 'info'">
            {{ { student: '学生', teacher: '教师', admin: '管理员' }[row.role] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="联系方式" />
      <el-table-column prop="gender" label="性别" width="60">
        <template #default="{ row }">{{ { M: '男', F: '女' }[row.gender] || '-' }}</template>
      </el-table-column>
      <el-table-column prop="age" label="年龄" width="60" />
      <el-table-column label="学号" width="120">
        <template #default="{ row }">{{ row.student_profile?.student_number || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteUser(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-if="total > pageSize" style="margin-top: 20px; justify-content: center"
      :current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="handlePageChange" />

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '添加用户'" width="500px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" :placeholder="isEdit ? '留空不修改' : '至少6位'" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="姓"><el-input v-model="form.last_name" /></el-form-item>
        <el-form-item label="名"><el-input v-model="form.first_name" /></el-form-item>
        <el-form-item label="性别">
          <el-select v-model="form.gender" clearable>
            <el-option label="男" value="M" />
            <el-option label="女" value="F" />
          </el-select>
        </el-form-item>
        <el-form-item label="年龄"><el-input-number v-model="form.age" :min="1" :max="120" /></el-form-item>
        <el-form-item label="联系方式"><el-input v-model="form.phone" /></el-form-item>
        <template v-if="form.role === 'student'">
          <el-divider>学生信息</el-divider>
          <el-form-item label="学号" prop="student_number"><el-input v-model="form.student_number" /></el-form-item>
          <el-form-item label="年级"><el-input v-model="form.grade" /></el-form-item>
          <el-form-item label="班级"><el-input v-model="form.class_name" /></el-form-item>
          <el-form-item label="专业"><el-input v-model="form.major" /></el-form-item>
        </template>
        <template v-if="form.role === 'teacher' || form.role === 'admin'">
          <el-divider>教师信息</el-divider>
          <el-form-item label="职称"><el-input v-model="form.title" /></el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const users = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const keyword = ref('')
const roleFilter = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const formRules = reactive({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{
    validator: (rule, value, callback) => {
      if (!isEdit.value && !value) {
        callback(new Error('请输入密码'))
      } else if (value && value.length < 6) {
        callback(new Error('密码至少6位'))
      } else {
        callback()
      }
    },
    trigger: 'blur',
  }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  student_number: [{
    validator: (rule, value, callback) => {
      if (form.role === 'student' && !value) {
        callback(new Error('学生必须填写学号'))
      } else {
        callback()
      }
    },
    trigger: 'blur',
  }],
})

const defaultForm = {
  username: '', password: '', role: 'student',
  first_name: '', last_name: '', gender: '', age: null, phone: '',
  student_number: '', grade: '', class_name: '', major: '', title: '',
}
const form = reactive({ ...defaultForm })

onMounted(loadUsers)

async function loadUsers() {
  const params = { page: page.value }
  if (keyword.value) params.keyword = keyword.value
  if (roleFilter.value) params.role = roleFilter.value
  const { data } = await api.get('/auth/users/', { params })
  users.value = data.results || data
  total.value = data.count || users.value.length
}

function openAdd() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, { ...defaultForm })
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, {
    username: row.username, password: '', role: row.role,
    first_name: row.first_name, last_name: row.last_name,
    gender: row.gender, age: row.age, phone: row.phone,
    student_number: row.student_profile?.student_number || '',
    grade: row.student_profile?.grade || '',
    class_name: row.student_profile?.class_name || '',
    major: row.student_profile?.major || '',
    title: row.teacher_profile?.title || '',
  })
  dialogVisible.value = true
}

async function saveUser() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  const data = { ...form }
  if (!data.password) delete data.password
  if (data.role !== 'student') { delete data.student_number; delete data.grade; delete data.class_name; delete data.major }
  if (data.role === 'student') delete data.title

  if (isEdit.value) {
    await api.patch(`/auth/users/${editingId.value}/`, data)
    ElMessage.success('用户更新成功')
  } else {
    await api.post('/auth/users/', data)
    ElMessage.success('用户创建成功')
  }
  dialogVisible.value = false
  loadUsers()
}

async function deleteUser(row) {
  await ElMessageBox.confirm(`确定删除用户 ${row.username}？`, '警告', { type: 'warning' })
  await api.delete(`/auth/users/${row.id}/`)
  ElMessage.success('删除成功')
  loadUsers()
}

function handlePageChange(p) { page.value = p; loadUsers() }
</script>
