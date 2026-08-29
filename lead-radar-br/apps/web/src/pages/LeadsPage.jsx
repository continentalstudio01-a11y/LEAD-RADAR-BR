import { useEffect, useState } from 'react'
import { Download, Filter, Search } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { api, exportUrl } from '../lib/api'
import LeadTable from '../components/LeadTable'
import EmptyState from '../components/EmptyState'

export default function LeadsPage() {
  const [params] = useSearchParams()
  const [leads, setLeads] = useState([])
  const [filters, setFilters] = useState({ q: '', funnel: '', min_score: 0, has_site: '' })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const qs = new URLSearchParams()
    const searchId = params.get('search_id')
    if (searchId) qs.set('search_id', searchId)
    if (filters.q) qs.set('q', filters.q)
    if (filters.funnel) qs.set('funnel', filters.funnel)
    if (filters.min_score) qs.set('min_score', filters.min_score)
    if (filters.has_site) qs.set('has_site', filters.has_site)
    setLoading(true)
    api(`/api/leads?${qs}`).then(setLeads).finally(() => setLoading(false))
  }, [params, filters])

  return (
    <div className="page">
      <header className="page-header compact-header">
        <div>
          <div className="eyebrow">BASE QUALIFICADA</div>
          <h1>Leads</h1>
          <p>{loading ? 'Atualizando…' : `${leads.length} leads no recorte atual`}</p>
        </div>
        <a className="secondary-button" href={exportUrl(filters.min_score)}><Download size={16} /> Exportar</a>
      </header>

      <div className="filter-bar glass">
        <div className="input-icon grow"><Search size={16} /><input value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} placeholder="Empresa, cidade ou categoria" /></div>
        <div className="filter-label"><Filter size={15} /> Filtros</div>
        <select value={filters.funnel} onChange={(e) => setFilters({ ...filters, funnel: e.target.value })}>
          <option value="">Todos os funis</option>
          <option value="Fundo">Fundo</option>
          <option value="Meio">Meio</option>
          <option value="Topo">Topo</option>
        </select>
        <select value={filters.has_site} onChange={(e) => setFilters({ ...filters, has_site: e.target.value })}>
          <option value="">Com e sem site</option>
          <option value="false">Somente sem site</option>
          <option value="true">Somente com site</option>
        </select>
        <select value={filters.min_score} onChange={(e) => setFilters({ ...filters, min_score: Number(e.target.value) })}>
          <option value="0">Score 0+</option>
          <option value="50">Score 50+</option>
          <option value="70">Score 70+</option>
          <option value="80">Score 80+</option>
        </select>
      </div>

      {leads.length ? <LeadTable leads={leads} /> : !loading && <EmptyState title="Nenhum lead nesse filtro" text="Ajuste os filtros ou execute uma nova busca." />}
    </div>
  )
}
