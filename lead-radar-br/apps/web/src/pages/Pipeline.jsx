import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { Link } from 'react-router-dom'
import ScoreRing from '../components/ScoreRing'

const stages = ['Novo', 'Analisado', 'Contatado', 'Respondeu', 'Reuniao', 'Proposta', 'Cliente', 'Perdido']

export default function Pipeline() {
  const [leads, setLeads] = useState([])
  const load = () => api('/api/leads?limit=1000').then(setLeads)
  useEffect(load, [])

  async function move(id, stage) {
    await api(`/api/leads/${id}/stage`, { method: 'PATCH', body: JSON.stringify({ stage }) })
    load()
  }

  return (
    <div className="page pipeline-page">
      <header className="page-header compact-header"><div><div className="eyebrow">CRM LEVE</div><h1>Pipeline</h1><p>Do lead novo até cliente, sem complicar.</p></div></header>
      <div className="kanban-scroll">
        <div className="kanban-board">
          {stages.map((stage) => {
            const items = leads.filter((l) => l.stage === stage)
            return <div className="kanban-column glass" key={stage}>
              <div className="kanban-head"><strong>{stage}</strong><span>{items.length}</span></div>
              <div className="kanban-cards">
                {items.map((lead) => <div className="kanban-card" key={lead.id}>
                  <div className="kanban-card-top"><Link to={`/leads/${lead.id}`}>{lead.name}</Link><ScoreRing value={lead.score} size={42} /></div>
                  <p>{lead.recommendation?.headline || 'Oportunidade digital'}</p>
                  <select value={lead.stage} onChange={(e) => move(lead.id, e.target.value)}>{stages.map((s) => <option key={s}>{s}</option>)}</select>
                </div>)}
                {!items.length && <div className="kanban-empty">Nenhum lead</div>}
              </div>
            </div>
          })}
        </div>
      </div>
    </div>
  )
}
