# 忘记密码安全改造 — 密保问题验证

## 目标

当前 `POST /api/password/forgot` 只需学号即可直接重置密码，存在严重的身份冒用风险。改造为：自助密保问题验证 + 人工审批重置 的双通道方案，无需外部服务依赖，零额外成本。

## 涉及范围

- **后端**：`auth_routes.py`、`auth_service.py`、`teacher_routes.py`、`entities.py`、`schemas/common.py`
- **前端**：`LoginView.vue`、`ChangePasswordView.vue`、`ProfileView.vue`、教师端学生管理页
- **测试**：`tests/` 新增密保验证和人工重置流程测试

## 不做

- 不引入邮箱/手机号绑定
- 不做暴力破解的 IP 黑名单（后续迭代）
- 不改变现有的 `change-password` 和 `register` 逻辑

## 总体流程

```
忘记密码
  └── 输入学号
        └── 系统检查该用户是否设置了密保问题
              ├── 已设置 → 显示密保问题 → 输入答案
              │     ├── 答案正确 → 重置密码（自动生成随机密码或自设）
              │     └── 答案错误 → 提示错误，剩余重试次数 -1
              │                     └── 超过 5 次 → "验证失败，请走人工重置"
              └── 未设置（或答不对） → 显示留言表单
                    └── 提交重置请求 → 写入待审批队列
                          └── 教师/管理员审批 → 密码重置为随机密码 → 通知学生
```

## 数据库变更

### 新增表：`security_questions`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 主键 |
| user_id | VARCHAR(20) | FK → users.id, NOT NULL | 所属用户 |
| question | VARCHAR(200) | NOT NULL | 自定义密保问题 |
| answer_hash | VARCHAR(255) | NOT NULL | 答案哈希（pbkdf2_sha256） |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |

索引：`UNIQUE(user_id, question)` 防止重复问题。

### 新增表：`password_reset_requests`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 主键 |
| user_id | VARCHAR(20) | FK → users.id, NOT NULL | 申请人 |
| message | TEXT | NOT NULL | 申请留言 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending / approved / rejected |
| resolved_by | VARCHAR(20) | FK → users.id, NULL | 审批人 |
| new_password_hash | VARCHAR(255) | NULL | 审批后设置的新密码哈希 |
| resolved_at | DATETIME | NULL | 审批时间 |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | 申请时间 |

### User 表：无需新增字段

说明：`needs_password_change` 已有，审批重置后设为 `true`，让学生登录后自行改密；老师重置后可直接设随机密码。

## API 设计

所有接口返回统一格式 `{"code": 0, "data": ..., "message": "ok"}`。

### 1. 密保问题管理（需登录）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 获取密保问题 | GET | `/api/security-questions` | 返回当前用户的问题列表（只返回 id + question，不含答案） |
| 设置密保问题 | PUT | `/api/security-questions` | 整体替换，body: `{questions: [{question, answer}]}`，最多 3 个，至少可以 0 个 |

### 2. 忘记密码 — 自助重置（无需登录）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 获取密保问题 | GET | `/api/password/forgot/questions?user_id=xxx` | 返回该用户的问题列表（只返回 id + question）。若用户未设置，返回空列表 `[]` |
| 提交答案并重置 | POST | `/api/password/forgot/reset` | body: `{user_id, answers: [{question_id, answer}], new_password}`。全部正确→重置成功；任一错误→返回剩余重试次数 |

重试次数使用内存或简单缓存策略：同一 user_id 5 分钟内最多 5 次错误尝试，超过后返回 "验证次数超限，请走人工重置"。

### 3. 忘记密码 — 人工重置（无需登录）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 提交重置请求 | POST | `/api/password/forgot/request` | body: `{user_id, message}`。若已有 pending 请求，返回 "已有待处理的请求" |

### 4. 教师/管理员审批（需登录 + 权限）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 查看待审批列表 | GET | `/api/teacher/password-reset-requests` | 教师：只返回自己班级学生的请求；管理员：返回全部。status=pending |
| 审批重置 | POST | `/api/teacher/password-reset-requests/{id}/approve` | 生成随机 8 位密码，重置后标记 `needs_password_change=true` |
| 驳回请求 | POST | `/api/teacher/password-reset-requests/{id}/reject` | 标记 rejected，需填写驳回原因 |

