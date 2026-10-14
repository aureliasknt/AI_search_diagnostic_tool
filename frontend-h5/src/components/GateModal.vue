<template>
  <teleport to="body">
    <transition name="fade">
      <div class="mask" @click.self="$emit('close')">
        <div class="modal">
          <button class="x" @click="$emit('close')" aria-label="关闭">×</button>
          <h3 class="m-title">查看完整报告</h3>
          <p class="m-sub">输入手机号并验证，即可查看竞品对比、舆情分析与优化建议全文，并支持导出PDF。</p>

          <label class="field">
            <span>手机号 <b>*</b></span>
            <div class="row">
              <input v-model.trim="phone" type="tel" maxlength="11" placeholder="请输入11位手机号" />
              <button class="code-btn" :disabled="countdown > 0 || sending" @click="onSend">
                {{ countdown > 0 ? `${countdown}s后重发` : '获取验证码' }}
              </button>
            </div>
          </label>

          <label class="field">
            <span>短信验证码 <b>*</b></span>
            <input v-model.trim="code" type="tel" maxlength="6" placeholder="6位验证码" />
            <em v-if="devCode" class="dev-tip">开发模式验证码：{{ devCode }}</em>
          </label>

          <div class="row-2">
            <label class="field">
              <span>姓名（选填）</span>
              <input v-model.trim="name" maxlength="20" placeholder="怎么称呼您" />
            </label>
            <label class="field">
              <span>公司名称（选填）</span>
              <input v-model.trim="company" maxlength="50" placeholder="您的公司" />
            </label>
          </div>

          <label class="consent">
            <input type="checkbox" v-model="consent" />
            <span>我已阅读并同意<a @click.prevent="showPrivacy = true">《个人信息保护政策》</a>，授权将联系方式用于本报告服务与业务跟进。</span>
          </label>

          <button class="submit" :disabled="loading" @click="onVerify">
            {{ loading ? '验证中…' : '解锁完整报告' }}
          </button>
          <p v-if="error" class="err">{{ error }}</p>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showPrivacy" class="mask" @click.self="showPrivacy = false">
        <div class="modal">
          <button class="x" @click="showPrivacy = false">×</button>
          <h3 class="m-title">个人信息保护政策</h3>
          <p class="privacy">
            为向您提供本诊断报告及后续服务，我们会收集您的手机号码等联系信息。
            信息仅用于报告查看授权、服务通知及业务跟进，存储时进行加密处理，
            并按照《中华人民共和国个人信息保护法》等相关法律法规进行最小化收集与保护。
            您有权随时要求查询、更正或删除您的个人信息。
          </p>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { sendCode, verify } from '../api/client'

const props = defineProps({ reportCode: { type: String, required: true } })
const emit = defineEmits(['close', 'unlocked'])

const phone = ref('')
const code = ref('')
const name = ref('')
const company = ref('')
const consent = ref(false)
const devCode = ref('')
const error = ref('')
const sending = ref(false)
const loading = ref(false)
const countdown = ref(0)
const showPrivacy = ref(false)
let timer = null

async function onSend() {
  error.value = ''
  sending.value = true
  try {
    const { data } = await sendCode(props.reportCode, phone.value)
    devCode.value = data.dev_code || ''
    countdown.value = 60
    timer = setInterval(() => {
      countdown.value -= 1
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    error.value = e?.response?.data?.detail || '发送失败，请稍后重试'
  } finally {
    sending.value = false
  }
}

async function onVerify() {
  error.value = ''
  if (!consent.value) {
    error.value = '请先勾选并同意《个人信息保护政策》'
    return
  }
  loading.value = true
  try {
    const { data } = await verify(props.reportCode, {
      phone: phone.value, code: code.value, name: name.value, company: company.value,
      consent: consent.value,
    })
    emit('unlocked', data.unlock_token)
  } catch (e) {
    error.value = e?.response?.data?.detail || '验证失败，请检查验证码'
  } finally {
    loading.value = false
  }
}

onBeforeUnmount(() => timer && clearInterval(timer))
</script>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  background: rgba(24, 12, 48, 0.6);
  z-index: 100;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.modal {
  width: 100%;
  max-width: 750px;
  background: #fff;
  border-radius: 22px 22px 0 0;
  padding: 24px 20px 32px;
  position: relative;
  max-height: 88vh;
  overflow-y: auto;
}
.x {
  position: absolute;
  top: 12px;
  right: 16px;
  border: 0;
  background: #f1eef8;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-size: 18px;
  color: #6a6f82;
}
.m-title { margin: 0; font-size: 20px; }
.m-sub { color: var(--c-sub); font-size: 13px; line-height: 1.8; }
.field { display: block; margin-top: 14px; font-size: 13px; color: #4c5165; }
.field b { color: var(--c-danger); }
.field input {
  width: 100%;
  margin-top: 7px;
  border: 1px solid #e3ddf3;
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 15px;
  outline: none;
}
.field input:focus { border-color: var(--c-primary-light); }
.row { display: flex; gap: 10px; }
.row input { flex: 1; }
.code-btn {
  border: 1px solid #d9c9fa;
  background: #f6f1ff;
  color: var(--c-primary);
  border-radius: 12px;
  padding: 0 14px;
  font-size: 13px;
  white-space: nowrap;
}
.code-btn:disabled { color: #b3a8d4; }
.dev-tip { display: block; font-style: normal; color: var(--c-warning); font-size: 12px; margin-top: 6px; }
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.consent { display: flex; gap: 8px; margin-top: 16px; font-size: 12px; color: var(--c-sub); line-height: 1.7; }
.consent input { margin-top: 3px; }
.consent a { color: var(--c-primary); }
.submit {
  width: 100%;
  margin-top: 18px;
  border: 0;
  background: var(--c-gradient);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  padding: 14px;
  border-radius: 999px;
  box-shadow: 0 8px 22px rgba(124, 58, 237, 0.4);
}
.submit:disabled { opacity: 0.6; }
.err { color: var(--c-danger); font-size: 13px; text-align: center; margin: 12px 0 0; }
.privacy { font-size: 13px; color: #4c5165; line-height: 2; }
</style>
