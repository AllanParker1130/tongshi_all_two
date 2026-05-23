<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const actionSteps = [
  {
    num: '01',
    title: '理解真实问题',
    desc: '从社区、学校和课程项目中选择一个具体问题，先明确对象、场景和限制条件。',
  },
  {
    num: '02',
    title: '设计 AI 方案',
    desc: '把课堂学到的 AI 工具、调研方法和表达方式整理成可执行的小方案。',
  },
  {
    num: '03',
    title: '服务并复盘',
    desc: '在公益课、读书会和项目实践中记录反馈，形成可复盘的学习材料。',
  },
]

const outcomeCards = [
  {
    id: 'public-class',
    icon: '🏫',
    title: 'AI 公益课',
    subtitle: '走进社区与中小学',
    desc: '面向青少年和社区居民开展 AI 启蒙，练习把知识讲清楚。',
    count: '20+',
    label: '场公益课',
  },
  {
    id: 'reading-club',
    icon: '📚',
    title: '读书会',
    subtitle: '围绕 AI 主题开展共读',
    desc: '通过阅读、分享和讨论，训练学生提问、表达和形成观点的能力。',
    count: '12',
    label: '期读书会',
  },
  {
    id: 'field-project',
    icon: '🌍',
    title: '落地项目',
    subtitle: '完成项目实践与展示',
    desc: '把课堂知识转化为调研报告、活动方案、工具原型和展示材料。',
    count: '8',
    label: '个落地项目',
  },
]

const outcomeDetails = [
  {
    id: 'public-class',
    badge: '公益课',
    title: 'AI 公益课：把 AI 知识讲清楚',
    intro: '学生团队走进社区与中小学，将 AI 概念、工具体验和安全意识设计成适合不同年龄段的课程。重点是让听众听得懂、能体验、知道基本使用边界。',
    stats: [
      { value: '20+', label: '累计课程' },
      { value: '600+', label: '覆盖听众' },
      { value: '4', label: '课程主题' },
    ],
    highlights: [
      '面向小学生设计“AI 是什么”“如何安全使用 AI”等启蒙内容。',
      '面向社区居民设计手机 AI 助手、常见风险识别和生活工具体验。',
      '课后收集听众反馈，复盘讲解节奏、案例选择和互动方式。',
    ],
    cases: ['AI 启蒙小课堂', '社区 AI 科普活动', '家长数字素养微课'],
  },
  {
    id: 'reading-club',
    badge: '读书会',
    title: '读书会：在阅读和讨论中形成观点',
    intro: '读书会围绕 AI、社会、教育和职业发展展开。学生需要摘录观点、提出问题、参与讨论，并把讨论内容整理成读书笔记或分享材料。',
    stats: [
      { value: '12', label: '读书会' },
      { value: '36', label: '主题分享' },
      { value: '5', label: '核心议题' },
    ],
    highlights: [
      '围绕《生命 3.0》《智能时代》等书目组织章节共读。',
      '用“观点卡片 + 问题清单”的方式引导学生发言。',
      '将讨论结论沉淀为读书笔记、展示海报和课堂分享。',
    ],
    cases: ['AI 与职业发展讨论', '技术伦理主题讨论', 'AI 主题读书分享'],
  },
  {
    id: 'field-project',
    badge: '落地项目',
    title: '落地项目：把课堂学习做成项目成果',
    intro: '落地项目要求学生从一个具体问题出发，完成调研、方案设计、原型制作和成果展示。项目强调过程清楚、材料完整、后续可以继续改进。',
    stats: [
      { value: '8', label: '落地项目' },
      { value: '3', label: '合作场景' },
      { value: '100%', label: '复盘记录' },
    ],
    highlights: [
      '从校园活动、社区服务和学习支持中选择具体问题。',
      '使用 AI 辅助调研、内容生成、数据整理或交互原型设计。',
      '通过项目展示和反馈记录，形成下一轮优化建议。',
    ],
    cases: ['社区问答助手原型', '校园活动海报生成', '学习资料整理工具'],
  },
]

const portfolioFeatures = [
  { label: '学习时长', color: 'var(--color-learn)' },
  { label: '练习正确率', color: 'var(--color-primary)' },
  { label: '创意作品', color: 'var(--color-create)' },
  { label: '公益参与', color: 'var(--color-act)' },
]

