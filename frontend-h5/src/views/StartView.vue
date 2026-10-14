<template>
  <div class="page">
    <HeroBanner company="免费体验" />

    <div class="card intro-card">
      <p class="intro-title">测一测你的品牌在AI搜索里排第几</p>
      <p class="intro-sub">输入企业名称，AI将围绕你的行业向豆包发起100余次真实提问采样，生成品牌可见度诊断报告。</p>
    </div>

    <div class="card form-card">
      <label class="fld">
        <span class="fld-label">企业名称</span>
        <input v-model.trim="company" class="fld-input" maxlength="100"
               placeholder="请输入营业执照上的企业全称，如：合肥某某科技有限公司" />
      </label>

      <button class="btn ghost" :disabled="!company || guessing" @click="doGuess">
        <span v-if="guessing" class="mini-spinner"></span>
        {{ guessing ? 'AI正在推测…' : '✨ AI推测行业' }}
      </button>
      <p class="hint">AI将根据企业名称自动推测行业、产品与搜索关键词，推测结果可手动修改。</p>

      <template v-if="guessed">
        <label class="fld">
          <span class="fld-label">所属行业</span>
          <input v-model.trim="form.industry" class="fld-input" maxlength="100" placeholder="如：污水处理设备制造" />
        </label>
        <label class="fld">
          <span class="fld-label">主营产品 / 服务</span>
          <input v-model.trim="form.products" class="fld-input" maxlength="255" placeholder="如：污水处理设备、一体化净水设备" />
        </label>

        <div class="fld">
          <span class="fld-label">搜索关键词 <em class="req">至少1个</em></span>
          <div class="chips">
            <span v-for="(k, i) in form.keywords" :key="k + i" class="chip">
              {{ k }}
              <button class="chip-x" @click="form.keywords.splice(i, 1)">×</button>
            </span>
          </div>
          <div class="chip-add">
            <input v-model.trim="newKw" class="fld-input sm" maxlength="50" placeholder="添加关键词，回车确认"
                   @keyup.enter="addKeyword" />
            <button class="btn tiny" :disabled="!newKw" @click="addKeyword">添加</button>
          </div>
        </div>

        <div class="fld">
          <span class="fld-label">竞品企业 <em class="opt">选填，可修改</em></span>
          <div class="chips">
            <span v-for="(c, i) in form.competitors" :key="c + i" class="chip gray">
              {{ c }}
              <button class="chip-x" @click="form.competitors.splice(i, 1)">×</button>
            </span>
            <span v-if="!form.competitors.length" class="chip-empty">未填写将由报告仅分析本品牌</span>
          </div>
          <div class="chip-add">
            <input v-model.trim="newComp" class="fld-input sm" maxlength="100" placeholder="添加竞品企业全称，回车确认"
                   @keyup.enter="addCompetitor" />
            <button class="btn tiny" :disabled="!newComp" @click="addCompetitor">添加</button>
          </div>
        </div>
      </template>

      <p v-if="error" class="err">{{ error }}</p>

      <button class="btn primary" :disabled="!canStart || starting" @click="doStart">
        <span v-if="starting" class="mini-spinner"></span>
        {{ starting ? '正在生成诊断…' : '开始诊断' }}
      </button>
      <p v-if="starting" class="hint center">已提交！正在向豆包AI发起100余次提问采样，约需1-3分钟，即将自动进入报告页…</p>
    </div>

    <footer class="foot">
      <p>合肥汇智聚能科技有限公司 · GEO智能营销服务</p>
      <p class="foot-sub">本报告由AI搜索诊断系统生成</p>
    </footer>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { guessCompany, startDiagnosis } from '../api/client'
import HeroBanner from '../components/HeroBanner.vue'

const router = useRouter()
const company = ref('')
const guessing = ref(false)
const starting = ref(false)
const guessed = ref(false)
const error = ref('')
const newKw = ref('')
const newComp = ref('')
const form = reactive({ industry: '', products: '', keywords: [], competitors: [] })

const canStart = computed(() =>
  company.value.length >= 2 && form.keywords.length >= 1 && !starting.value)

async function doGuess() {
  error.value = ''
  guessing.value = true
  try {
    const { data } = await guessCompany(company.value)
    form.industry = data.industry || ''
    form.products = data.products || ''
    form.keywords = data.keywords || []
    form.competitors = data.competitors || []
    guessed.value = true
  } catch (e) {
    error.value = e?.response?.data?.detail || '推测失败，请稍后重试，也可以直接手动填写'
  } finally {
    guessing.value = false
  }
}

