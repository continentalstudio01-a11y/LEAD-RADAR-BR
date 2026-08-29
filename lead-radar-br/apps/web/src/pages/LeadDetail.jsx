import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../lib/api'
import ScoreRing from '../components/ScoreRing'
import Badge from '../components/Badge'
import { AlertTriangle, ArrowUpRight, CheckCircle2, Copy, Globe2, Mail, MapPin, MessageCircle, Phone, ShieldCheck, Target, XCircle } from 'lucide-react'

const stages = ['Novo', 'Analisado', 'Contatado', 'Respondeu', 'Reuniao', 'Proposta', 'Cliente', 'Perdido']

function Finding({ ok, children }) {
  return <div className={`finding ${ok ? 'finding-ok' : 'finding-bad'}`}>{ok ? <CheckCircle2 size={15} /> : <XCircle size={15} />}{children}</div>
}

export default function LeadDetail() {
  const { id } = useParams()
  const [lead, setLead] = useState(null)
  const [approach, setApproach] = useState('')
  const [copied, setCopied] = useState(false)

  const load = () => api(`/api/leads/${id}`).then(setLead)
  useEffect(load, [id])

  async function stage(value) {
    await api(`/api/leads/${id}/stage`, { method: 'PATCH', body: JSON.stringify({ stage: value }) })
    load()
  }

  async function generate(channel = 'whatsapp') {
    const data = await api(`/api/leads/${id}/approach`, { method: 'POST', body: JSON.stringify({ channel }) })
    setApproach(data.text)
  }

  async function copy() {
    await navigator.clipboard.writeText(approach)
    setCopied(true)
    setTimeout(() => setCopied(false), 1200)
  }

  if (!lead) return <div className="page"><div className="loading-card glass">Carregando lead…</div></div>
  const audit = lead.audit || {}
  const rec = lead.recommendation || {}
  const alerts = rec.alerts || []

  return (
    <div className="page">
      <header className="lead-hero glass">
        <div className="lead-main">
          <div className="eyebrow">LEAD QUALIFICADO</div>
          <h1>{lead.name}</h1>
          <div className="lead-meta">
            <span><MapPin size={14} /> {lead.address || lead.city || 'Local não informado'}</span>
            {lead.category && <span>{lead.category}</span>}
          </div>
          <div className="lead-actions">
            {lead.phone && <a className="primary-button small" href={`https://wa.me/55${String(lead.phone).replace(/\D/g, '')}`} target="_blank" rel="noreferrer"><MessageCircle size={15} /> WhatsApp</a>}
            {lead.website && <a className="secondary-button small" href={lead.website} target="_blank" rel="noreferrer"><Globe2 size={15} /> Abrir site <ArrowUpRight size={13} /></a>}
          </div>
        </div>
        <div className="lead-score-panel">
          <ScoreRing value={lead.score} size={92} />
          <div><Badge tone={lead.funnel === 'Fundo' ? 'hot' : lead.funnel === 'Meio' ? 'warm' : 'cool'}>{lead.funnel} do funil</Badge><small>Confiança dos dados: {lead.confidence}%</small></div>
        </div>
      </header>

      {alerts.map((alert) => <div key={alert} className="warning-banner"><AlertTriangle size={16} /> {alert}</div>)}

      <div className="detail-grid">
        <section className="glass detail-card">
          <div className="card-title"><Target size={17} /> O que vender</div>
          <h2>{rec.headline || 'Diagnóstico digital'}</h2>
          <div className="service-list">
            {(rec.services || []).map((s) => <div className="service-row" key={s.service}><div><strong>{s.service}</strong><p>{s.why}</p></div><Badge tone={s.priority === 'alta' ? 'hot' : s.priority === 'media' ? 'warm' : 'neutral'}>{s.priority}</Badge></div>)}
          </div>
        </section>

        <section className="glass detail-card">
          <div className="card-title"><ShieldCheck size={17} /> Dados de contato</div>
          <div className="contact-details">
            <div><Phone size={15} /><span>Telefone</span><strong>{lead.phone || 'Não encontrado'}</strong></div>
            <div><Mail size={15} /><span>E-mail</span><strong>{lead.email || 'Não encontrado'}</strong></div>
            <div><Globe2 size={15} /><span>Site</span><strong>{lead.website || 'Sem site próprio'}</strong></div>
          </div>
          <div className="social-pills">{Object.entries(lead.social || {}).map(([k, v]) => <a key={k} href={v} target="_blank" rel="noreferrer">{k}</a>)}</div>
        </section>

        <section className="glass detail-card span-two">
          <div className="card-title"><Globe2 size={17} /> Auditoria do site</div>
          <div className="audit-grid">
            <Finding ok={!!lead.website}>{lead.website ? 'Site próprio identificado' : 'Sem site próprio identificado'}</Finding>
            <Finding ok={audit.https}>HTTPS</Finding>
            <Finding ok={audit.has_viewport}>Responsivo / viewport</Finding>
            <Finding ok={audit.has_whatsapp}>WhatsApp</Finding>
            <Finding ok={audit.has_form}>Formulário</Finding>
            <Finding ok={audit.has_cta}>CTA comercial</Finding>
            <Finding ok={audit.has_schema}>Schema.org</Finding>
            <Finding ok={audit.has_sitemap}>Sitemap</Finding>
            <Finding ok={audit.has_robots}>robots.txt</Finding>
            <Finding ok={audit.has_privacy}>Privacidade/LGPD</Finding>
          </div>
          {!!audit.page_speed && Object.keys(audit.page_speed).length > 0 && <div className="metric-strip">
            {['performance', 'seo', 'accessibility', 'best_practices'].map((key) => audit.page_speed?.[key] != null && <div key={key}><span>{key.replace('_', ' ')}</span><strong>{audit.page_speed[key]}</strong></div>)}
          </div>}
          <div className="issue-list">{(audit.issues || []).map((x) => <div key={x}><AlertTriangle size={14} /> {x}</div>)}</div>
        </section>

        <section className="glass detail-card">
          <div className="card-title"><MessageCircle size={17} /> Abordagem</div>
          <p className="muted">A mensagem usa apenas os problemas encontrados nesta análise.</p>
          <div className="channel-row"><button onClick={() => generate('whatsapp')}>WhatsApp</button><button onClick={() => generate('email')}>E-mail</button><button onClick={() => generate('instagram')}>Instagram</button></div>
          {approach && <div className="approach-box"><p>{approach}</p><button className="copy-button" onClick={copy}><Copy size={14} /> {copied ? 'Copiado' : 'Copiar'}</button></div>}
        </section>

        <section className="glass detail-card">
          <div className="card-title">Etapa comercial</div>
          <select value={lead.stage} onChange={(e) => stage(e.target.value)}>{stages.map((s) => <option key={s}>{s}</option>)}</select>
          <div className="score-reasons">{(rec.score_reasons || []).map((r) => <span key={r}><CheckCircle2 size={13} /> {r}</span>)}</div>
        </section>
      </div>
    </div>
  )
}
