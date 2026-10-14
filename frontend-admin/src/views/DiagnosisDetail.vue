<template>
  <div v-loading="loading">
    <el-page-header :title="'诊断 #' + d.id" @back="$router.push('/diagnoses')" />

    <el-descriptions :column="2" border style="margin-top: 16px">
      <el-descriptions-item label="目标企业">{{ d.company_name }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="{ done: 'success', failed: 'danger', running: 'warning' }[d.status] || 'info'">
          {{ d.status_label }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="关键词">{{ (d.keywords || []).join('，') }}</el-descriptions-item>
      <el-descriptions-item label="竞品">{{ (d.competitors || []).join('，') || '—' }}</el-descriptions-item>
      <el-descriptions-item label="AI样本数">{{ d.total_samples }}</el-descriptions-item>
      <el-descriptions-item label="综合得分">
        <b v-if="d.score != null">{{ d.score.toFixed(2) }}（{{ d.category }}）</b><span v-else>—</span>
      </el-descriptions-item>
      <el-descriptions-item label="分享码">{{ d.share_code }}</el-descriptions-item>
      <el-descriptions-item label="报告结论">{{ d.conclusion || '—' }}</el-descriptions-item>
    </el-descriptions>

    <el-alert v-if="d.error" type="error" :title="d.error" show-icon style="margin-top: 12px" />

    <el-tabs v-model="tab" style="margin-top: 18px">
      <el-tab-pane label="品牌指标" name="metrics">
        <el-table :data="d.metrics" stripe>
          <el-table-column prop="rank" label="排名" width="64" />
          <el-table-column prop="brand_name" label="品牌" min-width="180" />
          <el-table-column label="目标" width="70">
            <template #default="{ row }">
              <el-tag v-if="row.is_target" type="primary" size="small">目标</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="mention_rate" label="提及率%" width="90" />
          <el-table-column prop="mention_count" label="提及次数" width="90" />
          <el-table-column prop="position_score" label="位置分" width="90" />
          <el-table-column label="情感(正/中/负)" width="130">
            <template #default="{ row }">{{ row.pos_count }} / {{ row.neu_count }} / {{ row.neg_count }}</template>
          </el-table-column>
          <el-table-column prop="sentiment_score" label="情感分" width="90" />
          <el-table-column prop="composite" label="综合得分" width="100" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="AI回答样本" name="samples">
        <el-table :data="d.samples" stripe max-height="520">
          <el-table-column prop="keyword" label="关键词" width="160" show-overflow-tooltip />
          <el-table-column prop="question" label="提问" min-width="220" show-overflow-tooltip />
          <el-table-column label="提及品牌" min-width="200">
            <template #default="{ row }">{{ mentioned(row).join('、') || '（未提及）' }}</template>
          </el-table-column>
          <el-table-column label="回答摘要" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">{{ (row.answer_text || '').slice(0, 120) }}</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="GEO营销对比" name="geo">
        <p class="hint">MVP阶段由运营人员手动录入各企业的GEO营销现状，保存后在客户端报告「GEO营销现状对比」表格中展示。</p>
        <el-table :data="geoRows" border size="small">
          <el-table-column label="企业名称" min-width="180">
            <template #default="{ row }">
              <el-input v-model="row.company_name" size="small" />
            </template>
          </el-table-column>
          <el-table-column v-for="col in GEO_COLS" :key="col.key" :label="col.label" min-width="120">
            <template #default="{ row }">
              <el-input v-model="row[col.key]" size="small" :placeholder="col.ph" />
            </template>
          </el-table-column>
          <el-table-column width="70">
            <template #default="{ $index }">
              <el-button link type="danger" size="small" @click="geoRows.splice($index, 1)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="margin-top: 12px; display: flex; gap: 10px">
          <el-button size="small" @click="addGeoRow">添加一行</el-button>
          <el-button type="primary" size="small" :loading="savingGeo" @click="saveGeo">保存</el-button>
        </div>
      </el-tab-pane>

      <el-tab-pane label="问题与建议" name="problems">
        <el-card v-for="(p, i) in d.problems" :key="i" shadow="never" style="margin-bottom: 12px">
          <template #header><b>{{ p.title }}</b></template>
          <p><el-tag type="primary" size="small">分析问题</el-tag> {{ p.problem_text }}</p>
          <p><el-tag type="success" size="small">优化建议</el-tag> {{ p.suggestion_text }}</p>
        </el-card>
        <el-empty v-if="!d.problems?.length" description="暂无（诊断完成后生成）" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { client } from '../stores/auth'

const GEO_COLS = [
  { key: 'stage', label: 'GEO布局阶段', ph: '成熟布局' },
  { key: 'channels', label: '核心搜索渠道', ph: '官网、行业平台' },
  { key: 'content_eco', label: '内容生态建设', ph: '知识库+自媒体' },
  { key: 'authority', label: '权威资质支持', ph: '检测报告、专利' },
  { key: 'visibility', label: 'AI搜索可见度', ph: '高/中/低' },
  { key: 'acquisition_model', label: '主要获客模式', ph: '自然搜索+转介绍' },
]

const route = useRoute()
const loading = ref(true)
const savingGeo = ref(false)
const tab = ref('metrics')
const d = ref({})
const geoRows = ref([])

function mentioned(row) {
  return Object.entries(row.parse_json || {})
    .filter(([, v]) => v?.mentioned)
    .map(([k]) => k)
}

function addGeoRow() {
  geoRows.value.push({
    company_name: '', stage: '', channels: '', content_eco: '',
    authority: '', visibility: '', acquisition_model: '',
  })
}

async function load() {
  loading.value = true
  try {
    const { data } = await client.get(`/diagnoses/${route.params.id}`)
    d.value = data
    geoRows.value = (data.geo_profiles || []).map((g) => ({ ...g }))
    if (geoRows.value.length === 0 && data.company_name) {
      geoRows.value.push({ company_name: data.company_name, stage: '', channels: '', content_eco: '', authority: '', visibility: '', acquisition_model: '' })
      for (const c of data.competitors || []) {
        geoRows.value.push({ company_name: c, stage: '', channels: '', content_eco: '', authority: '', visibility: '', acquisition_model: '' })
      }
    }
  } finally {
    loading.value = false
  }
}

async function saveGeo() {
  savingGeo.value = true
  try {
    const rows = geoRows.value.filter((r) => r.company_name.trim())
    await client.put(`/diagnoses/${d.value.id}/geo`, rows)
    ElMessage.success('已保存')
  } finally {
    savingGeo.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.hint { color: #8a8fa3; font-size: 12.5px; margin: 0 0 10px; }
</style>
