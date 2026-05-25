# 前端实施计划 — 个人页面 + 登录改进 + 班级管理 + 图片修复

> **For agentic workers:** Use superpowers:subagent-driven-development 或 superpowers:executing-plans 按任务逐步实施。步骤使用 `- [ ]` 追踪。

**Goal:** 实现学生个人页面（修改密码/错题本/收藏作品）、登录流程改进（忘记密码弹窗/首次强制改密/密码错误弹窗）、班级管理手动添加学生改进、以及图片/PDF 显示问题修复。

**Architecture:** Vue 3 Composition API + Pinia + Vue Router + Element Plus。所有 API 调用通过 `@/api/` 模块封装，页面组件放在 `views/`，路由守卫控制访问权限。

**Tech Stack:** Vue 3、TypeScript、Vite、Element Plus、Pinia、Axios。

---

## 文件结构

- Modify: `frontend/src/stores/auth.ts`
  - User 接口增加 `is_first_login`；login 返回值改为丰富结构；新增 `changePassword` action
- Modify: `frontend/src/api/auth.ts`
  - 新增 `changePassword()`、`forgotPassword()` API
- Modify: `frontend/src/api/class.ts`
  - `enrollStudent()` 参数增加 `name`
- Modify: `frontend/src/views/LoginView.vue`
  - 密码错误弹窗、忘记密码弹窗、首次登录强制改密弹窗
- Modify: `frontend/src/views/teacher/TeacherClasses.vue`
  - 手动添加学生弹窗增加姓名输入框
- Modify: `frontend/src/router/index.ts`
  - 增加 `/profile` 路由
- Modify: `frontend/src/components/AppHeader.vue`
  - 增加"个人中心"入口
- Modify: `frontend/src/utils/url.ts`
  - 增强 URL 解析鲁棒性
- Create: `frontend/src/api/profile.ts`
  - 个人页面 API 模块
- Create: `frontend/src/views/ProfileView.vue`
  - 个人页面（修改密码/错题本/收藏作品）

---

## Task 1: 认证 Store 和 API 扩展

**Files:**
- Modify: `frontend/src/stores/auth.ts`
- Modify: `frontend/src/api/auth.ts`

- [ ] **Step 1: 扩展 auth API 模块**

在 `frontend/src/api/auth.ts` 中新增两个函数：

```typescript
export function changePassword(data: { old_password: string; new_password: string }) {
  return http.post<any, { message: string }>('/password/change', data)
}

export function forgotPassword(data: { id: string; new_password: string }) {
  return http.post<any, { message: string }>('/password/forgot', data)
}
```

- [ ] **Step 2: 修改 auth store**

在 `frontend/src/stores/auth.ts` 中：

1. `User` 接口增加字段：
```typescript
export interface User {
  id: string
  name: string
  role: 'student' | 'teacher'
  major?: string
  is_first_login?: boolean  // 新增
}
```

2. `login()` 方法中保存 `is_first_login`：
```typescript
const u: User = {
  id: result.user.id,
  name: result.user.name,
  role: result.user.role as 'student' | 'teacher',
  major: result.user.major,
  is_first_login: result.user.is_first_login,  // 新增
}
```

3. 新增 `changePassword` action（在 store 中调用 API 并更新本地 `is_first_login`）：

```typescript
import { changePassword as apiChangePassword } from '@/api/auth'

async function changePassword(oldPassword: string, newPassword: string): Promise<boolean> {
  try {
    await apiChangePassword({ old_password: oldPassword, new_password: newPassword })
    if (user.value) {
      user.value.is_first_login = false
      localStorage.setItem('auth_user', JSON.stringify(user.value))
    }
    return true
  } catch {
    return false
  }
}
```

4. 在 return 中导出 `changePassword`。

---

## Task 2: 登录页改造（需求 2/5/6）

**Files:**
- Modify: `frontend/src/views/LoginView.vue`

- [ ] **Step 1: 密码错误弹窗（需求 6）**

在 `handleLogin` 函数中，当 `authStore.login()` 返回 `false` 时，增加 `ElMessageBox.alert` 弹窗：

