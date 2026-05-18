<template>
  <div>
    <el-row :gutter="20" style="margin-bottom: 24px">
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="待审评审" :value="dashboard.pending_reviews_count" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="活跃项目" :value="dashboard.active_projects_count" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic title="我的角色" :value="userStore.roles.join(', ')" />
        </el-card>
      </el-col>
    </el-row>

    <h3>待处理评审</h3>
    <el-empty v-if="!dashboard.pending_reviews.length" description="暂无待审评审" />
    <el-card v-for="item in dashboard.pending_reviews" :key="item.project_name + item.gate_name" style="margin-bottom: 12px" shadow="hover">
      <div style="display: flex; justify-content: space-between; align-items: center">
        <div>
          <strong>{{ item.project_name }}</strong>
          <el-tag type="warning" style="margin-left: 8px">{{ item.gate_name }}</el-tag>
        </div>
        <el-button type="primary" size="small" @click="$router.push('/reviews')">前往评审</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const dashboard = ref({ pending_reviews_count: 0, active_projects_count: 0, pending_reviews: [] as any[] })

onMounted(async () => {
  const { data } = await api.get('/dashboard')
  dashboard.value = data
})
</script>
