import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login',      component: () => import('../pages/Login.vue'),      meta: { guest: true } },
  { path: '/register',   component: () => import('../pages/Register.vue'),   meta: { guest: true } },
  { path: '/onboarding', component: () => import('../pages/Onboarding.vue'), meta: { auth: true } },
  { path: '/',           component: () => import('../pages/Home.vue'),        meta: { auth: true } },
  { path: '/content/:id', component: () => import('../pages/ContentDetail.vue'), meta: { auth: true } },
  { path: '/profile',  component: () => import('../pages/Profile.vue'),  meta: { auth: true } },
  {
    path: '/admin',
    component: () => import('../pages/admin/Layout.vue'),
    meta: { auth: true, admin: true },
    children: [
      { path: '',           redirect: '/admin/dashboard' },
      { path: 'dashboard',  component: () => import('../pages/admin/Dashboard.vue') },
      { path: 'users',      component: () => import('../pages/admin/Users.vue') },
      { path: 'contents',   component: () => import('../pages/admin/Contents.vue') },
      { path: 'model',      component: () => import('../pages/admin/Model.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.token) return '/login'
  if (to.meta.guest && auth.token) return '/'
  if (to.meta.admin && auth.user?.role !== 'admin') return '/'
})

export default router
