<template>
  <section class="card xl-card" id="sec-queries">
    <!-- header gaya 报表明细 -->
    <div class="rpt-head">
      <div class="rpt-title">
        <span class="rpt-ico">📋</span> 查询详情
        <span class="rpt-help" title="本轮诊断向豆包AI发起的全部提问与回答原文">?</span>
      </div>
      <span class="rpt-filter">共 {{ filtered.length }} 条</span>
    </div>

    <!-- tab pill -->
    <div class="rpt-tabs">
      <button v-for="t in tabs" :key="t.id" class="rpt-tab"
              :class="{ active: tab === t.id }" @click="tab = t.id; page = 1">{{ t.label }}</button>
    </div>

    <!-- tabel daftar pertanyaan (mode ekspor PDF: tampilkan semua) -->
    <div class="rpt-table">
      <div class="rpt-tr rpt-th">
        <span class="c-idx">默认</span>
        <span class="c-kw">训练词</span>
        <span class="c-q">提问内容</span>
        <span class="c-op">操作</span>
      </div>
      <button v-for="(q, i) in isExport ? exportItems : pageItems" :key="i" class="rpt-tr"
              :disabled="isExport" @click="openIdx = isExport ? -1 : filteredIndex(start + i)">
        <span class="c-idx">{{ (isExport ? i : start + i) + 1 }}</span>
        <span class="c-kw">{{ q.keyword }}</span>
        <span class="c-q">{{ q.question }}</span>
        <span class="c-op"><span class="op-hand">👆</span></span>
      </button>
      <p v-if="!pageItems.length" class="rpt-empty">该分类下暂无提问</p>
    </div>

    <div v-if="!isExport" class="rpt-pager">
      <button class="pg-btn" :disabled="page === 1" @click="page--">‹</button>
      <span class="pg-info">共 {{ filtered.length }} 条 · {{ page }} / {{ totalPages }}</span>
      <button class="pg-btn" :disabled="page === totalPages" @click="page++">›</button>
    </div>

    <!-- ============ modal Q&A gaya chat Doubao ============ -->
    <div v-if="active" class="qa-mask" @click.self="openIdx = -1">
      <div class="qa-sheet">
        <div class="qa-head">
          <span class="qa-avatar">豆</span>
          <span class="qa-name">豆包</span>
          <button class="qa-close" @click="openIdx = -1">×</button>
        </div>

        <div class="qa-scroll">
          <h3 class="qa-title">{{ active.question }}</h3>
          <div class="qa-user-wrap">
            <div class="qa-user-bubble">{{ active.question }}</div>
          </div>

          <div class="qa-answer-label">豆包回答</div>
          <div class="qa-answer-bubble">
            <template v-for="(seg, j) in highlight(active.answer)" :key="j">
              <span v-if="seg.hit" class="brand-big">{{ seg.text }}</span>
              <template v-else>{{ seg.text }}</template>
            </template>
          </div>

          <div v-if="active.mentioned?.length" class="qa-mentioned">
            提及品牌：
            <span v-for="b in active.mentioned" :key="b" class="qa-brand-chip">{{ b }}</span>
          </div>
        </div>

        <a class="qa-cta" href="https://www.doubao.com/chat/" target="_blank" rel="noopener">💬 和豆包继续聊</a>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  queries: { type: Array, default: () => [] },
  aliasMap: { type: Object, default: () => ({}) },
  targetName: { type: String, default: '' },
})

const PAGE_SIZE = 20
const tab = ref('all')
const page = ref(1)
const openIdx = ref(-1)
const isExport = computed(() => useRoute().query.export === '1')
const exportItems = computed(() => props.queries)

const tabs = [
  { id: 'all', label: '全部提问' },
  { id: 'hit', label: '提到品牌' },
  { id: 'miss', label: '未提品牌' },
]

