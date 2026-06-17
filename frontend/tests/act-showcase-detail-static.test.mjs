import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')

function read(relativePath) {
  return readFileSync(resolve(root, relativePath), 'utf8')
}

const router = read('src/router/index.ts')
const actView = read('src/views/ActView.vue')
const detailPath = resolve(root, 'src/views/ActDetailView.vue')

assert.ok(
  existsSync(detailPath),
  '学生端“行”图文详情页 ActDetailView.vue 应存在。',
)

const detailView = read('src/views/ActDetailView.vue')

assert.match(
  router,
  /path:\s*['"]\/act\/showcase\/:id['"]/,
  '路由应提供 /act/showcase/:id 详情页入口。',
)

assert.match(
  router,
  /ActDetailView\.vue/,
  '详情页路由应懒加载 ActDetailView.vue。',
)

assert.match(
  actView,
  /router\.push\(`\/act\/showcase\/\$\{item\.id\}`\)/,
  '“了解详情”应跳转到站内二级详情页。',
)

assert.doesNotMatch(
  actView,
  /<a[\s\S]*?item\.link_url[\s\S]*?class="showcase-link"/,
  '列表页不应再把“了解详情”直接绑定到外部链接。',
)

assert.match(
  detailView,
  /getShowcase/,
  '详情页应复用现有公开图文接口。',
)

assert.match(
  detailView,
  /route\.params\.id/,
  '详情页应根据路由 id 查找图文内容。',
)

assert.match(
  detailView,
  /item\.content/,
  '详情页应展示完整正文内容。',
)

assert.match(
  detailView,
  /item\.images/,
  '详情页应展示相关图片列表。',
)

assert.match(
  detailView,
  /了解更多/,
  '详情页底部应包含“了解更多”区域。',
)

assert.match(
  detailView,
  /item\.link_url/,
  '详情页底部应使用 link_url 作为外部了解更多链接。',
)
