import { CheckCircle2, Database, Gauge, Globe2, LockKeyhole, Search } from 'lucide-react'

function Source({ icon: Icon, name, detail, status = 'Ativo' }) {
  return <div className="source-row"><div className="source-icon"><Icon size={17} /></div><div><strong>{name}</strong><p>{detail}</p></div><span className="source-status"><CheckCircle2 size={14} /> {status}</span></div>
}

export default function Settings() {
  return (
    <div className="page narrow-page">
      <header className="page-header"><div><div className="eyebrow">MODO GRATUITO</div><h1>Fontes e configurações</h1><p>O núcleo funciona sem assinatura paga. Algumas fontes possuem limites públicos e conectores opcionais.</p></div></header>
      <section className="glass detail-card settings-card">
        <div className="card-title"><Database size={17} /> Fontes atuais</div>
        <Source icon={Globe2} name="OpenStreetMap / Overpass" detail="Descoberta geográfica de empresas e pontos comerciais por nicho e raio." />
        <Source icon={Search} name="SearXNG local" detail="Pesquisa web para localizar site oficial, redes e sinais de presença digital." />
        <Source icon={Gauge} name="PageSpeed Insights" detail="Performance, SEO, acessibilidade e boas práticas; uso sem chave é adequado apenas para volume moderado." />
        <Source icon={LockKeyhole} name="Auditoria própria" detail="HTML, HTTPS, CTA, formulário, WhatsApp, Schema, sitemap, robots, privacidade e outros sinais." />
      </section>
      <section className="glass detail-card settings-card">
        <div className="card-title">Conectores futuros</div>
        <p className="muted">Google Places pode ser ligado depois como fonte premium/limitada por cota. LinkedIn, Instagram e Facebook não devem ser raspados por automação agressiva; o sistema pode enriquecer links públicos encontrados na web e receber APIs oficiais quando disponíveis.</p>
      </section>
    </div>
  )
}
