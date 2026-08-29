import { ExternalLink, Mail, MapPin, Phone, SearchX, Target } from 'lucide-react'
import { Link } from 'react-router-dom'
import ScoreRing from './ScoreRing'
import Badge from './Badge'

function tone(funnel) {
  return funnel === 'Fundo' ? 'hot' : funnel === 'Meio' ? 'warm' : 'cool'
}

export default function LeadTable({ leads }) {
  return (
    <div className="table-shell glass">
      <div className="table-scroll">
        <table className="lead-table">
          <thead>
            <tr>
              <th>Empresa</th>
              <th>Oportunidade</th>
              <th>Site</th>
              <th>Contato</th>
              <th>Funil</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id}>
                <td>
                  <Link className="company-link" to={`/leads/${lead.id}`}>{lead.name}</Link>
                  <div className="muted inline-meta"><MapPin size={13} /> {lead.city || lead.address || 'Local não informado'}</div>
                </td>
                <td>
                  <div className="opportunity"><Target size={15} /> {lead.recommendation?.headline || 'Analisar oportunidade'}</div>
                  <div className="muted issue-preview">{lead.audit?.issues?.[0] || 'Sem falha crítica identificada'}</div>
                </td>
                <td>
                  {lead.website ? (
                    <a className="site-link" href={lead.website} target="_blank" rel="noreferrer">Abrir site <ExternalLink size={13} /></a>
                  ) : (
                    <span className="danger-inline"><SearchX size={14} /> Sem site próprio</span>
                  )}
                </td>
                <td>
                  <div className="contact-stack">
                    {lead.phone && <span><Phone size={13} /> {lead.phone}</span>}
                    {lead.email && <span><Mail size={13} /> {lead.email}</span>}
                    {!lead.phone && !lead.email && <span className="muted">Enriquecimento necessário</span>}
                  </div>
                </td>
                <td><Badge tone={tone(lead.funnel)}>{lead.funnel}</Badge></td>
                <td><ScoreRing value={lead.score} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
