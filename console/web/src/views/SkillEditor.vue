<template>
  <div>
    <div style="display: flex; align-items: center; margin-bottom: 16px">
      <el-button text @click="$router.push('/assets')">&larr; 返回</el-button>
      <h3 style="margin: 0 0 0 8px">{{ title }}</h3>
      <el-tag v-if="isNew" type="success" style="margin-left: 8px">新建</el-tag>
    </div>

    <el-alert v-if="error" :title="error" type="error" show-icon style="margin-bottom: 12px" />

    <textarea
      ref="editorRef"
      v-model="content"
      style="width: 100%; height: calc(100vh - 240px); font-family: 'Fira Code', 'Courier New', monospace; font-size: 14px; padding: 12px; border: 1px solid #dcdfe6; border-radius: 4px; resize: none; tab-size: 2"
      spellcheck="false"
    />

    <div style="margin-top: 12px; display: flex; gap: 8px">
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      <el-button @click="handleValidate">校验格式</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import { ElMessage } from 'element-plus'

const props = defineProps<{ agentName: string; skillName?: string; docName?: string }>()
const route = useRoute()

const isSkill = computed(() => 'skillName' in route.params || route.path.includes('skills'))
const isNew = computed(() => route.path.endsWith('-new'))
const title = computed(() => {
  const type = isSkill.value ? 'Skill' : 'RAG 文档'
  const name = props.skillName || props.docName || '新建'
  return `${type}: ${props.agentName} / ${name}`
})

const content = ref('')
const error = ref('')
const saving = ref(false)

onMounted(async () => {
  if (isNew.value) {
    if (isSkill.value) {
      content.value = `---\nname: \ndescription: \nallowed-tools: []\n---\n\n# 触发条件\n\n# 执行步骤\n\n# 避坑指南\n`
    } else {
      content.value = `# 知识标题\n\n在此编写领域知识...\n`
    }
    return
  }

  try {
    const endpoint = isSkill.value
      ? `/agents/${props.agentName}/skills/${props.skillName}`
      : `/agents/${props.agentName}/rag/${props.docName}`
    const { data } = await api.get(endpoint)
    if (isSkill.value) {
      // 重组完整SKILL.md
      const frontmatter = [
        '---',
        `name: ${data.name}`,
        `description: ${data.description}`,
        `allowed-tools: [${data.allowed_tools.join(', ')}]`,
        '---',
        '',
      ].join('\n')
      content.value = frontmatter + data.content
    } else {
      content.value = data.content
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || '加载失败'
  }
})

async function handleSave() {
  error.value = ''
  saving.value = true
  try {
    const name = isNew.value
      ? prompt('请输入文件名 (不含.md):')
      : (props.skillName || props.docName)
    if (!name) { saving.value = false; return }

    const endpoint = isSkill.value
      ? `/agents/${props.agentName}/skills/${name}`
      : `/agents/${props.agentName}/rag/${name}`
    await api.put(endpoint, { content: content.value })
    ElMessage.success('保存成功')
    if (isNew.value) {
      // 跳转到编辑模式
      const path = isSkill.value
        ? `/assets/${props.agentName}/skills/${name}`
        : `/assets/${props.agentName}/rag/${name}`
      window.location.href = path
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

async function handleValidate() {
  if (!isSkill.value) {
    ElMessage.success('RAG 文档无需 Frontmatter 校验')
    return
  }
  try {
    await api.put(`/agents/${props.agentName}/skills/_validate`, { content: content.value })
    ElMessage.success('格式正确')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '校验失败'
  }
}
</script>
