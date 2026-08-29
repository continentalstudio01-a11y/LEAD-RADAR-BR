import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import SearchPage from './pages/SearchPage'
import LeadsPage from './pages/LeadsPage'
import LeadDetail from './pages/LeadDetail'
import Pipeline from './pages/Pipeline'
import Settings from './pages/Settings'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/buscar" element={<SearchPage />} />
        <Route path="/leads" element={<LeadsPage />} />
        <Route path="/leads/:id" element={<LeadDetail />} />
        <Route path="/pipeline" element={<Pipeline />} />
        <Route path="/configuracoes" element={<Settings />} />
      </Routes>
    </Layout>
  )
}