管理员端同理，路径前缀为 `/api/admin/`。

## 流程时序

### 自助重置
```
学生 → 前端：输入学号
前端 → GET /password/forgot/questions?user_id=2025001
后端 → 返回 [{id:1, question:"你最喜欢的动物？"}, ...]
前端 → 显示问题，学生填写答案 + 新密码
前端 → POST /password/forgot/reset {user_id, answers:[{question_id:1, answer:"猫"}], new_password:"xxx"}
后端 → 验证全部答案 → 哈希存储新密码 → 返回成功
```

### 人工重置
```
学生 → 前端：输入学号 → 系统返回 "未设置密保问题，请申请人工重置"
学生 → 填写留言（如："我是二班的张三，忘记密码了"）
前端 → POST /password/forgot/request {user_id:"2025001", message:"..."}
后端 → 写入 password_reset_requests 表 → 返回成功

教师登录 → 查看学生管理 → 密码重置请求列表
教师 → 点击 "审批重置"
前端 → POST /teacher/password-reset-requests/{id}/approve
后端 → 生成随机密码 → 重置 → 标记 needs_password_change=true
教师 → 告知学生新密码
```

## 前端改动

### LoginView.vue — 忘记密码弹窗重构

```
[弹窗标题: 忘记密码]

Step 1: 输入学号 → 点击"下一步" → 调用 GET /password/forgot/questions
  ├── 有密保问题 → Step 2a: 显示问题 + 答案输入框 + 新密码输入框
  │      └── 提交：POST /password/forgot/reset
  └── 无密保问题 → Step 2b: 显示留言输入框 + 提示"未设置密保问题，请描述情况申请人工重置"
         └── 提交：POST /password/forgot/request
```

### ChangePasswordView.vue — 首次登录改密码后

改密码成功后，提示设置密保问题（可跳过）：
- 弹窗："为了账号安全，建议设置密保问题，方便后续自助找回密码"
- 提供输入框：至少 1 个问题，可选多个
- "跳过"按钮 → 直接进入系统

### ProfileView.vue — 个人中心新增入口

- 新增 "密保问题设置" 菜单项
- 进入后可增删改问题（PUT 整体替换）
- 查看已有问题时答案用 `****` 遮挡，修改时需输入新答案

### 教师端 — 密码重置请求管理

- 在 `TeacherStudentAdmin.vue` 或新的 tab 中增加 "密码重置请求" 列表
- 列表项：学生姓名、学号、留言、申请时间、状态
- 操作按钮：审批重置 / 驳回

## 安全措施

1. 答案哈希存储（pbkdf2_sha256），与原密码哈希方案一致
2. 自助重置答案验证：同一 user_id 5 分钟内最多 5 次错误，超过锁定
3. 自助重置成功后不返回新密码明文，前端提示"密码重置成功，请用新密码登录"
4. 人工审批后生成随机 8 位密码（大小写+数字），`needs_password_change=true`
5. 所有操作记录日志
6. 不返回答案哈希给前端（任何接口都只返回问题文本）

## 测试计划

| 测试用例 | 场景 |
|----------|------|
| 设置密保问题 | 登录后设置 1~3 个问题，验证返回 |
| 自助重置成功 | 设置密保后，忘记密码→回答正确→重置成功→新密码可登录 |
| 自助重置失败 | 回答错误，验证剩余次数递减，超过 5 次后锁定 |
| 自助重置超限转人工 | 5 次错误后，提示走人工通道 |
| 人工重置申请 | 未设置密保→提交留言→写入 pending 请求 |
| 教师审批 | 教师查看本班请求→审批→学生密码被重置→needs_password_change=true |
| 教师驳回 | 教师填写原因驳回→状态变为 rejected |
| 越权测试 | 教师不能审批非本班学生的请求 |
| 管理员审批 | 管理员可审批任意请求 |
| 重复申请 | 已有 pending 请求时再次提交，返回提示 |