function scrollToOutcome(id: string) {
  document.getElementById(id)?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

function startAction() {
  document.getElementById('action-path')?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}
</script>

<template>
  <div class="act-page">
    <section class="page-hero">
      <div class="container">
        <div class="hero-inner">
          <div class="hero-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
              <path
                d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.63 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.841m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
          <h1>行 · 知行合一</h1>
          <p>把课堂学习延伸到社区、学校和项目实践中，记录每一次行动带来的成长。</p>
          <div class="hero-actions">
            <el-button type="success" size="large" round @click="startAction">
              开始开展行动
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <section id="action-path" class="path-section">
      <div class="container">
        <div class="section-header">
          <span class="section-kicker">行动路径</span>
          <h2>一次行动如何发生</h2>
          <p>先明确问题，再设计 AI 辅助方案，最后记录过程和反馈。</p>
        </div>

        <div class="steps-grid">
          <div v-for="step in actionSteps" :key="step.num" class="step-card">
            <span class="step-num">{{ step.num }}</span>
            <h3>{{ step.title }}</h3>
            <p>{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="outcomes-nav-section">
      <div class="container">
        <div class="section-header compact">
          <span class="section-kicker">行动成果</span>
          <h2>三类成果在同一页查看</h2>
          <p>点击任意成果卡片，查看对应的介绍、数据和案例。</p>
        </div>

        <div class="outcome-card-grid">
          <button
            v-for="outcome in outcomeCards"
            :key="outcome.id"
            class="outcome-card"
            type="button"
            @click="scrollToOutcome(outcome.id)"
          >
            <span class="outcome-icon">{{ outcome.icon }}</span>
            <span class="outcome-body">
              <span class="outcome-title">{{ outcome.title }}</span>
              <span class="outcome-subtitle">{{ outcome.subtitle }}</span>
              <span class="outcome-desc">{{ outcome.desc }}</span>
              <span class="outcome-stat">
                <strong>{{ outcome.count }}</strong>
                <span>{{ outcome.label }}</span>
              </span>
            </span>
          </button>
        </div>
      </div>
    </section>

    <section class="outcome-details-section">
      <div class="container">
        <article
          v-for="detail in outcomeDetails"
          :id="detail.id"
          :key="detail.id"
          class="detail-panel"
        >
          <div class="detail-main">
            <span class="detail-badge">{{ detail.badge }}</span>
            <h2>{{ detail.title }}</h2>
            <p>{{ detail.intro }}</p>

            <div class="detail-highlights">
              <h3>主要内容</h3>
              <ul>
                <li v-for="item in detail.highlights" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>

          <aside class="detail-side">
            <div class="detail-stats">
              <div v-for="stat in detail.stats" :key="stat.label" class="detail-stat">
                <strong>{{ stat.value }}</strong>
                <span>{{ stat.label }}</span>
              </div>
            </div>

            <div class="case-box">
              <h3>案例方向</h3>
              <div class="case-list">
                <span v-for="item in detail.cases" :key="item" class="case-item">
                  {{ item }}
                </span>
              </div>
            </div>
          </aside>
        </article>
      </div>
    </section>

    <section class="portfolio-section">
      <div class="container">
        <div class="portfolio-card">
          <div class="portfolio-content">
            <span class="section-kicker">成长沉淀</span>
            <h3>查看我的成长档案</h3>
            <p>公益课、读书会和落地项目中的参与记录，会和学习、练习、创作数据一起形成个人成长记录。</p>
            <div class="portfolio-features">
              <span v-for="feature in portfolioFeatures" :key="feature.label" class="pf-item">
                <span class="pf-dot" :style="{ background: feature.color }"></span>
                {{ feature.label }}
              </span>
            </div>
          </div>
          <el-button type="success" size="large" round @click="router.push('/portfolio')">
            打开成长档案
          </el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.act-page {
  padding-top: 64px;
}

.page-hero {
  padding: var(--space-3xl) 0;
  background: var(--color-act-bg);
  border-bottom: 1px solid var(--color-border-light);
}

.hero-inner {
  text-align: center;
}

.hero-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, var(--color-act-light), var(--color-act));
  border-radius: var(--radius-lg);
  color: white;
  margin-bottom: var(--space-lg);
}

.hero-inner h1 {
  font-size: 2rem;
  font-weight: 800;
  color: var(--color-text);
  margin-bottom: var(--space-sm);
}

.hero-inner p {
  max-width: 560px;
  margin: 0 auto;
  font-size: 1.05rem;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.hero-actions {
  margin-top: var(--space-xl);
}

.path-section,
.outcomes-nav-section,
.outcome-details-section,
.portfolio-section {
  padding: var(--space-3xl) 0;
}

.outcomes-nav-section,
.portfolio-section {
  background: var(--color-bg-alt);
}

.section-header {
  max-width: 640px;
  margin-bottom: var(--space-2xl);
}

.section-header.compact {
  margin-bottom: var(--space-xl);
}

.section-kicker {
  display: inline-block;
  margin-bottom: var(--space-xs);
  color: var(--color-act);
  font-size: 0.8rem;
  font-weight: 700;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-text);
  margin-bottom: var(--space-xs);
}

