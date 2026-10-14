<template>
  <div class="page">
    <!-- status: laporan masih dibuat -->
    <div v-if="loadingState === 'running'" class="running">
      <HeroBanner :company="summary.company_name || ''" />
      <div class="card run-card">
        <div class="spinner"></div>
        <p class="run-title">{{ summary.status_label || '报告生成中' }}</p>
        <p class="run-sub">AI正在对豆包进行多轮提问采样，预计需要1-3分钟，请勿关闭页面。</p>
        <div class="progress-track"><div class="progress-fill" :style="{ width: summary.progress + '%' }"></div></div>
        <p class="run-pct">{{ summary.progress }}%</p>
      </div>
    </div>

    <!-- gagal -->
    <div v-else-if="loadingState === 'failed'" class="card fail-card">
      <p class="fail-title">报告生成失败</p>
      <p class="fail-sub">{{ summary.error || '请稍后重试' }}</p>
    </div>

    <!-- tidak ditemukan / kedaluwarsa -->
    <div v-else-if="loadingState === 'missing'" class="card fail-card">
      <p class="fail-title">{{ missingTitle }}</p>
    </div>

    <!-- laporan selesai -->
    <template v-else-if="loadingState === 'done'">
      <HeroBanner :company="summary.company_name" />

      <div class="card gauge-card">
        <div class="gauge-label">品牌得分</div>
        <ScoreGauge :score="summary.score || 0" :size="250" />
        <div class="gauge-cat">{{ summary.category }}</div>
      </div>

      <KpiCards :target="summary.target || {}" :total="summary.total_samples || 0" />

      <div class="conclusion card">
        <p class="conc-text">{{ summary.conclusion }}</p>
        <div v-if="!unlocked" class="unlock-banner" @click="gateOpen = true">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <rect x="4" y="10" width="16" height="10" rx="2.4" /><path d="M8 10V7a4 4 0 0 1 8 0v3" />
          </svg>
          输入手机号，查看完整诊断报告（竞品对比 / 舆情分析 / 优化建议）
        </div>
      </div>

      <SectionNav :active="activeSection" @go="scrollTo" />

      <AnalysisInfo :d="summary" />
      <OverviewTiles :d="summary" />

      <template v-if="unlocked">
        <QueryDetailSection :queries="full.queries" :alias-map="full.alias_map" :target-name="summary.company_name" />
        <CompetitorSection :metrics="full.metrics" :geo="full.geo_profiles" :company="summary.company_name" />
        <SentimentSection :items="full.sentiment_items" :target-name="summary.company_name" />
        <ProblemsSection :items="full.problems" />
      </template>
      <template v-else>
        <div class="card locked-sec" id="sec-queries">
          <h2 class="section-title">查询详情<span class="lock-chip">🔒 解锁后查看</span></h2>
          <LockableSection @open-gate="gateOpen = true" />
        </div>
        <div class="card locked-sec" id="sec-competitor">
          <h2 class="section-title">竞品分析<span class="lock-chip">🔒 解锁后查看</span></h2>
          <LockableSection @open-gate="gateOpen = true" />
        </div>
        <div class="card locked-sec" id="sec-sentiment">
          <h2 class="section-title">舆情分析<span class="lock-chip">🔒 解锁后查看</span></h2>
          <LockableSection @open-gate="gateOpen = true" />
        </div>
        <div class="card locked-sec" id="sec-problems">
          <h2 class="section-title">报告总结<span class="lock-chip">🔒 解锁后查看</span></h2>
          <LockableSection @open-gate="gateOpen = true" />
        </div>
      </template>

      <DisclaimerCard />

      <ExportButtons v-if="unlocked && !isExportMode" :code="code" :token="token" />
      <ExportButtons v-if="unlocked && !isExportMode" :code="code" :token="token" floating />
    </template>

    <GateModal v-if="gateOpen" :report-code="code" @close="gateOpen = false" @unlocked="onUnlocked" />

    <footer class="foot">
      <p>合肥汇智聚能科技有限公司 · GEO智能营销服务</p>
      <p class="foot-sub">本报告由AI搜索诊断系统生成</p>
    </footer>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getFull, getSummary, getToken, setToken } from '../api/client'
import HeroBanner from '../components/HeroBanner.vue'
import ScoreGauge from '../components/ScoreGauge.vue'
import KpiCards from '../components/KpiCards.vue'
import SectionNav from '../components/SectionNav.vue'
import AnalysisInfo from '../components/AnalysisInfo.vue'
import OverviewTiles from '../components/OverviewTiles.vue'
import QueryDetailSection from '../components/QueryDetailSection.vue'
import CompetitorSection from '../components/CompetitorSection.vue'
import SentimentSection from '../components/SentimentSection.vue'
import ProblemsSection from '../components/ProblemsSection.vue'
import DisclaimerCard from '../components/DisclaimerCard.vue'
import LockableSection from '../components/LockableSection.vue'
import GateModal from '../components/GateModal.vue'
import ExportButtons from '../components/ExportButtons.vue'

