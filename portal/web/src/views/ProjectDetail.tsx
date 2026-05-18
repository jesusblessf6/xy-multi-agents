import { useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Tag, Descriptions, Spin, Typography } from 'antd'
import api from '../api'
import PipelineGraph from '../components/PipelineGraph'

const { Title } = Typography

interface ProjectDetailData {
  name: string
  client: string
  description: string
  current_state: string
  priority: string
  owner: string
  created_at: string
  artifacts: Record<string, { status: string; path: string; produced_by: string }>
  reviews: Record<string, { status: string; comments: string; timestamp: string }>
}

export default function ProjectDetail() {
  const { name } = useParams<{ name: string }>()
  const [project, setProject] = useState<ProjectDetailData | null>(null)
  const [loading, setLoading] = useState(true)
  const timerRef = useRef<number>()

  const fetchProject = async () => {
    if (!name) return
    try {
      const { data } = await api.get(`/projects/${name}`)
      setProject(data)
    } catch { /* ignore */ } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProject()
    // 10秒轮询
    timerRef.current = window.setInterval(fetchProject, 10000)
    return () => clearInterval(timerRef.current)
  }, [name])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (!project) return <div>项目不存在</div>

  return (
    <div>
      <Title level={3}>
        {project.name}
        <Tag color={project.current_state === 'delivery' ? 'success' : 'processing'} style={{ marginLeft: 12 }}>
          {project.current_state}
        </Tag>
      </Title>

      <PipelineGraph currentState={project.current_state} />

      <Card title="项目信息" style={{ marginTop: 16 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="客户">{project.client || '-'}</Descriptions.Item>
          <Descriptions.Item label="描述">{project.description || '-'}</Descriptions.Item>
          <Descriptions.Item label="优先级">{project.priority}</Descriptions.Item>
          <Descriptions.Item label="负责人">{project.owner || '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{project.created_at?.slice(0, 19).replace('T', ' ')}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="产出物" style={{ marginTop: 16 }}>
        {Object.entries(project.artifacts).map(([key, val]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
            <Tag color={val.status === 'ready' ? 'success' : 'default'}>{val.status}</Tag>
            <span>{key}</span>
            <span style={{ color: '#999', marginLeft: 8 }}>{val.path}</span>
          </div>
        ))}
      </Card>

      <Card title="评审状态" style={{ marginTop: 16 }}>
        {Object.entries(project.reviews).map(([key, val]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
            <Tag color={val.status === 'approved' ? 'success' : val.status === 'revision_needed' ? 'error' : 'warning'}>
              {val.status}
            </Tag>
            <span>{key}</span>
          </div>
        ))}
      </Card>
    </div>
  )
}