```typescript
import { ElMessage, ElMessageBox } from 'element-plus'

const success = await authStore.login(form.id.trim(), form.password)
loading.value = false
if (success) {
  // 登录成功逻辑...
} else {
  // 新增：密码错误弹窗
  ElMessageBox.alert('密码错误，请重试', '登录失败', {
    confirmButtonText: '确定',
    type: 'error',
  })
}
```

- [ ] **Step 2: 忘记密码弹窗（需求 2）**

在模板中 `.form-footer` 之后添加"忘记密码？"链接：

```html
<div class="form-footer">
  <span>没有账号？</span>
  <router-link to="/register" class="link">去注册</router-link>
  <span class="divider">|</span>
  <a class="link" @click="showForgotDialog = true">忘记密码？</a>
</div>
```

在模板底部添加 `ElDialog`（复用 RegisterView 的密码校验规则：6+位、包含字母和数字）：

```html
<el-dialog v-model="showForgotDialog" title="重置密码" width="400px" :close-on-click-modal="false">
  <div class="form-group">
    <label>学号 / 工号</label>
    <el-input v-model="forgotForm.id" placeholder="请输入学号或工号" size="large" />
  </div>
  <div class="form-group">
    <label>新密码</label>
    <el-input v-model="forgotForm.newPassword" type="password" placeholder="至少 6 位，包含字母和数字" size="large" show-password />
  </div>
  <div class="form-group">
    <label>确认密码</label>
    <el-input v-model="forgotForm.confirmPassword" type="password" placeholder="再次输入新密码" size="large" show-password />
  </div>
  <template #footer>
    <el-button @click="showForgotDialog = false">取消</el-button>
    <el-button type="primary" :loading="forgotLoading" @click="handleForgotPassword">重置密码</el-button>
  </template>
</el-dialog>
```

对应的 `handleForgotPassword` 函数：校验学号非空、密码规则、两次一致，调用 `forgotPassword` API。

- [ ] **Step 3: 首次登录强制改密弹窗（需求 5）**

登录成功后，检查 `authStore.user?.is_first_login`。若为 `true`，弹出不可关闭的 `ElDialog`：

```html
<el-dialog v-model="showChangePasswordDialog" title="首次登录，请修改密码"
           width="400px" :close-on-click-modal="false" :close-on-press-escape="false" :show-close="false">
  <div class="form-group">
    <label>当前密码</label>
    <el-input v-model="changeForm.oldPassword" type="password" size="large" show-password />
  </div>
  <div class="form-group">
    <label>新密码</label>
    <el-input v-model="changeForm.newPassword" type="password" placeholder="至少 6 位，包含字母和数字" size="large" show-password />
  </div>
  <div class="form-group">
    <label>确认密码</label>
    <el-input v-model="changeForm.confirmPassword" type="password" placeholder="再次输入新密码" size="large" show-password />
  </div>
  <template #footer>
    <el-button type="primary" :loading="changeLoading" @click="handleFirstLoginChange">确认修改</el-button>
  </template>
</el-dialog>
```

`handleFirstLoginChange` 函数：校验密码规则、两次一致，调用 `authStore.changePassword()`，成功后正常跳转。

核心流程修改：

```typescript
if (success) {
  if (authStore.user?.is_first_login) {
    // 首次登录，弹出改密窗口，暂不跳转
    showChangePasswordDialog.value = true
  } else {
    ElMessage.success(`欢迎回来，${authStore.user!.name}`)
    // 正常跳转逻辑...
  }
}
```

- [ ] **Step 4: 样式调整**

在 `<style scoped>` 中为新弹窗涉及的 `.form-group`、`.divider` 等添加基础样式（复用登录页已有的 `.form-group` 样式即可）。

---

## Task 3: 个人页面（需求 1）

**Files:**
- Create: `frontend/src/api/profile.ts`
- Create: `frontend/src/views/ProfileView.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/components/AppHeader.vue`

- [ ] **Step 1: 创建 profile API 模块**