const filtered = computed(() => {
  if (tab.value === 'hit') return props.queries.filter((q) => q.mentioned?.length)
  if (tab.value === 'miss') return props.queries.filter((q) => !q.mentioned?.length)
  return props.queries
})
const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE_SIZE)))
const start = computed(() => (page.value - 1) * PAGE_SIZE)
const pageItems = computed(() => filtered.value.slice(start.value, start.value + PAGE_SIZE))
const active = computed(() => (openIdx.value >= 0 ? props.queries[openIdx.value] : null))

/** indeks pada array penuh (queries), dari indeks pada array filtered */
function filteredIndex(i) {
  return props.queries.indexOf(filtered.value[i])
}

/** Pecah jawaban jadi segmen; segmen berisi nama brand (atau alias) ditandai hit. */
function highlight(text) {
  const segs = []
  if (!text) return segs
  const spans = []
  for (const { terms } of collectBrands()) {
    for (const term of terms) {
      let from = 0
      while (true) {
        const idx = text.indexOf(term, from)
        if (idx < 0) break
        spans.push([idx, idx + term.length])
        from = idx + term.length
      }
    }
  }
  if (!spans.length) return [{ text, hit: false }]
  spans.sort((a, b) => a[0] - b[0])
  const merged = []
  for (const s of spans) {
    if (merged.length && s[0] <= merged[merged.length - 1][1]) {
      merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], s[1])
    } else {
      merged.push([s[0], s[1]])
    }
  }
  let cursor = 0
  for (const [a, b] of merged) {
    if (a > cursor) segs.push({ text: text.slice(cursor, a), hit: false })
    segs.push({ text: text.slice(a, b), hit: true })
    cursor = b
  }
  if (cursor < text.length) segs.push({ text: text.slice(cursor), hit: false })
  return segs
}

function collectBrands() {
  const names = new Set()
  for (const q of props.queries) for (const b of q.mentioned || []) names.add(b)
  for (const b of Object.keys(props.aliasMap)) names.add(b)
  if (props.targetName) names.add(props.targetName)
  return [...names].map((b) => {
    const aliases = props.aliasMap[b] || []
    const terms = [b, ...aliases].filter(Boolean).sort((x, y) => y.length - x.length)
    return { name: b, terms }
  })
}
</script>

