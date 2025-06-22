import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('../views/ChatView.vue')
  },
  {
    path: '/faq',
    name: 'faq',
    component: () => import('../views/FaqView.vue')
  },
  {
    path: '/quiz',
    name: 'quiz',
    component: () => import('../views/QuizView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL || '/'),
  routes
})

export default router 