<template>
  <div>
    <div class="toolbar">
      <el-input v-model="q" placeholder="搜索姓名 / 公司 / 手机号(掩码)" clearable style="width: 260px" @change="load" />
      <el-select v-model="status" placeholder="跟进状态" clearable style="width: 140px" @change="load">
        <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-button @click="load">刷新</el-button>
      <el-button type="success" :loading="exporting" @click="doExport">导出 Excel</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="phone_mask" label="手机号" width="130">
        <template #default="{ row }"><code>{{ row.phone_mask }}</code></template>
      </el-table-column>
      <el-table-column prop="name" label="姓名" width="100" />
      <el-table-column prop="company" label="公司" min-width="140" show-overflow-tooltip />
      <el-table-column label="来源报告" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.report_company }}
          <el-tag size="small" type="info" effect="plain">#{{ row.diagnosis_id }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="填写时间" width="165">
        <template #default="{ row }">{{ (row.verified_at || '').replace('T', ' ') }}</template>
      </el-table-column>
      <el-table-column label="跟进状态" width="150">
        <template #default="{ row }">
          <el-select :model-value="row.status" size="small" @change="(v) => setStatus(row, v)">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="导出PDF" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.exported_pdf" type="success" size="small">是</el-tag>
          <span v-else class="muted">否</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination class="pager" layout="prev, pager, next, total" :total="total"
                   v-model:current-page="page" :page-size="pageSize" @current-change="load" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { client } from '../stores/auth'

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const q = ref('')
const status = ref('')
const statusOptions = ref([])
const loading = ref(false)
const exporting = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await client.get('/prospects', {
      params: { page: page.value, page_size: pageSize, q: q.value || undefined, status: status.value || undefined },
    })
    rows.value = data.items
    total.value = data.total
    statusOptions.value = data.status_options
  } finally {
    loading.value = false
  }
}

async function setStatus(row, value) {
  await client.patch(`/prospects/${row.id}`, { status: value })
  row.status = value
  ElMessage.success('已更新跟进状态')
}

async function doExport() {
  exporting.value = true
  try {
    const { data } = await client.get('/prospects/export', {
      params: { status: status.value || undefined }, responseType: 'blob',
    })
    const url = URL.createObjectURL(new Blob([data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `线索_${new Date().toISOString().slice(0, 10)}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('Excel 已导出（手机号已掩码）')
  } finally {
    exporting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.pager { margin-top: 16px; justify-content: flex-end; }
.muted { color: #b6bacb; }
code { font-family: 'JetBrains Mono', Consolas, monospace; }
</style>
