<template>
  <div v-loading="booting">
    <el-tabs v-model="tab">

      <el-tab-pane label="评分权重" name="weights">
        <el-card shadow="never" class="cfg-card">
          <p class="hint">综合得分 = 品牌提及率 × {{ weights.mention }}% + 提及位置 × {{ weights.position }}% + 情感倾向 × {{ weights.sentiment }}%。调整后的权重仅对之后完成的诊断生效。</p>
          <div class="slider-row" v-for="row in WEIGHT_ROWS" :key="row.key">
            <span class="slider-label">{{ row.label }}</span>
            <el-slider v-model="weights[row.key]" :min="0" :max="100" show-input />
          </div>
          <el-alert v-if="weightSum !== 100" type="warning" show-icon
                    :title="`当前合计 ${weightSum}%，建议调整为 100%`" style="margin-bottom: 14px" />
          <el-button type="primary" :loading="saving" @click="saveWeights">保存权重</el-button>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="提问模板" name="templates">
        <p class="hint">模板中的 <code>{kw}</code> 会被替换为诊断关键词；每个关键词取 3–5 个变体提问。</p>
        <simple-crud list-key="templates" :columns="[{ prop: 'text', label: '模板', minWidth: 320 }]"
                     :blank="{ text: '' }"
                     :fields="[{ key: 'text', label: '模板内容', placeholder: '例如：{kw}哪家好' }]" />
      </el-tab-pane>

      <el-tab-pane label="企业别名" name="aliases">
        <p class="hint">解析 AI 回答时，除企业全称外同时匹配这些别名（如简称），避免漏统计。多个别名用顿号「、」分隔。</p>
        <simple-crud list-key="aliases"
                     :columns="[{ prop: 'brand', label: '企业全称', minWidth: 220 },
                                 { prop: 'aliases', label: '别名', minWidth: 260, join: '、' }]"
                     :blank="{ brand: '', aliases: '' }"
                     :fields="[{ key: 'brand', label: '企业全称', placeholder: '安徽蓝天环保科技有限公司' },
                               { key: 'aliases', label: '别名（顿号分隔）', placeholder: '蓝天环保、蓝天科技' }]"
                     :serialize="(f) => ({ brand: f.brand, aliases: f.aliases.split(/[、,，]/).map((s) => s.trim()).filter(Boolean) })" />
      </el-tab-pane>

      <el-tab-pane label="问题推荐库" name="recommendations">
        <p class="hint">诊断完成后按指标匹配规则，为目标企业生成 2–5 张「分析问题 + 优化建议」卡片。指标：mention_rate 提及率、position_score 位置分、sentiment_score 情感分、composite 综合得分、neg_ratio 负面占比。</p>
        <rec-crud />
      </el-tab-pane>

      <el-tab-pane label="平台配置" name="platform">
        <el-form label-width="150px" class="cfg-card">
          <el-form-item label="AI 平台">
            <el-radio-group v-model="platform.provider">
              <el-radio-button value="auto">自动（按 API Key）</el-radio-button>
              <el-radio-button value="mock">模拟（开发演示）</el-radio-button>
              <el-radio-button value="doubao">豆包（火山方舟）</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="API Base URL">
            <el-input v-model="platform.base_url" :placeholder="platform.defaults?.base_url" />
          </el-form-item>
          <el-form-item label="模型">
            <el-input v-model="platform.model" :placeholder="platform.defaults?.model" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input v-model="platform.api_key" placeholder="留空则保持原值（不回显明文）" show-password type="password" />
          </el-form-item>
          <el-form-item label="Temperature">
            <el-input-number v-model="platform.temperature" :min="0" :max="2" :step="0.1" />
          </el-form-item>
          <el-form-item label="每关键词提问变体">
            <el-input-number v-model="platform.variants" :min="3" :max="5" />
          </el-form-item>
          <el-form-item label="采样轮数">
            <el-input-number v-model="platform.rounds" :min="2" :max="3" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="savePlatform">保存平台配置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="报告配置" name="report">
        <el-form label-width="150px" class="cfg-card">
          <el-form-item label="报告有效期（天）">
            <el-input-number v-model="report.expiry_days" :min="1" :max="3650" />
          </el-form-item>
          <el-form-item label="报告结论模板">
            <el-input v-model="report.conclusion_template" type="textarea" :rows="3" />
            <div class="hint" style="margin-top:6px">可用变量：{keywords} 关键词、{mention_rate} 提及率、{rank} 综合排名。</div>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="saveReport">保存报告配置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import {
  ElButton, ElInput, ElInputNumber, ElMessage, ElPopconfirm,
  ElSelect, ElOption, ElTable, ElTableColumn,
} from 'element-plus'
import { client } from '../stores/auth'

