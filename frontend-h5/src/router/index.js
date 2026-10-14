import { createRouter, createWebHistory } from 'vue-router'
import ReportView from '../views/ReportView.vue'
import StartView from '../views/StartView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'start', component: StartView },
    { path: '/r/:code', name: 'report', component: ReportView },
  ],
})

export default router
