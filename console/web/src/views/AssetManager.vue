<template>
  <div style="display: flex; height: calc(100vh - 120px)">
    <!-- 左侧Agent列表 -->
    <div style="width: 240px; border-right: 1px solid #eee; padding-right: 16px; overflow-y: auto">
      <h3>Agent 列表</h3>
      <el-menu :default-active="selectedAgent" @select="handleSelectAgent">
        <el-menu-item v-for="a in agents" :key="a.name" :index="a.name" :disabled="!a.can_edit">
          <span>{{ a.display_name }}</span>
          <el-badge :value="a.skills_count" style="margin-left: 8px" />
        </el-menu-item>
      </el-menu>
    </div>

    <!-- 右侧内容 -->
    <div style="flex: 1; padding-left: 16px; overflow-y: auto">
      <template v-if="selectedAgent">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="Skills" name="skills">
            <el-button type="primary" size="small" @click="newSkill" style="margin-bottom: 12px">新增 Skill</el-button>
            <el-table :data="skills" stripe>
              <el-table-column prop="name" label="名称" />
              <el-table-column prop="description" label="描述" />
              <el-table-column label="操作" width="160">
                <template #default="{ row }">
                  <el-button size="small" @click="$router.push(`/assets/${selectedAgent}/skills/${row.name}`)">编辑</el-button>
                  <el-popconfirm title="确认删除?" @confirm="handleDeleteSkill(row.name)">
                    <template #reference>
                      <el-button size="small" type="danger">删除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="RAG" name="rag">
            <el-button type="primary" size="small" @click="newRag" style="margin-bottom: 12px">新增 RAG 文档</el-button>
            <el-table :data="ragDocs" stripe>
              <el-table-column prop="name" label="名称" />
              <el-table-column label="操作" width="160">
                <template #default="{ row }">
                  <el-button size="small" @click="$router.push(`/assets/${selectedAgent}/rag/${row.name}`)">编辑</el-button>
                  <el-popconfirm title="确认删除?" @confirm="handleDeleteRag(row.name)">
                    <template #reference>
                      <el-button size="small" type="danger">删除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </template>
      <el-empty v-else description="请选择左侧的 Agent" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const agents = ref<any[]>([])
const selectedAgent = ref('')
const activeTab = ref('skills')
const skills = ref<any[]>([])
const ragDocs = ref<any[]>([])

onMounted(async () => {
  const { data } = await api.get('/agents')
  agents.value = data
  // 默认选中第一个可编辑的
  const first = data.find((a: any) => a.can_edit)
  if (first) selectedAgent.value = first.name
})

watch(selectedAgent, async (name) => {
  if (!name) return
  await loadAssets(name)
})

async function loadAssets(agentName: string) {
  const [skillRes, ragRes] = await Promise.all([
    api.get(`/agents/${agentName}/skills`),
    api.get(`/agents/${agentName}/rag`),
  ])
  skills.value = skillRes.data
  ragDocs.value = ragRes.data
}

function handleSelectAgent(name: string) {
  selectedAgent.value = name
}

function newSkill() {
  router.push(`/assets/${selectedAgent.value}/skills-new`)
}

function newRag() {
  router.push(`/assets/${selectedAgent.value}/rag-new`)
}

async function handleDeleteSkill(skillName: string) {
  await api.delete(`/agents/${selectedAgent.value}/skills/${skillName}`)
  ElMessage.success('已删除')
  await loadAssets(selectedAgent.value)
}

async function handleDeleteRag(docName: string) {
  await api.delete(`/agents/${selectedAgent.value}/rag/${docName}`)
  ElMessage.success('已删除')
  await loadAssets(selectedAgent.value)
}
</script>
