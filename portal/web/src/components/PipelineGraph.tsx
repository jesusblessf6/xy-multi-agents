import { useEffect, useState } from 'react'
import { Card } from 'antd'

interface PipelineNode {
  id: string
  label: string
  type: string
  agent: string | string[] | null
}

interface PipelineEdge {
  from: string
  to: string
  label: string
}

interface Props {
  currentState: string
}

// 布局常量
const NODE_W = 140
const NODE_H = 44
const GAP_X = 170
const GAP_Y = 70

const stateColors: Record<string, string> = {
  agent_execution: '#1890ff',
  review_gate: '#fa8c16',
  parallel: '#722ed1',
  terminal: '#52c41a',
}

export default function PipelineGraph({ currentState }: Props) {
  const [nodes, setNodes] = useState<PipelineNode[]>([])
  const [edges, setEdges] = useState<PipelineEdge[]>([])

  useEffect(() => {
    const api = require('../api').default
    api.get('/pipeline').then(({ data }: any) => {
      setNodes(data.graph.nodes)
      setEdges(data.graph.edges)
    })
  }, [])

  if (nodes.length === 0) return null

  // 简单水平布局：按 pipeline 顺序排列
  // 分行：review gate 和 rejected 回退需要换行
  const orderedIds = ['idle', 'requirements', 'prd', 'prd_review', 'design', 'design_review',
    'architecture', 'arch_review', 'development', 'test_case', 'test_review', 'test_execution', 'delivery']
  const posMap: Record<string, { x: number; y: number }> = {}
  let col = 0
  let row = 0

  for (const id of orderedIds) {
    if (!nodes.find(n => n.id === id)) continue
    posMap[id] = { x: col * GAP_X + 20, y: row * GAP_Y + 20 }
    // review gate 后面如果是回退边，不换行
    col++
  }

  const svgW = (orderedIds.filter(id => nodes.find(n => n.id === id)).length) * GAP_X + 40
  const svgH = GAP_Y + NODE_H + 20

  return (
    <Card title="流水线进度" size="small">
      <div style={{ overflowX: 'auto' }}>
        <svg width={svgW} height={svgH} style={{ minWidth: svgW }}>
          {/* 边 */}
          {edges.map((e, i) => {
            const from = posMap[e.from]
            const to = posMap[e.to]
            if (!from || !to) return null
            const isReject = e.label === '驳回'
            return (
              <g key={i}>
                <line
                  x1={from.x + NODE_W} y1={from.y + NODE_H / 2}
                  x2={to.x} y2={to.y + NODE_H / 2}
                  stroke={isReject ? '#ff4d4f' : '#d9d9d9'}
                  strokeWidth={isReject ? 1.5 : 1}
                  strokeDasharray={isReject ? '4 3' : undefined}
                />
                {e.label && (
                  <text
                    x={(from.x + NODE_W + to.x) / 2}
                    y={from.y + NODE_H / 2 - 6}
                    fill={isReject ? '#ff4d4f' : '#999'}
                    fontSize={10}
                    textAnchor="middle"
                  >
                    {e.label}
                  </text>
                )}
              </g>
            )
          })}

          {/* 节点 */}
          {nodes.map((n) => {
            const pos = posMap[n.id]
            if (!pos) return null
            const isCurrent = n.id === currentState
            const isPast = orderedIds.indexOf(n.id) < orderedIds.indexOf(currentState)
            const color = stateColors[n.type] || '#1890ff'
            const bgColor = isCurrent ? color : isPast ? '#f0f5ff' : '#fafafa'
            const textColor = isCurrent ? '#fff' : isPast ? '#1890ff' : '#999'
            const borderColor = isCurrent ? color : '#d9d9d9'

            return (
              <g key={n.id}>
                <rect
                  x={pos.x} y={pos.y}
                  width={NODE_W} height={NODE_H}
                  rx={6} ry={6}
                  fill={bgColor}
                  stroke={borderColor}
                  strokeWidth={isCurrent ? 2 : 1}
                />
                <text
                  x={pos.x + NODE_W / 2}
                  y={pos.y + NODE_H / 2 + 4}
                  fill={textColor}
                  fontSize={12}
                  textAnchor="middle"
                  fontWeight={isCurrent ? 'bold' : 'normal'}
                >
                  {n.label.length > 10 ? n.label.slice(0, 10) + '...' : n.label}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    </Card>
  )
}
