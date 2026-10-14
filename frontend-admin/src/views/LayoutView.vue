<template>
  <el-container class="shell">
    <el-aside width="220px" class="side">
      <div class="brand">AI诊断 · 运营后台</div>
      <el-menu :default-active="route.path" router background-color="#231942"
               text-color="#b8b3d9" active-text-color="#ffffff">
        <el-menu-item index="/diagnoses">诊断管理</el-menu-item>
        <el-menu-item index="/prospects">线索管理</el-menu-item>
        <el-menu-item v-if="auth.role === 'admin'" index="/config">配置中心</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="head">
        <span class="who">{{ auth.username }}（{{ auth.role === 'admin' ? '管理员' : '销售' }}）</span>
        <el-button text type="danger" @click="auth.logout()">退出登录</el-button>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useAuth } from '../stores/auth'

const route = useRoute()
const auth = useAuth()
</script>

<style scoped>
.shell { min-height: 100vh; }
.side { background: #231942; }
.brand {
  color: #fff;
  font-weight: 700;
  font-size: 15px;
  padding: 20px 18px;
  letter-spacing: 1px;
}
.side :deep(.el-menu) { border-right: 0; }
.head {
  background: #fff;
  border-bottom: 1px solid #eee9f9;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}
.who { color: #5b5f73; font-size: 14px; }
</style>
