import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { ROUTE_NAMES } from '@/utils/constants'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: ROUTE_NAMES.DASHBOARD,
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '概览', icon: 'icon-dashboard' },
      },
      {
        path: 'knowledge',
        name: ROUTE_NAMES.KNOWLEDGE_LIST,
        component: () => import('@/views/knowledge/List.vue'),
        meta: { title: '知识库管理', icon: 'icon-book' },
      },
      {
        path: 'knowledge/:id/items/:itemId?',
        name: ROUTE_NAMES.KNOWLEDGE_ITEMS,
        component: () => import('@/views/knowledge/Items.vue'),
        meta: { title: '知识条目', hidden: true },
      },
      {
        path: 'knowledge/:id/upload',
        name: ROUTE_NAMES.KNOWLEDGE_UPLOAD,
        component: () => import('@/views/knowledge/Upload.vue'),
        meta: { title: '导入文档', hidden: true },
      },
      {
        path: 'knowledge/:id',
        name: ROUTE_NAMES.KNOWLEDGE_DETAIL,
        component: () => import('@/views/knowledge/Detail.vue'),
        meta: { title: '知识库详情', hidden: true },
      },
      {
        path: 'chat',
        name: ROUTE_NAMES.CHAT,
        component: () => import('@/views/chat/Index.vue'),
        meta: { title: '智能问答', icon: 'icon-message' },
      },
      {
        path: 'agents/:agentId',
        name: ROUTE_NAMES.AGENT_DETAIL,
        component: () => import('@/views/agent/Detail.vue'),
        meta: { title: '专家助手', hidden: true },
      },
      {
        path: 'agents/:agentId/chat',
        name: ROUTE_NAMES.AGENT_CHAT,
        component: () => import('@/views/agent/Chat.vue'),
        meta: { title: '专家对话', hidden: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