.section-header p {
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

.step-card {
  padding: var(--space-xl);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.step-num {
  display: inline-flex;
  margin-bottom: var(--space-lg);
  color: var(--color-act);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 900;
}

.step-card h3 {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--color-text);
  margin-bottom: var(--space-sm);
}

.step-card p {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.7;
}

.outcome-card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

.outcome-card {
  display: flex;
  width: 100%;
  gap: var(--space-md);
  padding: var(--space-xl);
  text-align: left;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out);
}

.outcome-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-act-light);
  box-shadow: var(--shadow-md);
}

.outcome-card:focus-visible {
  outline: 3px solid var(--color-act-light);
  outline-offset: 3px;
}

.outcome-icon {
  flex-shrink: 0;
  font-size: 2.2rem;
  line-height: 1;
}

.outcome-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.outcome-title {
  color: var(--color-text);
  font-size: 1.1rem;
  font-weight: 800;
}

.outcome-subtitle {
  color: var(--color-text-muted);
  font-size: 0.82rem;
  font-weight: 600;
}

.outcome-desc {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
}

.outcome-stat {
  display: flex;
  align-items: baseline;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
}

.outcome-stat strong {
  color: var(--color-act);
  font-family: var(--font-mono);
  font-size: 1.5rem;
  font-weight: 900;
}

.outcome-stat span {
  color: var(--color-text-muted);
  font-size: 0.8rem;
}

.outcome-details-section {
  background: var(--color-bg-card);
}

.detail-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: var(--space-2xl);
  padding: var(--space-2xl);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  scroll-margin-top: 96px;
}

.detail-panel + .detail-panel {
  margin-top: var(--space-xl);
}

.detail-badge {
  display: inline-flex;
  margin-bottom: var(--space-md);
  padding: 0.25rem 0.7rem;
  color: var(--color-act);
  background: var(--color-act-bg);
  border-radius: var(--radius-full);
  font-size: 0.8rem;
  font-weight: 700;
}

.detail-main h2 {
  color: var(--color-text);
  font-size: 1.45rem;
  font-weight: 800;
  margin-bottom: var(--space-md);
}

.detail-main p {
  color: var(--color-text-secondary);
  line-height: 1.8;
}

.detail-highlights {
  margin-top: var(--space-xl);
}

.detail-highlights h3,
.case-box h3 {
  color: var(--color-text);
  font-size: 1rem;
  font-weight: 800;
  margin-bottom: var(--space-md);
}

.detail-highlights ul {
  display: grid;
  gap: var(--space-sm);
  padding-left: 1.2rem;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.detail-side {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.detail-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-sm);
}

.detail-stat {
  padding: var(--space-md);
  background: var(--color-act-bg);
  border-radius: var(--radius-md);
  text-align: center;
}

.detail-stat strong {
  display: block;
  color: var(--color-act);
  font-family: var(--font-mono);
  font-size: 1.3rem;
  font-weight: 900;
  margin-bottom: 0.1rem;
}

.detail-stat span {
  color: var(--color-text-secondary);
  font-size: 0.78rem;
}

.case-box {
  padding: var(--space-lg);
  background: var(--color-bg-alt);
  border-radius: var(--radius-lg);
}

.case-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.case-item {
  padding: 0.35rem 0.7rem;
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: 0.8rem;
}

.portfolio-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-xl);
  padding: var(--space-xl) var(--space-2xl);
  background: var(--color-act-bg);
  border: 1px solid rgba(16, 185, 129, 0.15);
  border-radius: var(--radius-lg);
}

.portfolio-content h3 {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--color-text);
  margin-bottom: var(--space-xs);
}

.portfolio-content p {
  max-width: 640px;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin-bottom: var(--space-md);
}

.portfolio-features {
  display: flex;
  gap: var(--space-lg);
  flex-wrap: wrap;
}

.pf-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.pf-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

@media (max-width: 960px) {
  .steps-grid,
  .outcome-card-grid,
  .detail-panel {
    grid-template-columns: 1fr;
  }

  .detail-side {
    max-width: none;
  }
}

@media (max-width: 768px) {
  .section-header {
    text-align: left;
  }

  .outcome-card {
    flex-direction: column;
  }

  .detail-panel {
    padding: var(--space-xl);
  }

  .detail-stats {
    grid-template-columns: 1fr;
  }

  .portfolio-card {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
