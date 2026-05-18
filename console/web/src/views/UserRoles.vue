<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">新增用户</el-button>
    </div>

    <el-table :data="users" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="display_name" label="显示名" />
      <el-table-column label="角色">
        <template #default="{ row }">
          <el-tag v-for="role in row.roles" :key="role" style="margin-right: 4px">{{ role }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingUser ? '编辑用户' : '新增用户'" width="500px">
      <el-form :model="form">
        <el-form-item label="用户名" v-if="!editingUser">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item :label="editingUser ? '新密码 (留空不改)' : '密码'">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="显示名">
          <el-input v-model="form.display_name" />
        </el-form-item>
        <el-form-item label="角色">
          <el-checkbox-group v-model="form.roles">
            <el-checkbox v-for="role in allRoles" :key="role" :label="role">{{ role }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'

const allRoles = ['admin', 'presales', 'pm', 'product', 'design', 'architect', 'frontend', 'backend', 'qa']
const users = ref<any[]>([])
const dialogVisible = ref(false)
const showCreateDialog = ref(false)
const editingUser = ref<any>(null)
const saving = ref(false)
const form = ref({ username: '', password: '', display_name: '', roles: [] as string[] })

onMounted(fetchUsers)

async function fetchUsers() {
  const { data } = await api.get('/users')
  users.value = data
}

function openEditDialog(user: any) {
  editingUser.value = user
  form.value = {
    username: user.username,
    password: '',
    display_name: user.display_name,
    roles: [...user.roles],
  }
  dialogVisible.value = true
}

watch(dialogVisible, (v) => {
  if (v && !editingUser.value) {
    form.value = { username: '', password: '', display_name: '', roles: [] }
  }
  if (!v) editingUser.value = null
})

async function handleSave() {
  saving.value = true
  try {
    if (editingUser.value) {
      const payload: any = { display_name: form.value.display_name, roles: form.value.roles }
      if (form.value.password) payload.password = form.value.password
      await api.put(`/users/${editingUser.value.id}`, payload)
    } else {
      await api.post('/users', form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchUsers()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(userId: number) {
  await api.delete(`/users/${userId}`)
  ElMessage.success('已删除')
  await fetchUsers()
}
</script>
