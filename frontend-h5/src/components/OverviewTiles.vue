<template>
  <section class="card" id="sec-overview">
    <h2 class="section-title">数据总览</h2>
    <div class="ov-grid">
      <div class="ov score">
        <div class="ov-label">品牌得分</div>
        <div class="ov-value">{{ d.score?.toFixed(2) ?? '-' }}</div>
        <span class="cat" :class="catClass">{{ d.category }}</span>
      </div>
      <div class="ov">
        <div class="ov-label">AI提问次数</div>
        <div class="ov-value">{{ d.total_samples ?? 0 }}</div>
      </div>
      <div v-for="t in tiles" :key="t.label" class="ov">
        <div class="ov-label">{{ t.label }}</div>
        <div class="ov-value">{{ t.value }}</div>
        <div v-if="t.pct !== undefined" class="progress-track">
          <div class="progress-fill" :style="{ width: t.pct + '%' }"></div>
        </div>
      </div>
    </div>
    <p class="section-note">全部指标均来自本次诊断关键词对应的豆包AI回答样本。</p>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ d: { type: Object, required: true } })

const catClass = computed(() => {
  const c = props.d.category
  return c === '良好' ? 'good' : c === '一般' ? 'mid' : 'bad'
})

const tiles = computed(() => {
  const t = props.d.target || {}
  return [
    { label: '品牌提及率', value: `${t.mention_rate ?? 0}%`, pct: t.mention_rate ?? 0 },
    { label: '品牌提及次数', value: t.mention_count ?? 0 },
    { label: '正面/中性情绪', value: `${posNeu(t)}%`, pct: posNeu(t) },
    { label: '负面情感倾向', value: `${t.neg_ratio ?? 0}%`, pct: t.neg_ratio ?? 0 },
  ]
})

function posNeu(t) {
  const total = Math.max((t.pos_count ?? 0) + (t.neu_count ?? 0) + (t.neg_count ?? 0), 1)
  return Math.round(((t.pos_count ?? 0) + (t.neu_count ?? 0)) / total * 100)
}
</script>

<style scoped>
.ov-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 14px;
}
.ov {
  border: 1px solid #efe9fb;
  border-radius: 14px;
  padding: 14px;
  background: linear-gradient(180deg, #fbfaff, #ffffff);
}
.ov.score { grid-column: span 2; text-align: center; }
.ov-label { font-size: 12.5px; color: var(--c-sub); }
.ov-value { font-size: 26px; font-weight: 800; color: var(--c-primary-deep); margin-top: 4px; }
.cat {
  display: inline-block;
  margin-top: 6px;
  font-size: 12px;
  padding: 3px 14px;
  border-radius: 999px;
  color: #fff;
  background: #b6bccf;
}
.cat.good { background: linear-gradient(135deg, #16a34a, #4ade80); }
.cat.mid { background: linear-gradient(135deg, #d97706, #fbbf24); }
.cat.bad { background: linear-gradient(135deg, #dc2626, #f87171); }
</style>
