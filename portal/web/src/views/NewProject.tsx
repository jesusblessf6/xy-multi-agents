import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Card, message, Select } from 'antd'
import api from '../api'

export default function NewProject() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      await api.post('/requirements', values)
      message.success('需求已提交')
      navigate(`/project/${values.project_name}`)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '提交失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <Card title="提交新需求">
        <Form layout="vertical" onFinish={onFinish} initialValues={{ priority: 'normal' }}>
          <Form.Item name="project_name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="my-project" />
          </Form.Item>
          <Form.Item name="client" label="客户">
            <Input placeholder="客户名称" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <Input.TextArea rows={2} placeholder="简要描述项目目标" />
          </Form.Item>
          <Form.Item name="priority" label="优先级">
            <Select options={[
              { value: 'low', label: '低' },
              { value: 'normal', label: '普通' },
              { value: 'high', label: '高' },
              { value: 'urgent', label: '紧急' },
            ]} />
          </Form.Item>
          <Form.Item name="owner" label="负责人">
            <Input placeholder="负责人" />
          </Form.Item>
          <Form.Item name="requirement_text" label="需求描述" rules={[{ required: true, message: '请输入需求描述' }]}>
            <Input.TextArea rows={6} placeholder="详细描述客户需求、功能要点、业务场景..." />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} size="large">提交需求</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