<style scoped>
.xl-card { border: 1.5px solid #d9c8fa; }
/* header */
.rpt-head { display: flex; align-items: center; justify-content: space-between; }
.rpt-title { display: flex; align-items: center; gap: 7px; font-size: 16.5px; font-weight: 800; }
.rpt-ico { font-size: 18px; }
.rpt-help {
  width: 17px; height: 17px; border-radius: 50%; background: #efe9fb; color: var(--c-primary);
  font-size: 11.5px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center;
  cursor: help;
}
.rpt-filter {
  font-size: 12px; color: var(--c-primary); background: #f1eafe;
  border-radius: 999px; padding: 5px 14px; font-weight: 600;
}
/* tabs */
.rpt-tabs { display: flex; gap: 10px; margin-top: 14px; overflow-x: auto; padding-bottom: 2px; }
.rpt-tab {
  flex-shrink: 0; border: 0; border-radius: 999px; padding: 9px 18px;
  font-size: 13.5px; font-weight: 600; background: #f2eefb; color: #5b5f73; cursor: pointer;
}
.rpt-tab.active { background: var(--c-gradient); color: #fff; box-shadow: 0 6px 16px rgba(124, 58, 237, 0.35); }
/* table */
.rpt-table { margin-top: 14px; border: 1px solid #efe9fb; border-radius: 14px; overflow: hidden; }
.rpt-tr {
  width: 100%; display: flex; align-items: center; gap: 8px;
  border: 0; border-bottom: 1px dashed #f0ecf8; background: #fff;
  padding: 13px 12px; text-align: left; cursor: pointer; font-size: 13.5px;
}
.rpt-tr:last-child { border-bottom: 0; }
.rpt-tr:active { background: #f8f5ff; }
.rpt-th {
  background: #f5f1ff; color: var(--c-primary-deep); font-weight: 700; font-size: 13px;
  cursor: default; padding: 11px 12px;
}
.c-idx { width: 34px; flex-shrink: 0; text-align: center; color: #8b8fa3; }
.c-kw {
  flex-shrink: 0; max-width: 92px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-size: 11.5px; color: #6b6f85; background: #f2f4f8; border-radius: 6px; padding: 3px 8px;
}
.c-q { flex: 1; color: #33384d; line-height: 1.5; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.c-op { width: 40px; flex-shrink: 0; text-align: center; }
.op-hand { font-size: 19px; filter: drop-shadow(0 2px 3px rgba(245, 130, 32, 0.4)); }
.rpt-empty { text-align: center; color: #9aa0b4; font-size: 13px; padding: 24px 0; margin: 0; }
/* pager */
.rpt-pager { display: flex; align-items: center; justify-content: center; gap: 14px; margin-top: 16px; }
.pg-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1px solid var(--c-border); background: #fff;
  font-size: 17px; color: var(--c-primary); cursor: pointer; line-height: 1;
}
.pg-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.pg-info { font-size: 12.5px; color: #8b8fa3; }
/* ===== modal chat ===== */
.qa-mask {
  position: fixed; inset: 0; z-index: 90; background: rgba(30, 20, 60, 0.55);
  backdrop-filter: blur(3px); display: flex; align-items: center; justify-content: center; padding: 14px;
}
.qa-sheet {
  width: 100%; max-width: 480px; max-height: 88vh;
  background: #f7f6fb; border-radius: 22px;
  display: flex; flex-direction: column; overflow: hidden;
  box-shadow: 0 24px 60px rgba(50, 20, 100, 0.35);
}
.qa-head {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; background: #fff; flex-shrink: 0;
}
.qa-avatar {
  width: 38px; height: 38px; border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #6d28d9);
  color: #fff; font-weight: 800; font-size: 17px;
  display: inline-flex; align-items: center; justify-content: center;
}
.qa-name { font-size: 16.5px; font-weight: 800; flex: 1; }
.qa-close { border: 0; background: #f0eef6; width: 30px; height: 30px; border-radius: 50%; font-size: 17px; color: #5b5f73; cursor: pointer; }
.qa-scroll { overflow-y: auto; padding: 18px 16px 20px; }
.qa-title { margin: 0 0 14px; font-size: 19px; font-weight: 900; line-height: 1.5; color: #1c1f2e; }
.qa-user-wrap { display: flex; justify-content: flex-end; margin-bottom: 18px; }
.qa-user-bubble {
  max-width: 82%; background: #eceef3; color: #33384d;
  border-radius: 16px 16px 4px 16px; padding: 11px 15px;
  font-size: 14px; line-height: 1.6;
}
.qa-answer-label { font-size: 12px; font-weight: 700; color: #8b8fa3; margin-bottom: 8px; }
.qa-answer-bubble {
  background: #fff; border-radius: 4px 16px 16px 16px;
  padding: 16px 17px; font-size: 15px; line-height: 2.0; color: #2a2e3f;
  white-space: pre-wrap; word-break: break-word;
  box-shadow: 0 2px 10px rgba(80, 60, 140, 0.06);
}
.brand-big {
  color: #e03131; font-weight: 900; font-size: 1.45em; line-height: 1.4;
  letter-spacing: 0.5px;
}
.qa-mentioned { margin-top: 14px; font-size: 12.5px; color: #8b8fa3; }
.qa-brand-chip {
  display: inline-block; margin: 4px 0 0 6px;
  background: #f1eafe; color: var(--c-primary-deep);
  border-radius: 999px; padding: 3px 11px; font-weight: 600; font-size: 12px;
}
.qa-cta {
  flex-shrink: 0; margin: 0 auto 18px;
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--c-gradient); color: #fff; text-decoration: none;
  font-size: 14.5px; font-weight: 700;
  padding: 12px 30px; border-radius: 999px;
  box-shadow: 0 10px 24px rgba(124, 58, 237, 0.45);
}
</style>
