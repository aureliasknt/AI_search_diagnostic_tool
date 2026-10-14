<template>
  <div class="kpi-grid">
    <div v-for="k in items" :key="k.label" class="kpi" :class="{ wide: k.wide }">
      <div class="kpi-label">{{ k.label }}</div>
      <div class="kpi-value" :style="{ color: k.color }">{{ k.value }}</div>
      <div v-if="k.sub" class="kpi-sub">{{ k.sub }}</div>
      <svg v-if="!k.wide" class="kpi-art" viewBox="0 0 96 30" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <g v-if="k.kind === 'bars'">
          <rect v-for="(h, i) in [10, 14, 18, 24]" :key="i" :x="8 + i * 14" :y="26 - h" width="8" :height="h" rx="2" :fill="k.color" :opacity="0.35 + i * 0.2" />
          <path d="M8 22 L36 14 L64 8 L88 3" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round" opacity="0.9" />
        </g>
        <g v-else-if="k.kind === 'line'">
          <polyline points="4,24 22,16 40,20 58,9 76,13 92,4" fill="none" :stroke="k.color" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
          <circle cx="92" cy="4" r="3.4" :fill="k.color" />
        </g>
        <g v-else>
          <circle cx="14" cy="22" r="3.4" :fill="k.color" />
          <circle cx="48" cy="12" r="3.4" :fill="k.color" opacity="0.75" />
          <circle cx="82" cy="20" r="3.4" :fill="k.color" opacity="0.5" />
          <path d="M14 22 L48 12 L82 20" stroke="#dcd5f0" stroke-width="1.6" stroke-dasharray="3 3" fill="none" />
        </g>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  target: { type: Object, default: () => ({}) },
  total: { type: Number, default: 0 },
})

const items = computed(() => {
  const t = props.target || {}
  return [
    { label: 'AI提问次数', value: String(props.total ?? 0), color: '#5b5bd6', kind: 'bars', wide: true,
      sub: `本轮诊断共向豆包AI提问 ${props.total ?? 0} 次，收集 ${props.total ?? 0} 条回答` },
    { label: '品牌提及率', value: `${t.mention_rate ?? 0}%`, color: '#7c3aed', kind: 'bars',
      sub: `${t.mention_rate ?? 0}% 的回答中提到了该品牌` },
    { label: '品牌提及次数', value: String(t.mention_count ?? 0), color: '#f59e0b', kind: 'line',
      sub: '品牌名在全部回答中出现的总次数' },
    { label: '正面/中性情绪', value: `${positiveNeutral(t)}%`, color: '#1fa971', kind: 'dots',
      sub: 'AI回答情感倾向为正面或中性的占比' },
    { label: '负面情感倾向', value: `${t.neg_ratio ?? 0}%`, color: '#e5484d', kind: 'dots',
      sub: 'AI回答情感倾向为负面的占比' },
  ]
})

function positiveNeutral(t) {
  const total = Math.max((t.pos_count ?? 0) + (t.neu_count ?? 0) + (t.neg_count ?? 0), 1)
  return Math.round(((t.pos_count ?? 0) + (t.neu_count ?? 0)) / total * 100)
}
</script>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 0 14px;
  margin-top: 12px;
}
.kpi {
  background: #fff;
  border: 1px solid var(--c-border);
  border-radius: 16px;
  box-shadow: var(--shadow);
  padding: 14px;
}
.kpi-label { font-size: 12.5px; color: var(--c-sub); }
.kpi-value { font-size: 26px; font-weight: 800; margin-top: 4px; }
.kpi.wide { grid-column: span 2; display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 14px; }
.kpi.wide .kpi-value { font-size: 30px; }
.kpi-sub { width: 100%; font-size: 11.5px; color: #9aa0b4; margin-top: 5px; line-height: 1.5; }
.kpi-art { width: 84px; height: 28px; margin-top: 8px; }
</style>
