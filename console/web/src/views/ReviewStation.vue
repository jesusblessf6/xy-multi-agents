<template>
  <div>
    <h2>评审工作台</h2>
    <el-empty v-if="!pending.length" description="暂无待审评审" />

    <el-collapse v-model="activeNames">
      <el-collapse-item v-for="item in pending" :key="item.project_name + item.gate_name" :name="item.project_name + item.gate_name">
        <template #title>
          <strong>{{ item.project_name }}</strong>
          <el-tag type="warning" style="margin-left: 8px">{{ item.gate_name }}</el-tag>
          <el-tag v-if="item.status === 'awaiting_review'" type="info" style="margin-left: 8px">待审</el-tag>
        </template>

        <div v-if="detailMap[item.project_name + item.gate_name]">
          <h4>检查清单</h4>
          <ul>
            <li v-for="(c, i) in detailMap[item.project_name + item.gate_name].checklist" :key="i">{{ c }}</li>
          </ul>

          <h4>已审核</h4>
          <el-tag v-for="d in detailMap[item.project_name + item.gate_name].decisions" :key="d.reviewer_role"
            :type="d.approved ? 'success' : 'danger'" style="margin-right: 8px">
            {{ d.reviewer_role }}: {{ d.approved ? '通过' : '驳回' }}
          </el-tag>

          <el-divider />

          <el-form :inline="true">
            <el-form-item label="审批意见">
              <el-input v-model="commentsMap[item.project_name + item.gate_name]" type="textarea" :rows="2" style="width: 400px" />
            </el-form-item>
            <el-form-item>
              <el-button type="success" @click="submitReview(item.project_name, item.gate_name, true)">通过</el-button>
              <el-button type="danger" @click="submitReview(item.project_name, item.gate_name, false)">驳回</el-button>
            </el-form-item>
          </el-form>
        </div>
        <div v-else style="color: #999">加载中...</div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'

const pending = ref<any[]>([])
const activeNames = ref<string[]>([])
const detailMap = ref<Record<string, any>>({})
const commentsMap = ref<Record<string, string>>({})

onMounted(async () => {
  const { data } = await api.get('/reviews/pending')
  pending.value = data
})

watch(activeNames, async (names) => {
  for (const name of names) {
    if (detailMap.value[name]) continue
    const [proj, gate] = name.split(/(?=prd_review|design_review|arch_review|test_review)/)
    try {
      const { data } = await api.get(`/reviews/${proj}/${gate}`)
      detailMap.value[name] = data
    } catch { /* ignore */ }
  }
})

async function submitReview(projectName: string, gateName: string, approved: boolean) {
  const key = projectName + gateName
  const comments = commentsMap.value[key] || ''
  try {
    await api.post(`/reviews/${projectName}/${gateName}`, { approved, comments })
    ElMessage.success(approved ? '评审通过' : '评审驳回')
    // 刷新列表
    const { data } = await api.get('/reviews/pending')
    pending.value = data
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  }
}
</script>