function addKeyword() {
  const k = newKw.value.trim()
  if (k && !form.keywords.includes(k) && form.keywords.length < 10) form.keywords.push(k)
  newKw.value = ''
}
function addCompetitor() {
  const c = newComp.value.trim()
  if (c && !form.competitors.includes(c) && form.competitors.length < 5) form.competitors.push(c)
  newComp.value = ''
}

async function doStart() {
  error.value = ''
  starting.value = true
  try {
    const { data } = await startDiagnosis({
      company_name: company.value,
      industry: form.industry,
      products: form.products,
      keywords: form.keywords,
      competitors: form.competitors,
    })
    router.push(`/r/${data.code}`)
  } catch (e) {
    error.value = e?.response?.data?.detail || '提交失败，请稍后重试'
    starting.value = false
  }
}
</script>

<style scoped>
.intro-card { padding: 18px 20px; }
.intro-title { margin: 0; font-size: 17px; font-weight: 800; }
.intro-sub { margin: 8px 0 0; font-size: 13px; color: var(--c-sub); line-height: 1.8; }
.form-card { padding: 20px; }
.fld { display: block; margin-top: 16px; }
.fld:first-child { margin-top: 0; }
.fld-label { display: block; font-size: 13.5px; font-weight: 600; margin-bottom: 8px; }
.req { font-style: normal; font-size: 11px; color: #e5484d; font-weight: 400; margin-left: 6px; }
.opt { font-style: normal; font-size: 11px; color: #9aa0b4; font-weight: 400; margin-left: 6px; }
.fld-input {
  width: 100%; box-sizing: border-box;
  border: 1.5px solid var(--c-border); border-radius: 12px;
  padding: 12px 14px; font-size: 14.5px; background: #fbfaff;
  outline: none; transition: border-color 0.2s;
}
.fld-input:focus { border-color: var(--c-primary); background: #fff; }
.fld-input.sm { flex: 1; padding: 9px 12px; font-size: 13.5px; }
.btn {
  width: 100%; border: 0; border-radius: 12px; padding: 13px;
  font-size: 15px; font-weight: 700; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.btn.ghost {
  margin-top: 14px; background: #f1eafe; color: var(--c-primary);
  border: 1.5px dashed #c9b6f7;
}
.btn.primary {
  margin-top: 20px; background: var(--c-gradient); color: #fff;
  box-shadow: 0 8px 20px rgba(124, 58, 237, 0.35);
}
.btn.tiny { width: auto; padding: 9px 16px; font-size: 13px; background: var(--c-gradient); color: #fff; border-radius: 10px; }
.hint { font-size: 12px; color: #9aa0b4; margin: 10px 0 0; line-height: 1.7; }
.hint.center { text-align: center; color: var(--c-primary); }
.err {
  margin: 14px 0 0; font-size: 13px; color: #e5484d;
  background: #fef1f1; border-radius: 10px; padding: 10px 12px;
}
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  display: inline-flex; align-items: center; gap: 4px;
  background: #f1eafe; color: var(--c-primary-deep);
  font-size: 12.5px; padding: 6px 6px 6px 12px; border-radius: 999px; font-weight: 600;
}
.chip.gray { background: #f2f4f8; color: #4b5064; }
.chip-x {
  border: 0; background: rgba(0,0,0,0.08); color: inherit;
  width: 18px; height: 18px; border-radius: 50%; cursor: pointer;
  font-size: 13px; line-height: 1; display: inline-flex; align-items: center; justify-content: center;
}
.chip-empty { font-size: 12px; color: #b0b5c6; }
.chip-add { display: flex; gap: 8px; margin-top: 10px; }
.mini-spinner {
  width: 15px; height: 15px; border-radius: 50%;
  border: 2.5px solid rgba(124, 58, 237, 0.25); border-top-color: var(--c-primary);
  animation: spin 0.8s linear infinite;
}
.btn.primary .mini-spinner { border-color: rgba(255,255,255,0.4); border-top-color: #fff; }
@keyframes spin { to { transform: rotate(360deg); } }
.foot { text-align: center; margin-top: 30px; color: #9aa0b4; font-size: 12px; line-height: 1.9; }
.foot-sub { opacity: 0.75; margin: 0; }
</style>
