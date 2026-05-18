import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { ConfigProvider, Layout, Menu } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import ProjectList from './views/ProjectList'
import NewProject from './views/NewProject'
import ProjectDetail from './views/ProjectDetail'

const { Header, Content } = Layout

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Layout style={{ minHeight: '100vh' }}>
          <Header style={{ display: 'flex', alignItems: 'center', background: '#001529' }}>
            <div style={{ color: '#fff', fontSize: 18, fontWeight: 'bold', marginRight: 40 }}>XY Portal</div>
            <Menu theme="dark" mode="horizontal" defaultSelectedKeys={['projects']} items={[
              { key: 'projects', label: <Link to="/">项目列表</Link> },
              { key: 'new', label: <Link to="/new">提交需求</Link> },
            ]} />
          </Header>
          <Content style={{ padding: '24px 48px' }}>
            <Routes>
              <Route path="/" element={<ProjectList />} />
              <Route path="/new" element={<NewProject />} />
              <Route path="/project/:name" element={<ProjectDetail />} />
            </Routes>
          </Content>
        </Layout>
      </BrowserRouter>
    </ConfigProvider>
  )
}
