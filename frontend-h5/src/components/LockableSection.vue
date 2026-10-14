<template>
  <div class="lock-wrap" @click="$emit('open-gate')">
    <div class="placeholder">
      <div class="ph-head"></div>
      <div class="ph-line w80"></div>
      <div class="ph-line w60"></div>
      <div class="ph-block"></div>
    </div>
    <div class="overlay">
      <svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="#fff" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="10" width="16" height="10" rx="2.4" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      </svg>
      <div class="lock-title">该内容已锁定</div>
      <div class="lock-sub">输入手机号查看完整报告</div>
      <button class="lock-btn" @click.stop="$emit('open-gate')">解锁查看</button>
    </div>
  </div>
</template>

<script setup>
defineEmits(['open-gate'])
</script>

<style scoped>
.lock-wrap { position: relative; cursor: pointer; }
.placeholder { filter: blur(7px); opacity: 0.55; pointer-events: none; user-select: none; }
.ph-head { width: 40%; height: 18px; border-radius: 6px; background: #e9e4f6; }
.ph-line { height: 12px; border-radius: 6px; background: #efeaf9; margin-top: 12px; }
.ph-line.w80 { width: 80%; }
.ph-line.w60 { width: 60%; }
.ph-block { height: 120px; border-radius: 12px; background: #f2eefb; margin-top: 16px; }
.overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #fff;
  text-align: center;
}
.lock-title { font-size: 16px; font-weight: 700; text-shadow: 0 1px 8px rgba(76, 29, 149, 0.45); }
.lock-sub { font-size: 12.5px; color: #efe9fe; text-shadow: 0 1px 6px rgba(76, 29, 149, 0.4); }
.lock-btn {
  margin-top: 10px;
  border: 0;
  background: var(--c-gradient);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  padding: 9px 30px;
  border-radius: 999px;
  box-shadow: 0 6px 18px rgba(124, 58, 237, 0.45);
}
</style>