创建 `frontend/src/api/profile.ts`：

```typescript
import http from './http'

export interface WrongQuestion {
  question_id: number
  chapter_id: number
  stem: string
  options: string[]
  answer: string
  explanation: string
  user_answer: string
  answered_at: string
}

export interface LikedProject {
  id: number
  title: string
  author_name: string
  major: string
  description: string
  image_url: string
  images: { image_url: string; sort_order: number }[]
  likes: number
  date: string
}

export function getWrongQuestions() {
  return http.get<any, WrongQuestion[]>('/profile/wrong-questions')
}

export function getLikedProjects() {
  return http.get<any, LikedProject[]>('/profile/liked-projects')
}
```

- [ ] **Step 2: 创建 ProfileView.vue**

创建 `frontend/src/views/ProfileView.vue`，使用 `el-tabs` 分三个 Tab：

**Tab 1 — 修改密码：**
- 旧密码、新密码、确认密码输入框
- 校验规则复用 RegisterView 的逻辑（6+位、字母+数字、两次一致）
- 提交调用 `changePassword` API（从 `@/api/auth` 导入）

**Tab 2 — 错题本：**
- 页面加载时调用 `getWrongQuestions()`
- 使用 `el-collapse` 或卡片列表展示：题目（stem）、我的答案、正确答案、解析
- 空状态："暂无错题，继续保持！"

**Tab 3 — 收藏作品：**
- 页面加载时调用 `getLikedProjects()`
- 卡片网格布局（参考 CreateView.vue 的卡片样式），3列响应式
- 每张卡片：封面图（`resolveFileUrl`）、标题、作者、点赞数
- 点击跳转 `/create/project/:id`
- 空状态："暂无收藏作品"

页面结构：

```html
<template>
  <div class="profile-page">
    <div class="page-header">
      <h1>个人中心</h1>
    </div>
    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="修改密码" name="password">
        <!-- 修改密码表单 -->
      </el-tab-pane>
      <el-tab-pane label="错题本" name="wrong-questions">
        <!-- 错题列表 -->
      </el-tab-pane>
      <el-tab-pane label="收藏作品" name="liked-projects">
        <!-- 收藏作品卡片网格 -->
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
```

- [ ] **Step 3: 添加路由**

在 `frontend/src/router/index.ts` 的 `/portfolio` 路由之后添加：

```typescript
{
  path: '/profile',
  name: 'profile',
  component: () import('../views/ProfileView.vue'),
  meta: { title: '个人中心' },
},
```

- [ ] **Step 4: 增加 Header 入口**

在 `frontend/src/components/AppHeader.vue` 中：

1. 桌面端 `header-actions` 区域，在 `user-name` 之前增加个人中心链接：

```html
<router-link to="/profile" class="nav-link profile-link">个人中心</router-link>
```

2. 移动端 `mobile-nav` 区域，在教师工作台链接之后增加：

```html
<router-link to="/profile" class="mobile-nav-link" @click="mobileMenuOpen = false">
  个人中心
</router-link>
```

---

## Task 4: 班级管理改进（需求 4）

**Files:**
- Modify: `frontend/src/api/class.ts`
- Modify: `frontend/src/views/teacher/TeacherClasses.vue`

- [ ] **Step 1: 修改 class API**

在 `frontend/src/api/class.ts` 中修改 `enrollStudent` 函数：

```typescript
export function enrollStudent(classId: number, studentId: string, name: string = '') {
  return http.post<any, any>(`/classes/${classId}/enroll`, { student_id: studentId, name })
}
```

- [ ] **Step 2: 修改 TeacherClasses.vue**

1. 增加 `enrollStudentName` ref：

```typescript
const enrollStudentName = ref('')
```

2. 在 `openEnroll` 中重置姓名：

```typescript
function openEnroll() {
  enrollStudentId.value = ''
  enrollStudentName.value = ''
  enrollDialogVisible.value = true
}
```

3. 修改 `handleEnroll` 传递姓名：

