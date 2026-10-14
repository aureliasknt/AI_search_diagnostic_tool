<template>
  <div class="login-wrap">
    <el-card class="login-card">
      <h2 class="title">AI搜索诊断系统</h2>
      <p class="sub">运营后台 · GEO Agent</p>
      <el-form @submit.prevent="onSubmit">
        <el-form-item>
          <el-input v-model="username" placeholder="用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" size="large"
                    show-password :prefix-icon="Lock" @keyup.enter="onSubmit" />
        </el-form-item>
        <el-button type="primary" size="large" class="btn" :loading="loading" @click="onSubmit">
          登录
        </el-button>
        <p v-if="error" class="err">{{ error }}</p>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Lock, User } from '@element-plus/icons-vue'
import { useAuth } from '../stores/auth'

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const router = useRouter()
const auth = useAuth()

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/diagnoses')
  } catch (e) {
    error.value = e?.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2e1065, #7c3aed);
}
.login-card { width: 380px; border-radius: 16px; }
.title { margin: 0; text-align: center; }
.sub { text-align: center; color: #8a8fa3; font-size: 13px; margin: 6px 0 22px; }
.btn { width: 100%; }
.err { color: #e5484d; text-align: center; font-size: 13px; margin: 12px 0 0; }
</style>
