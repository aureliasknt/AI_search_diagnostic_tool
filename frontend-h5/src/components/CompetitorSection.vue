<template>
  <section class="card" id="sec-competitor">
    <h2 class="section-title">竞品分析</h2>
    <div class="tag-note">
      综合得分、品牌提及率、提及次数等指标，均来源于本报告搜索关键词对应的豆包AI问答样本数据。
      本次分析仅针对该组关键词下的问答内容开展，分析结论无法代表全行业整体真实情况，仅供业务参考使用。
    </div>

    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>排名</th><th>品牌名称</th><th>综合得分</th><th>品牌提及率</th><th>提及次数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in metrics" :key="m.brand_name" :class="{ hl: m.is_target }">
            <td>{{ m.rank }}</td>
            <td>{{ m.brand_name }}</td>
            <td>
              <span class="mini-bar" :class="{ gray: !m.is_target }"><i :style="{ width: m.composite + '%' }"></i></span>
              {{ m.composite.toFixed(2) }}
            </td>
            <td>{{ m.mention_rate }}%</td>
            <td>{{ m.mention_count }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <h3 class="sub-title">GEO营销现状对比</h3>
    <div class="table-wrap" v-if="geo.length">
      <table class="data-table">
        <thead>
          <tr>
            <th>企业名称</th><th>GEO布局阶段</th><th>核心搜索渠道</th><th>内容生态建设</th>
            <th>权威资质支持</th><th>AI搜索可见度</th><th>主要获客模式</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="g in geo" :key="g.company_name" :class="{ hl: g.company_name === company }">
            <td>{{ g.company_name }}</td>
            <td>{{ g.stage || '—' }}</td>
            <td>{{ g.channels || '—' }}</td>
            <td>{{ g.content_eco || '—' }}</td>
            <td>{{ g.authority || '—' }}</td>
            <td>{{ g.visibility || '—' }}</td>
            <td>{{ g.acquisition_model || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="section-note" v-else>GEO营销现状数据由运营人员在诊断管理中录入后展示。</p>
  </section>
</template>

<script setup>
defineProps({
  metrics: { type: Array, default: () => [] },
  geo: { type: Array, default: () => [] },
  company: { type: String, default: '' },
})
</script>

<style scoped>
.sub-title {
  font-size: 16px;
  font-weight: 700;
  margin: 22px 0 10px;
}
</style>