const WEIGHT_ROWS = [
  { key: 'mention', label: '品牌提及率' },
  { key: 'position', label: '提及位置' },
  { key: 'sentiment', label: '情感倾向' },
]
const METRICS = ['mention_rate', 'position_score', 'sentiment_score', 'composite', 'neg_ratio']
const OPS = ['<', '<=', '>', '>=', '==', '!=']

const tab = ref('weights')
const booting = ref(true)
const saving = ref(false)
const weights = reactive({ mention: 40, position: 30, sentiment: 30 })
const platform = reactive({ provider: 'auto', base_url: '', model: '', api_key: '', temperature: 0.5, variants: 3, rounds: 2, defaults: {} })
const report = reactive({ expiry_days: 90, conclusion_template: '' })
const weightSum = computed(() => Number(weights.mention) + Number(weights.position) + Number(weights.sentiment))

async function fetchList(key) {
  const { data } = await client.get(`/config/${key}`)
  return data.items
}
async function addItem(key, item) {
  await client.post(`/config/${key}`, item)
  ElMessage.success('已添加')
}
async function delItem(key, id) {
  await client.delete(`/config/${key}/${id}`)
  ElMessage.success('已删除')
}

async function saveWeights() {
  saving.value = true
  try {
    await client.put('/config/weights', { ...weights })
    ElMessage.success('权重已保存')
  } finally { saving.value = false }
}

async function savePlatform() {
  saving.value = true
  try {
    const { data } = await client.put('/config/platform', { ...platform })
    Object.assign(platform, data)
    ElMessage.success('平台配置已保存')
  } finally { saving.value = false }
}

async function saveReport() {
  saving.value = true
  try {
    await client.put('/config/report', { ...report })
    ElMessage.success('报告配置已保存')
  } finally { saving.value = false }
}

/* ---------- CRUD generik untuk templates & aliases ---------- */
const SimpleCrud = defineComponent({
  name: 'SimpleCrud',
  props: {
    listKey: { type: String, required: true },
    columns: { type: Array, required: true },
    fields: { type: Array, required: true },
    blank: { type: Object, required: true },
    serialize: { type: Function, default: (f) => f },
  },
  setup(props) {
    const items = ref([])
    const loading = ref(false)
    const form = reactive({ ...props.blank })

    async function reload() {
      loading.value = true
      try { items.value = await fetchList(props.listKey) } finally { loading.value = false }
    }
    async function onAdd() {
      for (const f of props.fields) {
        if (!String(form[f.key] ?? '').trim()) {
          ElMessage.warning(`请填写${f.label}`)
          return
        }
      }
      await addItem(props.listKey, props.serialize({ ...form }))
      Object.assign(form, props.blank)
      reload()
    }
    async function onDel(row) {
      await delItem(props.listKey, row.id)
      reload()
    }
    onMounted(reload)

    return () => h('div', { class: 'crud' }, [
      h(ElTable, { data: items.value, size: 'small', stripe: true }, () => [
        ...props.columns.map((c) => h(ElTableColumn, {
          prop: c.prop, label: c.label, minWidth: c.minWidth || 180, showOverflowTooltip: true,
        }, {
          default: ({ row }) => (c.join ? (row[c.prop] || []).join(c.join) : row[c.prop]),
        })),
        h(ElTableColumn, { label: '操作', width: 90 }, {
          default: ({ row }) => h(ElPopconfirm, { title: '确认删除？', onConfirm: () => onDel(row) }, {
            reference: () => h(ElButton, { link: true, type: 'danger', size: 'small' }, () => '删除'),
          }),
        }),
      ]),
      h('div', { class: 'crud-add' }, [
        ...props.fields.map((f) => h(ElInput, {
          modelValue: form[f.key],
          'onUpdate:modelValue': (v) => { form[f.key] = v },
          placeholder: f.placeholder || f.label,
          style: { width: '300px' },
          onKeydown: (e) => { if (e.key === 'Enter') onAdd() },
        })),
        h(ElButton, { type: 'primary', onClick: onAdd }, () => '添加'),
      ]),
    ])
  },
})

