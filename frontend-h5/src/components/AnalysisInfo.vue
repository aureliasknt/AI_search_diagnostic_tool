<template>
  <section class="card" id="sec-info">
    <h2 class="section-title">分析说明</h2>
    <dl class="info-list">
      <div><dt>公司名称</dt><dd>{{ d.company_name }}</dd></div>
      <div v-if="d.industry"><dt>所属行业</dt><dd>{{ d.industry }}</dd></div>
      <div v-if="d.products"><dt>主营产品</dt><dd>{{ d.products }}</dd></div>
      <div><dt>搜索关键词</dt><dd>{{ (d.keywords || []).join('，') }}</dd></div>
      <div><dt>分析状态</dt><dd><span class="ok">已完成</span></dd></div>
      <div><dt>AI提问次数</dt><dd>共 {{ d.total_samples }} 次提问 / {{ d.total_samples }} 条回答</dd></div>
      <div><dt>数据来源</dt><dd>豆包AI平台实时应答内容</dd></div>
    </dl>
  </section>
</template>

<script setup>
defineProps({ d: { type: Object, required: true } })
</script>

<style scoped>
.info-list { margin: 14px 0 0; }
.info-list > div {
  display: flex;
  gap: 12px;
  padding: 9px 0;
  font-size: 14px;
  border-bottom: 1px dashed #f0ecf8;
}
.info-list > div:last-child { border-bottom: 0; }
dt { color: var(--c-sub); min-width: 84px; }
dd { margin: 0; flex: 1; line-height: 1.6; }
.ok { color: var(--c-success); font-weight: 600; }
</style>
