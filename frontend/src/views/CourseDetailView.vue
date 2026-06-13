<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCourseDetail, type CourseDetail } from '@/api/course'
import { getCourseContents, type Material } from '@/api/material'
import { resolveFileUrl } from '@/utils/url'

const route = useRoute()
const router = useRouter()
const courseId = computed(() => Number(route.params.courseId))
const course = ref<CourseDetail | null>(null)
const materials = ref<Material[]>([])
const loading = ref(true)
const keyword = ref('')

function materialUrl(item: Material) {
  return resolveFileUrl(item.file_id ? `/api/files/${item.file_id}` : item.url)
}

async function loadContents() {
  loading.value = true
  try {
    const [detail, contents] = await Promise.all([
      getCourseDetail(courseId.value),
      getCourseContents(courseId.value, keyword.value || undefined),
    ])
    course.value = detail
    materials.value = contents
  } finally {
    loading.value = false
  }
}

onMounted(loadContents)
</script>

<template>
  <div class="course-detail-page">
    <section class="course-hero">
      <div class="container">
        <button class="back-btn" @click="router.push('/learn')">
          <span class="back-arrow">←</span>
          <span>返回课程列表</span>
        </button>
        <div v-if="course" class="course-heading">
          <h1>{{ course.name }}</h1>
          <p>{{ course.material_count }} 份学习资料，{{ course.question_count }} 道练习题</p>
        </div>
      </div>
    </section>

    <section class="materials-section">
      <div class="container">
        <div class="search-bar">
          <input
            v-model="keyword"
            type="text"
            placeholder="搜索资料标题"
            @keyup.enter="loadContents"
          />
          <button @click="loadContents">搜索</button>
        </div>
        <div v-if="loading" class="empty-state">课程加载中...</div>
        <div v-else-if="materials.length > 0" class="materials-grid">
          <a
            v-for="item in materials"
            :key="item.id"
            class="material-card"
            :href="materialUrl(item)"
            target="_blank"
            rel="noopener"
          >
            <span class="material-type">{{ item.type === 'video' ? '视频' : 'PDF' }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.size || '未记录大小' }} · {{ item.date || '未记录日期' }}</p>
          </a>
        </div>
        <div v-else class="empty-state">{{ keyword ? '未找到匹配的资料' : '该课程暂无学习资料。' }}</div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.course-detail-page {
  padding-top: 60px;
}

.course-hero {
  padding: var(--space-2xl) 0;
  background: var(--color-learn-bg);
  border-bottom: 1px solid var(--color-border-light);
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--space-lg);
  padding: 8px 14px;
  color: var(--color-learn);
  background: rgba(45, 106, 122, 0.08);
  border: 1px solid rgba(45, 106, 122, 0.18);
  border-radius: var(--radius-full);
  font-weight: 700;
  transition: all var(--duration-fast);
}

.back-btn:hover {
  background: rgba(45, 106, 122, 0.14);
  transform: translateX(-2px);
}

.back-arrow {
  font-size: 1.15rem;
  line-height: 1;
}

.course-heading h1 {
  font-size: 2rem;
  font-weight: 800;
  font-family: var(--font-serif);
  letter-spacing: 0.05em;
  color: var(--color-text);
  margin-bottom: var(--space-sm);
}

.course-heading p {
  color: var(--color-text-secondary);
}

.materials-section {
  padding: var(--space-3xl) 0;
}

.search-bar {
  display: flex;
  gap: 8px;
  margin-bottom: var(--space-xl);
}

.search-bar input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
}

.search-bar button {
  padding: 10px 20px;
  background: var(--color-learn);
  color: white;
  border-radius: var(--radius-md);
  font-weight: 700;
  font-size: 0.85rem;
}

.materials-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-xl);
}

.material-card {
  display: block;
  padding: var(--space-xl);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--duration-normal) var(--ease-out);
}

.material-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-learn);
}

.material-type {
  display: inline-flex;
  margin-bottom: var(--space-sm);
  color: var(--color-learn);
  font-weight: 800;
}

.material-card h3 {
  font-size: 1.1rem;
  font-weight: 800;
  font-family: var(--font-serif);
  letter-spacing: 0.05em;
  color: var(--color-text);
  margin-bottom: var(--space-sm);
}

.material-card p,
.empty-state {
  color: var(--color-text-muted);
}

.empty-state {
  text-align: center;
  padding: var(--space-4xl) 0;
}

@media (max-width: 768px) {
  .materials-grid {
    grid-template-columns: 1fr;
  }
}
</style>
