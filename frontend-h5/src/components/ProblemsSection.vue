<template>
  <section class="card" id="sec-problems">
    <h2 class="section-title">报告总结</h2>
    <article v-for="(p, i) in items" :key="i" class="problem">
      <h3 class="p-title">{{ p.title }}</h3>
      <div class="divider"></div>
      <span class="pill pill-problem">分析问题</span>
      <p class="p-text">{{ p.problem_text }}</p>
      <span class="pill pill-suggest">优化建议</span>
      <p class="p-text">{{ p.suggestion_text }}</p>
    </article>
  </section>
</template>

<script setup>
defineProps({ items: { type: Array, default: () => [] } })
</script>

<style scoped>
.problem {
  border: 1px solid #efe9fb;
  border-radius: 16px;
  padding: 18px;
  margin-top: 14px;
  background: linear-gradient(180deg, #fdfcff, #ffffff);
}
.p-title { margin: 0; font-size: 16.5px; line-height: 1.55; }
.divider { height: 1px; background: #f0ecf8; margin: 14px 0; }
.p-text { font-size: 13.5px; line-height: 1.9; color: #4c5165; margin: 10px 0 16px; }
</style>
