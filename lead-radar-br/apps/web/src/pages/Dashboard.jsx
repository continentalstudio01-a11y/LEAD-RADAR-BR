import { useEffect, useState } from 'react'
import { ArrowRight, Globe2, Flame, Search, Target, TrendingUp, UsersRound } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import LeadTable from '../components/LeadTable'
import EmptyState from '../components/EmptyState'

function Stat({ icon: Icon, label, value, helper }) {
  return (
    <div className="stat-card glass">
      <div className="stat-icon"><Icon size={18} /></div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{helper}</small>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const load = () => api('/api/dashboard').then(setData).catch((e) => setError(e.message))
  useEffect(load, [])

  async function seed() {
    await api('/api/demo/seed', { method: 'POST' })
    load()
  }

  return (
    <div className="page">
      <header className="page-header hero-header">
        <div>
          <div className="eyebrow">PROSPECÇÃO COM EVIDÊNCIA</div>
          <h1>Oportunidades que valem uma abordagem.</h1>
          <p>Encontre negócios, identifique lacunas digitais e priorize quem tem mais chance de precisar de um site.</p>
        </div>
        <Link className="primary-button" to="/buscar"><Search size={17} /> Iniciar busca</Link>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="stats-grid">
        <Stat icon={UsersRound} label="Leads mapeados" value={data?.total_leads ?? '—'} helper="base consolidada" />
        <Stat icon={Flame} label="Alta prioridade" value={data?.hot_leads ?? '—'} helper="fundo do funil" />
        <Stat icon={Globe2} label="Sem site" value={data?.without_site ?? '—'} helper="oportunidade direta" />
        <Stat icon={TrendingUp} label="Score médio" value={data ? `${data.avg_score}/100` : '—'} helper="qualidade da base" />
      </section>

      <section className="section-block">
        <div className="section-heading">
          <div>
            <span className="section-kicker">PRIORIDADE</span>
            <h2>Leads mais promissores</h2>
          </div>
          <Link to="/leads" className="text-link">Ver todos <ArrowRight size={15} /></Link>
        </div>
        {data?.top_leads?.length ? <LeadTable leads={data.top_leads} /> : (
          <EmptyState
            title="Sua base ainda está vazia"
            text="Faça a primeira busca real ou carregue uma amostra para visualizar o fluxo completo."
            action={<div className="button-row"><Link to="/buscar" className="primary-button"><Target size={16} /> Buscar leads</Link><button className="secondary-button" onClick={seed}>Carregar demonstração</button></div>}
          />
        )}
      </section>
    </div>
  )
}
