import { useEffect, useState } from 'react'
import { CheckCircle2, Compass, LoaderCircle, MapPin, Radar, Search, SlidersHorizontal } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

const defaults = { niche: 'dentistas', location: 'São Paulo, SP', radius_km: 10, depth: 'profunda', min_score: 0, only_without_site: false, max_results: 100 }

export default function SearchPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState(defaults)
  const [job, setJob] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!job?.id || job.status === 'done' || job.status === 'error') return
    const timer = setInterval(async () => {
      try {
        const next = await api(`/api/searches/${job.id}`)
        setJob(next)
        if (next.status === 'done') {
          clearInterval(timer)
          setTimeout(() => navigate(`/leads?search_id=${next.id}`), 700)
        }
      } catch {}
    }, 1800)
    return () => clearInterval(timer)
  }, [job?.id, job?.status, navigate])

  function update(name, value) {
    setForm((f) => ({ ...f, [name]: value }))
  }

  async function submit(e) {
    e.preventDefault()
    setError('')
    try {
      const created = await api('/api/searches', { method: 'POST', body: JSON.stringify(form) })
      setJob(created)
    } catch (e) {
      setError(e.message)
    }
  }

  const running = job && !['done', 'error'].includes(job.status)

  return (
    <div className="page narrow-page">
      <header className="page-header">
        <div>
          <div className="eyebrow">DESCOBERTA PROFUNDA</div>
          <h1>Configure a busca</h1>
          <p>Defina o nicho, a região e o nível de auditoria. O sistema cruza sinais públicos antes de pontuar cada empresa.</p>
        </div>
      </header>

      <div className="search-layout">
        <form className="search-form glass" onSubmit={submit}>
          <div className="form-section-title"><Search size={17} /> Mercado</div>
          <label>Nicho
            <input value={form.niche} onChange={(e) => update('niche', e.target.value)} placeholder="Ex.: dentistas, academias, clínicas" required />
          </label>
          <div className="two-cols">
            <label>Localidade
              <div className="input-icon"><MapPin size={16} /><input value={form.location} onChange={(e) => update('location', e.target.value)} placeholder="Cidade, bairro ou estado" required /></div>
            </label>
            <label>Raio
              <select value={form.radius_km} onChange={(e) => update('radius_km', Number(e.target.value))}>
                {[2, 5, 10, 20, 30, 50, 75, 100].map((n) => <option key={n} value={n}>{n} km</option>)}
              </select>
            </label>
          </div>

          <div className="form-divider" />
          <div className="form-section-title"><SlidersHorizontal size={17} /> Qualificação</div>
          <div className="two-cols">
            <label>Profundidade
              <select value={form.depth} onChange={(e) => update('depth', e.target.value)}>
                <option value="profunda">Profunda — site + SEO + performance</option>
                <option value="rapida">Rápida — presença e estrutura</option>
              </select>
            </label>
            <label>Máximo de resultados
              <select value={form.max_results} onChange={(e) => update('max_results', Number(e.target.value))}>
                {[25, 50, 100, 150, 250].map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
          </div>
          <label>Score mínimo <span className="range-value">{form.min_score}</span>
            <input type="range" min="0" max="100" value={form.min_score} onChange={(e) => update('min_score', Number(e.target.value))} />
          </label>
          <label className="toggle-row">
            <input type="checkbox" checked={form.only_without_site} onChange={(e) => update('only_without_site', e.target.checked)} />
            <span className="toggle-ui" />
            Mostrar somente empresas sem site próprio
          </label>

          {error && <div className="error-banner">{error}</div>}
          <button className="primary-button wide" disabled={running}>
            {running ? <><LoaderCircle className="spin" size={17} /> Analisando empresas…</> : <><Radar size={17} /> Iniciar busca qualificada</>}
          </button>
        </form>

        <aside className="search-status glass">
          <div className="status-visual"><Compass size={27} /></div>
          <h3>{running ? 'Busca em andamento' : job?.status === 'done' ? 'Busca concluída' : 'Como funciona'}</h3>
          {running ? (
            <>
              <p>Encontrando empresas, consolidando presença web e executando auditorias.</p>
              <div className="progress-line"><span /></div>
              <div className="status-list">
                <span><CheckCircle2 size={15} /> Nicho e geografia definidos</span>
                <span><LoaderCircle className="spin" size={15} /> Descoberta e enriquecimento</span>
                {job?.total_found != null && <span>{job.total_found} empresas encontradas até agora</span>}
              </div>
            </>
          ) : (
            <>
              <p>A busca combina dados geográficos abertos, pesquisa web e análise técnica do site.</p>
              <div className="status-list muted-list">
                <span>01 · Descoberta de negócios</span>
                <span>02 · Deduplicação e validação</span>
                <span>03 · Site, contatos e redes</span>
                <span>04 · Auditoria de presença digital</span>
                <span>05 · Score + Topo/Meio/Fundo</span>
                <span>06 · Serviço e abordagem sugeridos</span>
              </div>
            </>
          )}
        </aside>
      </div>
    </div>
  )
}
