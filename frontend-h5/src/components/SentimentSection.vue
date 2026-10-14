<template>
  <section class="card" id="sec-sentiment">
    <h2 class="section-title">舆情分析</h2>

    <div class="total-card">
      <div>
        <div class="t-label">舆情总量</div>
        <div class="t-nums">
          <span>总计 <b>{{ totals.total }}</b></span>
          <span>中性 <b class="neu">{{ totals.neutral }}</b></span>
        </div>
        <div class="t-nums">
          <span>正面 <b class="pos">{{ totals.positive }}</b></span>
          <span>负面 <b class="neg">{{ totals.negative }}</b></span>
        </div>
      </div>
      <div ref="donutEl" class="donut"></div>
    </div>

    <div class="mini-stats">
      <div>
        <div class="m-label">目标企业舆情</div>
        <div class="m-vals">
          <span class="pos">正 {{ targetStats.pos }}</span>
          <span class="neu">中 {{ targetStats.neu }}</span>
          <span class="neg">负 {{ targetStats.neg }}</span>
        </div>
      </div>
      <div>
        <div class="m-label">行业整体舆情</div>
        <div class="m-vals">
          <span class="pos">正 {{ totals.positive }}</span>
          <span class="neu">中 {{ totals.neutral }}</span>
          <span class="neg">负 {{ totals.negative }}</span>
        </div>
      </div>
    </div>

    <h3 class="sub-title">舆情明细</h3>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>发布时间</th><th>类型</th><th>标题</th><th>正/负面</th>
            <th>企业名称</th><th>内容摘要</th><th>信息来源</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in pageItems" :key="s.id">
            <td>{{ s.publish_date }}</td>
            <td>{{ s.item_type }}</td>
            <td class="clip" :title="s.title">{{ s.title }}</td>
            <td><span :class="['pol', s.polarity]">{{ polLabel(s.polarity) }}</span></td>
            <td class="clip" :title="s.company_name">{{ s.company_name }}</td>
            <td class="clip wide" :title="s.summary">{{ s.summary }}</td>
            <td class="clip" :title="s.source">{{ s.source }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="pager">
      <button :disabled="page <= 1" @click="page--">上一页</button>
      <span>共 {{ items.length }} 条 · 第 {{ page }}/{{ pages }} 页</span>
      <button :disabled="page >= pages" @click="page++">下一页</button>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  items: { type: Array, default: () => [] },
  targetName: { type: String, default: '' },
})

const page = ref(1)
const per = 10
const pages = computed(() => Math.max(1, Math.ceil(props.items.length / per)))
const pageItems = computed(() => props.items.slice((page.value - 1) * per, page.value * per))

const totals = computed(() => {
  const t = { total: props.items.length, positive: 0, neutral: 0, negative: 0 }
  for (const it of props.items) t[it.polarity] = (t[it.polarity] || 0) + 1
  return t
})

const targetStats = computed(() => {
  const s = { pos: 0, neu: 0, neg: 0 }
  for (const it of props.items) {
    if (it.company_name !== props.targetName) continue
    if (it.polarity === 'positive') s.pos++
    else if (it.polarity === 'negative') s.neg++
    else s.neu++
  }
  return s
})

function polLabel(p) {
  return p === 'positive' ? '正面' : p === 'negative' ? '负面' : '中性'
}

const donutEl = ref(null)
let chart = null

function renderDonut() {
  if (!chart) return
  const t = totals.value
  chart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['52%', '74%'],
      center: ['50%', '50%'],
      label: { show: false },
      data: [
        { value: t.positive, name: '正面', itemStyle: { color: '#1fa971' } },
        { value: t.neutral, name: '中性', itemStyle: { color: '#c3c8da' } },
        { value: t.negative, name: '负面', itemStyle: { color: '#e5484d' } },
      ],
    }],
  })
}

onMounted(() => {
  chart = echarts.init(donutEl.value)
  renderDonut()
})
watch(totals, renderDonut)
onBeforeUnmount(() => chart && chart.dispose())
</script>

<style scoped>
.sub-title { font-size: 16px; font-weight: 700; margin: 22px 0 10px; }
.total-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid #efe9fb;
  border-radius: 14px;
  padding: 16px;
  background: linear-gradient(135deg, #faf8ff, #ffffff);
  margin-top: 12px;
}
.t-label { font-weight: 700; font-size: 15px; margin-bottom: 8px; }
.t-nums { display: flex; gap: 18px; font-size: 13px; color: var(--c-sub); margin: 6px 0; }
.t-nums b { color: var(--c-text); margin-left: 2px; }
b.pos { color: var(--c-success); }
b.neg { color: var(--c-danger); }
b.neu { color: #8a8fa3; }
.donut { width: 130px; height: 130px; flex-shrink: 0; }
.mini-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 12px;
}
.mini-stats > div {
  border: 1px solid #efe9fb;
  border-radius: 14px;
  padding: 12px 14px;
}
.m-label { font-size: 12.5px; color: var(--c-sub); }
.m-vals { display: flex; gap: 12px; margin-top: 6px; font-size: 13.5px; font-weight: 600; }
.m-vals .pos { color: var(--c-success); }
.m-vals .neg { color: var(--c-danger); }
.m-vals .neu { color: #8a8fa3; }
.pol { font-weight: 600; }
.pol.positive { color: var(--c-success); }
.pol.negative { color: var(--c-danger); }
.pol.neutral { color: #8a8fa3; }
.clip {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
}
.clip.wide { max-width: 240px; }
</style>
