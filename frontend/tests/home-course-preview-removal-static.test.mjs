import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')

function read(relativePath) {
  return readFileSync(resolve(root, relativePath), 'utf8')
}

const homeView = read('src/views/HomeView.vue')

assert.ok(
  existsSync(resolve(root, 'src/components/home/CoursePreview.vue')),
  'CoursePreview 组件文件应保留，便于后续改造成动态课程入口。',
)

assert.doesNotMatch(
  homeView,
  /import\s+CoursePreview\s+from/,
  '首页不应继续导入旧的课程预览组件。',
)

assert.doesNotMatch(
  homeView,
  /<CoursePreview\s*\/>/,
  '首页不应继续渲染旧的六块课程内容。',
)
