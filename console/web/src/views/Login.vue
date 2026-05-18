<template>
  <div style="display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5">
    <el-card style="width: 400px">
      <template #header><h2 style="text-align: center; margin: 0">XY Console</h2></template>
      <el-form @submit.prevent="handleLogin">
        <el-form-item label="用户名">
          <el-input v-model="username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-button type="primary" style="width: 100%" :loading="loading" native-type="submit">登录</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const username = ref('')
const password = ref('')
const loading = ref(false)
const router = useRouter()
const userStore = useUserStore()

async function handleLogin() {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login(username.value, password.value)
    router.push('/')
  } catch {
    ElMessage.error('登录失败：用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>
