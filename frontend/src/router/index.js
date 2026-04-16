import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/auth/callback/github',
    name: 'AuthCallback',
    component: () => import('../views/AuthCallback.vue'),
    meta: { guest: true },
  },
  {
    path: '/student',
    component: () => import('../views/student/Layout.vue'),
    meta: { role: 'student' },
    children: [
      { path: '', name: 'StudentDashboard', component: () => import('../views/student/Dashboard.vue') },
      { path: 'discussion/:sessionId', name: 'StudentDiscussion', component: () => import('../views/student/Discussion.vue') },
    ],
  },
  {
    path: '/teacher',
    component: () => import('../views/teacher/Layout.vue'),
    meta: { role: 'teacher' },
    children: [
      { path: '', name: 'TeacherDashboard', component: () => import('../views/teacher/Dashboard.vue') },
      { path: 'statistics/:sessionId', name: 'TeacherStatistics', component: () => import('../views/teacher/Statistics.vue') },
      { path: 'history', name: 'TeacherHistory', component: () => import('../views/teacher/History.vue') },
      { path: 'discussion/:sessionId', name: 'TeacherDiscussion', component: () => import('../views/teacher/Discussion.vue') },
    ],
  },
  {
    path: '/admin',
    component: () => import('../views/admin/Layout.vue'),
    meta: { role: 'admin' },
    children: [
      { path: '', name: 'AdminUserManagement', component: () => import('../views/admin/UserManagement.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = sessionStorage.getItem('access_token')
  const userStr = sessionStorage.getItem('user')

  if (to.meta.guest) {
    if (token) {
      const user = JSON.parse(userStr)
      next(`/${user.role}`)
    } else {
      next()
    }
    return
  }

  if (!token) {
    next('/login')
    return
  }

  if (to.meta.role) {
    const user = JSON.parse(userStr)
    if (user.role !== to.meta.role) {
      next(`/${user.role}`)
      return
    }
  }

  next()
})

export default router
