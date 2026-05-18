import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Tag, Row, Col, Spin } from 'antd'
import api from '../api'

interface Project {
  name: string
  client: string
  description: string
  current_state: string
  priority: string
  owner: string
  created_at: string
}

const stateColors: Record<string, string> = {
  idle: 'default',
  requirements: 'processing',
  prd: 'processing',
  prd_review: 'warning',
  design: 'processing',
  design_review: 'warning',
  architecture: 'processing',
  arch_review: 'warning',
  development: 'processing',
  test_case: 'processing',
  test_review: 'warning',
  test_execution: 'processing',
  delivery: 'success',
}

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/projects').then(({ data }) => {
      setProjects(data)
      setLoading(false)
    })
  }, [])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />

  return (
    <div>
      <h2>项目列表</h2>
      <Row gutter={[16, 16]}>
        {projects.map((p) => (
          <Col xs={24} sm={12} lg={8} key={p.name}>
            <Card hoverable onClick={() => navigate(`/project/${p.name}`)}>
              <Card.Meta
                title={<>{p.name} <Tag color={stateColors[p.current_state] || 'default'}>{p.current_state}</Tag></>}
                description={
                  <>
                    <div>客户: {p.client || '-'}</div>
                    <div>{p.description || '暂无描述'}</div>
                    <div style={{ color: '#999', marginTop: 8 }}>{p.created_at?.slice(0, 10)}</div>
                  </>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>
      {projects.length === 0 && <div style={{ textAlign: 'center', color: '#999', marginTop: 60 }}>暂无项目，请先提交需求</div>}
    </div>
  )
}
