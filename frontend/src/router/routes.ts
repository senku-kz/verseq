import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('../pages/LandingPage.vue') },
      { path: 'practice', component: () => import('../pages/PracticePage.vue') },
      { path: 'course', component: () => import('../pages/CoursePage.vue') },
      { path: 'lesson/:lessonId', component: () => import('../pages/LessonPage.vue') },
      { path: 'stats', component: () => import('../pages/StatsPage.vue') },
      { path: 'login', component: () => import('../pages/LoginPage.vue') },
      { path: 'settings', component: () => import('../pages/SettingsPage.vue') },
      { path: 'onboarding', component: () => import('../pages/OnboardingPage.vue') },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('../pages/LandingPage.vue'),
  },
]

export default routes