```typescript
async function handleEnroll() {
  if (!selectedClass.value || !enrollStudentId.value.trim() || !enrollStudentName.value.trim()) {
    ElMessage.warning('请输入学号和姓名')
    return
  }
  try {
    await enrollStudent(selectedClass.value.id, enrollStudentId.value.trim(), enrollStudentName.value.trim())
    ElMessage.success('添加成功')
    enrollDialogVisible.value = false
    classStudents.value = await getClassStudents(selectedClass.value.id)
    await loadClasses()
  } catch {
    ElMessage.error('添加失败，请检查信息是否正确')
  }
}
```

4. 修改弹窗模板，增加姓名输入框：

```html
<!-- Enroll student dialog -->
<el-dialog v-model="enrollDialogVisible" title="手动添加学生" width="380px">
  <div class="form-group">
    <label>学号</label>
    <el-input v-model="enrollStudentId" placeholder="输入学生学号" size="large" />
  </div>
  <div class="form-group">
    <label>姓名</label>
    <el-input v-model="enrollStudentName" placeholder="输入学生姓名" size="large" />
  </div>
  <p class="enroll-hint">若该学号不存在，系统将自动创建学生账号（默认密码 123456）</p>
  <template #footer>
    <el-button @click="enrollDialogVisible = false">取消</el-button>
    <el-button type="primary" @click="handleEnroll">添加</el-button>
  </template>
</el-dialog>
```

5. 添加 `.enroll-hint` 样式：

```css
.enroll-hint {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-top: var(--space-sm);
}
```

---

## Task 5: 修复图片/PDF 显示（需求 3）

**Files:**
- Modify: `frontend/src/utils/url.ts`

- [ ] **Step 1: 增强 resolveFileUrl**

在 `frontend/src/utils/url.ts` 中，增加对缺少前导 `/` 的路径处理：

```typescript
export function resolveFileUrl(url: string | undefined | null): string {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url

  // 统一路径格式：确保以 / 开头
  let normalized = url
  if (!normalized.startsWith('/')) {
    normalized = '/' + normalized
  }

  const base = import.meta.env.VITE_API_BASE as string | undefined
  if (!base) return normalized
  return `${base.replace(/\/$/, '')}${normalized}`
}
```

- [ ] **Step 2: 验证显示效果**

启动前后端后，检查以下页面的图片和 PDF 是否正常显示：

1. `/teacher/reviews` — 作品审核页的图片预览和 PDF iframe
2. `/create/project/:id` — 作品详情页的图片和 PDF
3. `/profile`（新增）— 收藏作品的封面图

如果仍有问题，检查浏览器 Network 面板中的请求 URL 和响应状态码，确认 Vite proxy 配置是否正确覆盖 `/uploads` 路径。

---

## 验收标准

1. 登录页输入错误密码，弹窗显示"密码错误，请重试"。
2. 登录页点击"忘记密码？"，弹窗输入学号+新密码，重置后可新密码登录。
3. 使用默认密码 123456 首次登录，弹出不可关闭的改密窗口，改密后正常进入。
4. 进入 `/profile` 页面，修改密码 Tab 可正常修改密码。
5. 错题本 Tab 显示该用户所有错题（去重，仅最近一次答错）。
6. 收藏作品 Tab 显示点赞过的作品卡片，点击可跳转详情。
7. Header 中"个人中心"链接可正常跳转（桌面端和移动端）。
8. 教师端手动添加学生弹窗有学号+姓名两个输入框，填写后可自动创建账号。
9. 教师端审核页和学生端详情页的图片/PDF 正常显示。

---

## 自检结果

- 覆盖了全部 6 项前端需求。
- 密码校验规则在注册、修改密码、忘记密码、首次改密四处保持一致（6+位、字母+数字）。
- 错题本和收藏作品复用现有 service 层逻辑，未重复实现。
- 班级管理改进兼容旧逻辑（name 为空时后端要求用户已存在）。
- 图片显示通过增强 `resolveFileUrl` 处理路径格式不一致问题。
- 未引入新 UI 框架，全部使用 Element Plus 现有组件。
