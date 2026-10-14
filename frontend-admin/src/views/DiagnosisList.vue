<template>
  <div>
    <div class="toolbar">
      <el-input v-model="q" placeholder="搜索企业名称" clearable style="width: 240px" @change="load" />
      <el-select v-model="status" placeholder="状态" clearable style="width: 130px" @change="load">
        <el-option v-for="(label, key) in STATUS" :key="key" :label="label" :value="key" />
      </el-select>
      <el-button type="primary" @click="createOpen = true">新建诊断</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="64" />
      <el-table-column prop="company_name" label="目标企业" min-width="200" show-overflow-tooltip />
      <el-table-column label="关键词" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ (row.keywords || []).join('，') }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="tagType(row.status)">{{ row.status_label }}</el-tag>
          <el-progress v-if="row.status === 'running'" :percentage="row.progress" :stroke-width="6" style="margin-top:4px" />
        </template>
      </el-table-column>
      <el-table-column label="综合得分" width="110">
        <template #default="{ row }">
          <b v-if="row.score != null">{{ row.score.toFixed(2) }}</b>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="165">
        <template #default="{ row }">{{ row.created_at?.replace('T', ' ') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/diagnoses/${row.id}`)">详情</el-button>
          <el-button size="small" type="primary" plain :disabled="row.status !== 'done'"
                     @click="openShare(row)">分享</el-button>
          <el-button v-if="row.status === 'failed'" size="small" type="warning" @click="retry(row)">重试</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination class="pager" layout="prev, pager, next, total" :total="total"
                   v-model:current-page="page" :page-size="pageSize" @current-change="load" />

    <!-- 新建诊断 -->
    <el-dialog v-model="createOpen" title="新建诊断" width="560px">
      <el-form label-width="92px">
        <el-form-item label="企业名称" required>
          <el-input v-model="form.company_name" placeholder="客户企业全称" />
        </el-form-item>
        <el-form-item label="行业关键词" required>
          <el-select v-model="form.keywords" multiple filterable allow-create default-first-option
                     placeholder="输入后回车添加，可多个" style="width: 100%" />
        </el-form-item>
        <el-form-item label="竞品">
          <el-select v-model="form.competitors" multiple filterable allow-create default-first-option
                     placeholder="竞品企业名称，可多个" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createOpen = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="create">开始诊断（约1-3分钟）</el-button>
      </template>
    </el-dialog>

    <!-- 分享 -->
    <el-dialog v-model="shareOpen" title="分享报告给客户端" width="420px">
      <div class="share-body">
        <div class="qr" v-html="share.qr_svg"></div>
        <el-input v-model="share.url" readonly>
          <template #append>
            <el-button @click="copyUrl">复制链接</el-button>
          </template>
        </el-input>
        <p class="share-tip">链接可在微信中直接打开，无需安装与注册；客户端填写手机号后可查看完整报告。</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { client } from '../stores/auth'

const STATUS = { queued: '排队中', running: '进行中', done: '已完成', failed: '失败' }
const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const q = ref('')
const status = ref('')
const loading = ref(false)
const createOpen = ref(false)
const creating = ref(false)
const shareOpen = ref(false)
const share = reactive({ url: '', qr_svg: '' })
const form = reactive({ company_name: '', keywords: [], competitors: [] })
let pollTimer = null

function tagType(s) {
  return { queued: 'info', running: 'warning', done: 'success', failed: 'danger' }[s] || 'info'
}

async function load() {
  loading.value = true
  try {
    const { data } = await client.get('/diagnoses', {
      params: { page: page.value, page_size: pageSize, q: q.value || undefined, status: status.value || undefined },
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function create() {
  if (!form.company_name.trim() || form.keywords.length === 0) {
    ElMessage.warning('请填写企业名称与至少一个关键词')
    return
  }
  creating.value = true
  try {
    await client.post('/diagnoses', { ...form })
    ElMessage.success('诊断任务已创建，正在后台运行')
    createOpen.value = false
    Object.assign(form, { company_name: '', keywords: [], competitors: [] })
    load()
    schedulePoll()
  } finally {
    creating.value = false
  }
}

async function openShare(row) {
  const { data } = await client.get(`/diagnoses/${row.id}/share`)
  Object.assign(share, data)
  shareOpen.value = true
}

async function copyUrl() {
  try {
    await navigator.clipboard.writeText(share.url)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.info(share.url)
  }
}

async function retry(row) {
  await client.post(`/diagnoses/${row.id}/retry`)
  ElMessage.success('已重新排队')
  load()
  schedulePoll()
}

function schedulePoll() {
  clearTimeout(pollTimer)
  pollTimer = setTimeout(async () => {
    await load()
    if (rows.value.some((r) => r.status === 'running' || r.status === 'queued')) schedulePoll()
  }, 3000)
}

onMounted(() => {
  load()
  schedulePoll()
})
onBeforeUnmount(() => clearTimeout(pollTimer))
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.pager { margin-top: 16px; justify-content: flex-end; }
.share-body { display: flex; flex-direction: column; align-items: center; gap: 14px; }
.qr :deep(svg) { width: 180px; height: 180px; }
.share-tip { color: #8a8fa3; font-size: 12.5px; line-height: 1.8; margin: 0; }
</style>
