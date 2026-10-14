<template>
  <nav class="nav">
    <button v-for="t in tabs" :key="t.id" class="nav-item" :class="{ active: active === t.id }" @click="$emit('go', t.id)">
      <span class="nav-ico" v-html="t.icon"></span>
      <span>{{ t.label }}</span>
    </button>
  </nav>
</template>

<script setup>
defineProps({ active: { type: String, default: 'info' } })
defineEmits(['go'])

const I = (d) => `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`
const tabs = [
  { id: 'info', label: '分析说明', icon: I('<path d="M4 5h16v12H4z"/><path d="M8 9h8M8 13h5"/>') },
  { id: 'overview', label: '数据总览', icon: I('<path d="M4 20V10M10 20V4M16 20v-7M21 20H3"/>') },
  { id: 'queries', label: '查询详情', icon: I('<path d="M21 12a8 8 0 0 1-8 8H4l2-3a8 8 0 1 1 15-5z"/><path d="M8.5 11h7M8.5 14h4"/>') },
  { id: 'competitor', label: '竞品分析', icon: I('<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M7 6H4a3 3 0 0 0 3 5M17 6h3a3 3 0 0 1-3 5"/>') },
  { id: 'sentiment', label: '舆情分析', icon: I('<path d="M12 3l2.4 4.9 5.4.8-3.9 3.8.9 5.4-4.8-2.5-4.8 2.5.9-5.4L4.2 8.7l5.4-.8z"/>') },
]
</script>

<style scoped>
.nav {
  position: sticky;
  top: 0;
  z-index: 20;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
  padding: 10px 10px;
  background: rgba(246, 245, 251, 0.92);
  backdrop-filter: blur(8px);
}
.nav-item {
  border: 1px solid var(--c-border);
  background: #fff;
  border-radius: 14px;
  padding: 9px 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #5b5f73;
}
.nav-item.active {
  color: var(--c-primary);
  border-color: #c9b6f7;
  background: #f5f0ff;
  font-weight: 600;
}
.nav-ico { display: inline-flex; }
</style>
