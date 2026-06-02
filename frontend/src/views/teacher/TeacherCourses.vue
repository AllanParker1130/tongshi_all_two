<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createCourse,
  deleteCourse,
  getCourses,
  updateCourse,
  type Course,
} from '@/api/course'

const courses = ref<Course[]>([])
const loading = ref(true)
const router = useRouter()
const publicSearchKeyword = ref('')

const myCourses = computed(() => courses.value.filter(course => !course.is_public))
const publicCourses = computed(() => courses.value.filter(course => course.is_public))
const filteredPublicCourses = computed(() => {
  const keyword = publicSearchKeyword.value.trim().toLowerCase()
  if (!keyword) return publicCourses.value
  return publicCourses.value.filter(course => course.name.toLowerCase().includes(keyword))
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formData = reactive({
  name: '',
  is_public: false,
})
const saving = ref(false)

// 添加公共课程
const addDialogVisible = ref(false)
const addSearchKeyword = ref('')
const addedCourseIds = ref<Set<number>>(new Set())
const addingCourseIds = ref<Set<number>>(new Set())

// 已添加到自己的课程名称集合（跨对话）
const ownedCourseNames = computed(() => new Set(myCourses.value.map(c => c.name)))

function isAlreadyOwned(course: Course) {
  return addedCourseIds.value.has(course.id) || ownedCourseNames.value.has(course.name)
}

const searchablePublicCourses = computed(() => {
  const keyword = addSearchKeyword.value.trim().toLowerCase()
  let list = publicCourses.value.filter(c => !c.is_owner)
  if (keyword) list = list.filter(c => c.name.toLowerCase().includes(keyword))
  return [...list].sort((a, b) => {
    const aAdded = isAlreadyOwned(a) ? 0 : 1
    const bAdded = isAlreadyOwned(b) ? 0 : 1
    return aAdded - bAdded
  })
})

async function handleAddOneCourse(course: Course) {
  if (isAlreadyOwned(course) || addingCourseIds.value.has(course.id)) return
  addingCourseIds.value = new Set([...addingCourseIds.value, course.id])
  try {
    await createCourse({ name: course.name, is_public: false })
    addedCourseIds.value = new Set([...addedCourseIds.value, course.id])
    await loadCourses()
  } catch {
    ElMessage.error('添加失败，请稍后重试')
  } finally {
    const next = new Set(addingCourseIds.value)
    next.delete(course.id)
    addingCourseIds.value = next
  }
}

function openAddDialog() {
  addSearchKeyword.value = ''
  addedCourseIds.value = new Set()
  addDialogVisible.value = true
}

async function loadCourses() {
  loading.value = true
  try {
    courses.value = await getCourses()
  } catch {
    ElMessage.error('课程列表加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadCourses()
})

function openCreate() {
  isEdit.value = false
  editingId.value = null
  formData.name = ''
  formData.is_public = false
  dialogVisible.value = true
}

function openEdit(course: Course) {
  if (course.is_public && !course.is_owner) {
    ElMessage.warning('公共课程只能由创建者编辑')
    return
  }
  isEdit.value = true
  editingId.value = course.id
  formData.name = course.name
  formData.is_public = Boolean(course.is_public)
  dialogVisible.value = true
}

async function handleSave() {
  const name = formData.name.trim()
  if (!name) {
    ElMessage.warning('请输入课程名称')
    return
  }
  saving.value = true
  try {
    if (isEdit.value && editingId.value !== null) {
      await updateCourse(editingId.value, { name, is_public: formData.is_public })
      ElMessage.success('课程更新成功')
    } else {
      await createCourse({ name, is_public: formData.is_public })
      ElMessage.success('课程创建成功')
    }
    dialogVisible.value = false
    await loadCourses()
  } catch {
    ElMessage.error(isEdit.value ? '更新失败，请稍后重试' : '创建失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

async function handleDelete(course: Course) {
  if (course.is_public && !course.is_owner) {
    ElMessage.warning('公共课程只能由创建者删除')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除课程「${course.name}」？存在资料、题目、学习记录或班级时系统会拒绝删除。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' },
    )
    await deleteCourse(course.id)
    courses.value = courses.value.filter(item => item.id !== course.id)
    ElMessage.success('已删除')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}

function openMaterials(course: Course) {
  router.push({ path: '/teacher/materials', query: { course_id: course.id } })
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  return dateStr.slice(0, 10)
}
</script>

<template>
  <div class="courses-page">
    <div class="page-header">
      <h1>已添加课程</h1>
      <div class="header-actions">
        <el-button type="primary" round @click="openAddDialog">添加课程</el-button>
        <el-button type="primary" round @click="openCreate">新建课程</el-button>
      </div>
    </div>

    <el-table :data="myCourses" stripe style="width: 100%" v-loading="loading">
      <el-table-column type="index" label="序号" width="70" align="center" />
      <el-table-column prop="name" label="课程名称" min-width="200" />
      <el-table-column label="资料数" width="100" align="center">
        <template #default="{ row }">
          <span class="count-badge">{{ row.material_count ?? 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column label="题目数" width="100" align="center">
        <template #default="{ row }">
          <span class="count-badge">{{ row.question_count ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="140">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" @click="openMaterials(row)">查看资料</el-button>
          <el-button text size="small" @click="openEdit(row)">编辑</el-button>
          <el-button type="danger" text size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="!loading && myCourses.length === 0" class="empty-state">
      <p>暂无课程，请点击「新建课程」添加</p>
    </div>

    <div class="section-header public-section-header">
      <h2>公共课程 <span class="public-count">共 {{ publicCourses.length }} 门</span></h2>
    </div>

    <el-table :data="filteredPublicCourses" stripe style="width: 100%" max-height="240" v-loading="loading">
      <el-table-column type="index" label="序号" width="70" align="center" />
      <el-table-column prop="name" label="课程名称" min-width="200">
        <template #default="{ row }">
          <span>{{ row.name }}</span>
          <el-tag class="public-tag" size="small" type="success" effect="plain">公共</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="资料数" width="100" align="center">
        <template #default="{ row }">
          <span class="count-badge">{{ row.material_count ?? 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column label="题目数" width="100" align="center">
        <template #default="{ row }">
          <span class="count-badge">{{ row.question_count ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="140">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" @click="openMaterials(row)">查看资料</el-button>
          <el-button v-if="row.is_owner" type="danger" text size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="public-course-search">
      <el-input
        v-model="publicSearchKeyword"
        placeholder="搜索公共课程"
        clearable
        size="large"
      />
    </div>

    <div v-if="!loading && publicCourses.length === 0" class="empty-state public-empty">
      <p>暂无公共课程</p>
    </div>
    <div v-else-if="!loading && filteredPublicCourses.length === 0" class="empty-state public-empty">
      <p>没有匹配的公共课程</p>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑课程' : '新建课程'"
      width="420px"
      :close-on-click-modal="false"
    >
      <div class="form-group">
        <label>课程名称<span class="required">*</span></label>
        <el-input
          v-model="formData.name"
          placeholder="请输入课程名称"
          size="large"
          maxlength="100"
          show-word-limit
          @keyup.enter="handleSave"
        />
      </div>
      <div class="form-group">
        <el-checkbox v-model="formData.is_public">设为公共课程</el-checkbox>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ isEdit ? '保存修改' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加公共课程弹窗 -->
    <el-dialog
      v-model="addDialogVisible"
      title="添加公共课程"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-input
        v-model="addSearchKeyword"
        placeholder="搜索课程名称"
        size="large"
        clearable
        style="margin-bottom: var(--space-md)"
      />
      <el-table :data="searchablePublicCourses" stripe style="width: 100%" max-height="360">
        <el-table-column prop="name" label="课程名称" min-width="200">
          <template #default="{ row }">
            <span>{{ row.name }}</span>
            <el-tag class="public-tag" size="small" type="success" effect="plain">公共</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="资料" width="70" align="center">
          <template #default="{ row }">
            {{ row.material_count ?? 0 }}
          </template>
        </el-table-column>
        <el-table-column label="题目" width="70" align="center">
          <template #default="{ row }">
            {{ row.question_count ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button
              v-if="!isAlreadyOwned(row)"
              type="primary"
              text
              size="small"
              :loading="addingCourseIds.has(row.id)"
              @click="handleAddOneCourse(row)"
            >添加</el-button>
            <el-tag v-else size="small" type="info">已添加</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="searchablePublicCourses.length === 0" class="empty-state" style="margin-top: var(--space-md)">
        暂无可用公共课程
      </div>
      <template #footer>
        <el-button @click="addDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.courses-page {
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

.page-header h1 {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-text);
  font-family: var(--font-serif);
  letter-spacing: 0.05em;
}

.count-badge {
  font-weight: 700;
  color: var(--color-primary);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: var(--space-2xl) 0 var(--space-md);
}

.section-header h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
}

.section-header span {
  color: var(--color-text-secondary);
  font-size: 0.85rem;
}

.public-tag {
  margin-left: var(--space-sm);
}

.public-course-search {
  max-width: 360px;
  margin-top: var(--space-xl);
}

.empty-state {
  text-align: center;
  padding: var(--space-3xl) 0;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.public-empty {
  margin-top: var(--space-md);
}

.form-group {
  margin-bottom: var(--space-lg);
}

.form-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: var(--space-sm);
}

.required {
  color: #e74c3c;
  margin-left: 2px;
}
</style>