/* ---------- CRUD 规则推荐 (带条件编辑器) ---------- */
const RecCrud = defineComponent({
  name: 'RecCrud',
  setup() {
    const items = ref([])
    const loading = ref(false)
    const form = reactive({ metric: 'mention_rate', op: '<', value: 50, title: '', problem: '', suggestion: '' })

    async function reload() {
      loading.value = true
      try { items.value = await fetchList('recommendations') } finally { loading.value = false }
    }
    async function onAdd() {
      if (!form.title.trim() || !form.problem.trim()) {
        ElMessage.warning('请至少填写规则标题与问题描述')
        return
      }
      await addItem('recommendations', {
        metric: form.metric, op: form.op, value: Number(form.value),
        title: form.title, problem: form.problem, suggestion: form.suggestion, enabled: true,
      })
      Object.assign(form, { title: '', problem: '', suggestion: '' })
      reload()
    }
    async function toggle(row) {
      await client.put(`/config/recommendations/${row.id}`, { ...row, enabled: !row.enabled })
      reload()
    }
    onMounted(reload)

    return () => h('div', { class: 'crud' }, [
      h(ElTable, { data: items.value, size: 'small', stripe: true }, () => [
        h(ElTableColumn, { label: '触发条件', width: 230 }, {
          default: ({ row }) => `${row.metric} ${row.op} ${row.value}`,
        }),
        h(ElTableColumn, { prop: 'title', label: '卡片标题', minWidth: 150, showOverflowTooltip: true }),
        h(ElTableColumn, { prop: 'problem', label: '分析问题', minWidth: 240, showOverflowTooltip: true }),
        h(ElTableColumn, { prop: 'suggestion', label: '优化建议', minWidth: 240, showOverflowTooltip: true }),
        h(ElTableColumn, { label: '启用', width: 90 }, {
          default: ({ row }) => h(ElButton, {
            link: true, type: row.enabled ? 'success' : 'info', size: 'small', onClick: () => toggle(row),
          }, () => (row.enabled ? '已启用' : '已停用')),
        }),
        h(ElTableColumn, { label: '操作', width: 90 }, {
          default: ({ row }) => h(ElPopconfirm, { title: '确认删除？', onConfirm: async () => { await delItem('recommendations', row.id); reload() } }, {
            reference: () => h(ElButton, { link: true, type: 'danger', size: 'small' }, () => '删除'),
          }),
        }),
      ]),
      h('div', { class: 'rec-form' }, [
        h(ElSelect, { modelValue: form.metric, style: { width: '170px' }, 'onUpdate:modelValue': (v) => { form.metric = v } },
          () => METRICS.map((m) => h(ElOption, { value: m, label: m }))),
        h(ElSelect, { modelValue: form.op, style: { width: '90px' }, 'onUpdate:modelValue': (v) => { form.op = v } },
          () => OPS.map((o) => h(ElOption, { value: o, label: o }))),
        h(ElInputNumber, { modelValue: form.value, style: { width: '130px' }, 'onUpdate:modelValue': (v) => { form.value = v } }),
      ]),
      h('div', { class: 'crud-add' }, [
        h(ElInput, { modelValue: form.title, 'onUpdate:modelValue': (v) => { form.title = v }, placeholder: '卡片标题，如：品牌提及率偏低', style: { width: '240px' } }),
        h(ElInput, { modelValue: form.problem, 'onUpdate:modelValue': (v) => { form.problem = v }, placeholder: '分析问题描述', style: { width: '300px' } }),
        h(ElInput, { modelValue: form.suggestion, 'onUpdate:modelValue': (v) => { form.suggestion = v }, placeholder: '优化建议（可选）', style: { width: '300px' } }),
        h(ElButton, { type: 'primary', onClick: onAdd }, () => '添加规则'),
      ]),
    ])
  },
})

onMounted(async () => {
  try {
    const [w, p, r] = await Promise.all([
      client.get('/config/weights'),
      client.get('/config/platform'),
      client.get('/config/report'),
    ])
    Object.assign(weights, w.data)
    Object.assign(platform, p.data)
    Object.assign(report, r.data)
  } finally {
    booting.value = false
  }
})
</script>

<style scoped>
.cfg-card { max-width: 760px; }
.hint { color: #8a8fa3; font-size: 12.5px; line-height: 1.8; margin: 0 0 14px; }
.slider-row { display: flex; align-items: center; gap: 16px; margin-bottom: 8px; max-width: 640px; }
.slider-label { width: 96px; color: #454a5f; flex: none; }
code { background: #f2f0fa; padding: 1px 6px; border-radius: 4px; }
.crud-add { display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
.rec-form { display: flex; gap: 10px; margin-top: 14px; }
</style>