const route = useRoute()
const code = route.params.code
const isExportMode = computed(() => route.query.export === '1')
if (isExportMode.value && route.query.token) setToken(code, route.query.token)
// ?reset=1 → kunci ulang tampilan (lupa token tersimpan di browser ini)
if (route.query.reset === '1') setToken(code, '')

const summary = reactive({})
const full = reactive({ metrics: [], sentiment_items: [], problems: [], geo_profiles: [], queries: [], alias_map: {} })
const loadingState = ref('loading')
const missingTitle = ref('报告不存在或链接已失效')
const gateOpen = ref(false)
const unlocked = ref(false)
const token = ref(getToken(code))
const activeSection = ref('info')
let pollTimer = null

async function loadSummary() {
  try {
    const { data } = await getSummary(code)
    Object.assign(summary, data)
    if (data.status !== 'done') {
      loadingState.value = data.status === 'failed' ? 'failed' : 'running'
      pollTimer = setTimeout(loadSummary, 2000)
    } else {
      loadingState.value = 'done'
    }
  } catch (e) {
    loadingState.value = 'missing'
    missingTitle.value = e?.response?.status === 410
      ? '报告已超过有效期，请联系服务人员重新生成'
      : '报告不存在或链接已失效'
  }
}

async function tryUnlockFromStorage() {
  if (!token.value) return
  try {
    const { data } = await getFull(code, token.value)
    applyFull(data)
    unlocked.value = true
  } catch {
    token.value = ''
    setToken(code, '')
  }
}

function applyFull(data) {
  Object.assign(summary, data)
  full.metrics = data.metrics || []
  full.sentiment_items = data.sentiment_items || []
  full.problems = data.problems || []
  full.geo_profiles = data.geo_profiles || []
  full.queries = data.queries || []
  full.alias_map = data.alias_map || {}
}

function onUnlocked(newToken) {
  token.value = newToken
  setToken(code, newToken)
  gateOpen.value = false
  getFull(code, newToken).then(({ data }) => {
    applyFull(data)
    unlocked.value = true
  })
}

function scrollTo(id) {
  activeSection.value = id
  document.getElementById(`sec-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

let sectionObserver = null
function watchSections() {
  sectionObserver = new IntersectionObserver((entries) => {
    for (const en of entries) {
      if (en.isIntersecting) activeSection.value = en.target.id.replace('sec-', '')
    }
  }, { rootMargin: '-30% 0px -60% 0px' })
  ;['info', 'overview', 'queries', 'competitor', 'sentiment'].forEach((id) => {
    const el = document.getElementById(`sec-${id}`)
    if (el) sectionObserver.observe(el)
  })
}

onMounted(async () => {
  await loadSummary()
  if (loadingState.value === 'done') {
    await tryUnlockFromStorage()
    watchSections()
  }
})
onBeforeUnmount(() => {
  pollTimer && clearTimeout(pollTimer)
  sectionObserver && sectionObserver.disconnect()
})
</script>

<style scoped>
.gauge-card { text-align: center; padding-top: 24px; }
.gauge-label { font-size: 15px; color: var(--c-sub); letter-spacing: 3px; }
.gauge-cat { font-size: 14px; color: var(--c-primary); font-weight: 700; margin-top: -38px; }
.conclusion { padding: 18px 20px; }
.conc-text { margin: 0; font-size: 14.5px; line-height: 1.9; font-weight: 600; }
.lock-chip {
  margin-left: auto;
  font-size: 11px;
  font-weight: 500;
  color: var(--c-primary);
  background: #f1eafe;
  border-radius: 999px;
  padding: 3px 10px;
  letter-spacing: 0;
  flex-shrink: 0;
}
.unlock-banner {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  background: var(--c-gradient);
  color: #fff;
  border-radius: 14px;
  padding: 13px 14px;
  font-size: 13px;
  line-height: 1.6;
  box-shadow: 0 8px 20px rgba(124, 58, 237, 0.35);
}
.running .run-card { text-align: center; padding: 34px 22px; }
.spinner {
  width: 42px;
  height: 42px;
  margin: 0 auto;
  border: 4px solid #ece5fb;
  border-top-color: var(--c-primary);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.run-title { font-size: 17px; font-weight: 700; margin: 16px 0 4px; }
.run-sub { color: var(--c-sub); font-size: 13px; line-height: 1.8; margin: 0 0 16px; }
.run-pct { color: var(--c-primary); font-weight: 700; margin: 8px 0 0; }
.fail-card { text-align: center; padding: 44px 20px; margin-top: 40px; }
.fail-title { font-size: 17px; font-weight: 700; }
.fail-sub { color: var(--c-sub); font-size: 13.5px; }
.foot { text-align: center; margin-top: 30px; color: #9aa0b4; font-size: 12px; line-height: 1.9; }
.foot-sub { opacity: 0.75; margin: 0; }
</style>
