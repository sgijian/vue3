import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'TaskCreate',
      component: () => import('../views/TaskCreate.vue'),
    },
    {
      path: '/result/:id',
      name: 'ResultView',
      component: () => import('../views/ResultView.vue'),
      // 添加 props 配置以便在组件内直接获取 route params (可选，视 ResultView 实现而定)
      props: true 
    },
  ],
})

export default router