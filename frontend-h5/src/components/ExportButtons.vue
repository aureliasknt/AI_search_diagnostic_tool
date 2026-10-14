<template>
  <div>
    <button v-if="!floating" class="btn" :disabled="!token" @click="onExport">
      导出PDF报告
    </button>
    <button v-else class="fab" :disabled="!token" @click="onExport" title="导出PDF">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 3v12M7 10l5 5 5-5M4 21h16" />
      </svg>
      <span>导出PDF</span>
    </button>
  </div>
</template>

<script setup>
import { pdfUrl } from '../api/client'

const props = defineProps({
  code: { type: String, required: true },
  token: { type: String, default: '' },
  floating: { type: Boolean, default: false },
})

function onExport() {
  window.open(pdfUrl(props.code, props.token), '_blank')
}
</script>

<style scoped>
.btn {
  width: 100%;
  border: 0;
  background: var(--c-gradient);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  padding: 14px;
  border-radius: 999px;
  box-shadow: 0 8px 22px rgba(124, 58, 237, 0.35);
  margin: 14px;
  width: calc(100% - 28px);
}
.btn:disabled { opacity: 0.55; }
.fab {
  position: fixed;
  right: 16px;
  bottom: 26px;
  z-index: 50;
  display: flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: var(--c-gradient);
  color: #fff;
  font-size: 13.5px;
  font-weight: 600;
  padding: 11px 18px;
  border-radius: 999px;
  box-shadow: 0 10px 26px rgba(124, 58, 237, 0.5);
}
.fab:disabled { opacity: 0.55; }
</style>
