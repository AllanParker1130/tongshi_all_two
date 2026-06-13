<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { getTeacherStats } from '@/api/teacher'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const pendingReviewCount = ref(0)
let reviewTimer: number | undefined

const navItems = [
  { name: '概述', path: '/teacher', icon: '&#9673;' },
  { name: '课程管理', path: '/teacher/courses', icon: '&#9670;' },
  { name: '班级管理', path: '/teacher/classes', icon: '&#9881;' },
  { name: '发布作业', path: '/teacher/publish', icon: '&#9993;' },
  { name: '学生成绩', path: '/teacher/grades', icon: '&#9783;' },
  { name: '作业完成', path: '/teacher/task-report', icon: '&#9745;' },
  { name: '作品审核', path: '/teacher/reviews', icon: '&#10003;' },
  { name: '资料管理', path: '/teacher/materials', icon: '&#9776;' },
  { name: '学生管理', path: '/teacher/student-admin', icon: '&#9782;' },
  { name: '题库管理', path: '/teacher/questions', icon: '&#9998;' },
]

function isActive(path: string) {
  if (path === '/teacher/task-report') {
    return route.path.startsWith('/teacher/task-report')
  }
  return route.path === path
}

async function fetchPendingReviews() {
  if (!authStore.isLoggedIn || authStore.user?.role !== 'teacher') {
    pendingReviewCount.value = 0
    return
  }
  try {
    const stats = await getTeacherStats()
    pendingReviewCount.value = stats.pending_reviews
  } catch {}
}

onMounted(() => {
  fetchPendingReviews()
  reviewTimer = window.setInterval(fetchPendingReviews, 15000)
})

onUnmounted(() => {
  if (reviewTimer !== undefined) window.clearInterval(reviewTimer)
})

watch(
  () => route.fullPath,
  () => {
    fetchPendingReviews()
  },
)
</script>

<template>
  <div class="teacher-layout">
    <header class="teacher-header">
      <div class="header-left">
        <router-link to="/" class="logo-link">
          <svg viewBox="0 0 32 32" width="24" height="24">
            <defs>
              <linearGradient id="tLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color: var(--color-primary)" />
                <stop offset="100%" style="stop-color: var(--color-learn)" />
              </linearGradient>
            </defs>
            <circle cx="16" cy="16" r="14" fill="url(#tLogoGrad)" />
            <text x="16" y="21" text-anchor="middle" font-size="13" font-weight="700" fill="white" font-family="sans-serif">师</text>
          </svg>
          <span class="logo-text">教师工作台</span>
        </router-link>
      </div>
      <div class="header-right">
        <span class="teacher-name">{{ authStore.user?.name || '教师' }}</span>
        <button class="btn-student-view" @click="router.push('/')">
          返回学生端
        </button>
      </div>
    </header>

    <div class="teacher-body">
      <aside class="teacher-sidebar">
        <nav class="sidebar-nav">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="sidebar-link"
            :class="{ active: isActive(item.path) }"
          >
            <span class="sidebar-icon" v-html="item.icon"></span>
            <span class="sidebar-text">{{ item.name }}</span>
            <span
              v-if="item.path === '/teacher/reviews' && pendingReviewCount > 0"
              class="review-badge"
            >
              {{ pendingReviewCount > 99 ? '99+' : pendingReviewCount }}
            </span>
          </router-link>
        </nav>
      </aside>

      <main class="teacher-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.teacher-layout {
  min-height: 100vh;
  background: var(--color-bg-alt);
  font-family: var(--font-sans);
}

.teacher-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-xl);
  background: rgba(255, 253, 248, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo-link {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.logo-text {
  font-size: 1rem;
  font-weight: 700;
  font-family: var(--font-serif);
  color: var(--color-text);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.teacher-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text);
}

.btn-student-view {
  padding: 0.4rem 1rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--duration-fast);
}

.btn-student-view:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.teacher-body {
  display: flex;
  padding-top: 60px;
  min-height: 100vh;
}

.teacher-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--color-bg-card);
  border-right: 1px solid var(--color-border);
  padding: var(--space-lg) 0;
  position: fixed;
  top: 60px;
  bottom: 0;
  left: 0;
  overflow-y: auto;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding: 0 var(--space-sm);
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  border-left: 3px solid transparent;
  transition: all var(--duration-fast);
  position: relative;
}

.sidebar-link:hover {
  color: var(--color-primary);
  border-left-color: var(--color-border);
}

.sidebar-link.active {
  color: #2d5a6e !important;
  font-weight: 600;
  border-left-color: #2d5a6e;
  background: rgba(45, 90, 110, 0.06);
}

.sidebar-link.active .sidebar-icon {
  color: #2d5a6e !important;
}

.sidebar-icon {
  font-size: 1rem;
  width: 20px;
  text-align: center;
}

.sidebar-text {
  flex: 1;
  min-width: 0;
}

.review-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: #dc2626;
  color: #fff;
  font-size: 0.68rem;
  font-weight: 800;
  line-height: 18px;
  text-align: center;
  box-shadow: 0 0 0 2px var(--color-bg-card);
}

.teacher-main {
  flex: 1;
  margin-left: 200px;
  padding: var(--space-xl);
}

@media (max-width: 768px) {
  .teacher-sidebar {
    width: 60px;
  }

  .sidebar-link {
    justify-content: center;
    padding: var(--space-sm);
    border-left: none;
  }

  .sidebar-link span:not(.sidebar-icon) {
    display: none;
  }

  .review-badge {
    display: block !important;
    position: absolute;
    top: 4px;
    right: 6px;
    min-width: 8px;
    width: 8px;
    height: 8px;
    padding: 0;
    overflow: hidden;
    color: transparent;
    line-height: 8px;
  }

  .teacher-main {
    margin-left: 60px;
  }

  .teacher-name {
    display: none;
  }
}
</style>
