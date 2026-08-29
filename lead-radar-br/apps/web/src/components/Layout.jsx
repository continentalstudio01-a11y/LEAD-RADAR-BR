import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Search, UsersRound, KanbanSquare, Settings, Radar, Download } from 'lucide-react'
import { exportUrl } from '../lib/api'

const nav = [
  ['/', LayoutDashboard, 'Visão geral'],
  ['/buscar', Search, 'Nova busca'],
  ['/leads', UsersRound, 'Leads'],
  ['/pipeline', KanbanSquare, 'Pipeline'],
  ['/configuracoes', Settings, 'Configurações'],
]

export default function Layout({ children }) {
  return (
    <div className="app-shell">
      <aside className="sidebar glass-strong">
        <div className="brand">
          <div className="brand-mark"><Radar size={21} /></div>
          <div>
            <strong>Lead Radar</strong>
            <span>BR</span>
          </div>
        </div>
        <nav className="nav-list">
          {nav.map(([to, Icon, label]) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <a className="secondary-button small" href={exportUrl(0)} target="_blank" rel="noreferrer"><Download size={15} /> Exportar CSV</a>
          <div className="free-mode"><span className="status-dot" /> Modo gratuito</div>
        </div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  )
}
