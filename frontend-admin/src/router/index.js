import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth'

const routes = [
  { path: '/login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('../views/LayoutView.vue'),
    children: [
      { path: '', redirect: '/diagnoses' },
      { path: 'diagnoses', component: () => import('../views/DiagnosisList.vue') },
      { path: 'diagnoses/:id', component: () => import('../views/DiagnosisDetail.vue') },
      { path: 'prospects', component: () => import('../views/ProspectsView.vue') },
      { path: 'config', component: () => import('../views/ConfigView.vue'), meta: { admin: true } },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuth()
  if (!to.meta.public && !auth.token) return '/login'
  if (to.meta.admin && auth.role !== 'admin') return '/diagnoses'
})

export default router
