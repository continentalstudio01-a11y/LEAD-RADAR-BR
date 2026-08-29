from __future__ import annotations

from typing import Any


def recommend_services(lead: dict[str, Any]) -> dict[str, Any]:
    audit = lead.get('audit') or {}
    issues = set(audit.get('issues') or [])
    services: list[dict[str, str]] = []

    if not lead.get('website'):
        services.append({'service': 'Site institucional', 'priority': 'alta', 'why': 'Nenhum site próprio confiável foi identificado.'})
    elif audit.get('status') in ('quebrado', 'timeout', 'erro', 'manutencao'):
        services.append({'service': 'Reconstrução do site', 'priority': 'alta', 'why': 'O site atual está indisponível, quebrado ou em manutenção.'})
    elif len(issues) >= 5:
        services.append({'service': 'Redesign + modernização', 'priority': 'alta', 'why': 'A auditoria detectou múltiplos problemas técnicos/comerciais.'})

    if any('SEO' in i or 'H1' in i or 'Meta description' in i or 'Sitemap' in i or 'Schema' in i for i in issues):
        services.append({'service': 'SEO local e técnico', 'priority': 'alta', 'why': 'Há lacunas que podem limitar indexação e presença na busca.'})
    if any('Performance' in i or 'lenta' in i or 'viewport' in i for i in issues):
        services.append({'service': 'Otimização mobile/performance', 'priority': 'media', 'why': 'A experiência móvel ou velocidade precisa de melhoria.'})
    if not audit.get('has_whatsapp', False):
        services.append({'service': 'Conversão por WhatsApp', 'priority': 'media', 'why': 'Não foi encontrado um caminho claro de contato por WhatsApp.'})
    if not audit.get('has_form', False):
        services.append({'service': 'Captação de leads', 'priority': 'media', 'why': 'Não foi identificado formulário de orçamento/contato.'})
    if not audit.get('has_privacy', False) and lead.get('website'):
        services.append({'service': 'Adequação de privacidade/LGPD', 'priority': 'baixa', 'why': 'Política de privacidade não foi identificada.'})

    if not services:
        services.append({'service': 'Diagnóstico comercial digital', 'priority': 'media', 'why': 'O negócio existe, mas não há uma oportunidade dominante com os dados atuais.'})

    # Avoid implying Google ranking certainty when source is a metasearch.
    visibility = lead.get('web_search') or {}
    alerts: list[str] = []
    if lead.get('website') and visibility.get('result_count', 0) > 0 and visibility.get('official_position') is None:
        alerts.append('O site existe, mas não apareceu entre os resultados da busca pública usada nesta análise. Confirmar no Google Search Console/Google antes da abordagem.')
    if audit.get('maintenance') and not audit.get('maintenance_90d_confirmed'):
        alerts.append('Manutenção detectada agora, mas ainda sem comprovação histórica de 90 dias.')

    return {
        'headline': services[0]['service'],
        'services': services[:6],
        'alerts': alerts,
        'next_action': 'Priorizar contato consultivo com evidências objetivas da auditoria.' if lead.get('score', 0) >= 70 else 'Enriquecer os dados antes de iniciar a abordagem.',
    }


def approach_text(lead: dict[str, Any], channel: str = 'whatsapp') -> str:
    name = lead.get('name') or 'sua empresa'
    rec = lead.get('recommendation') or recommend_services(lead)
    headline = rec.get('headline') or 'melhoria do site'
    audit = lead.get('audit') or {}
    concrete = (audit.get('issues') or [])[:2]
    evidence = '; '.join(concrete) if concrete else 'há oportunidades claras na presença digital'

    if channel == 'email':
        return (
            f'Olá, equipe da {name}. Fiz uma análise rápida da presença digital de vocês e encontrei alguns pontos objetivos: '
            f'{evidence}. A principal oportunidade que identifiquei é {headline.lower()}. '
            'Se fizer sentido, posso enviar um diagnóstico curto com as melhorias prioritárias, sem compromisso.'
        )
    if channel == 'instagram':
        return (
            f'Olá! Analisei a presença digital da {name} e encontrei uma oportunidade de {headline.lower()}. '
            f'Vi também: {evidence}. Posso enviar um diagnóstico bem curto por aqui?'
        )
    return (
        f'Olá! Tudo bem? Analisei a presença digital da {name} e encontrei uma oportunidade clara de {headline.lower()}. '
        f'Na análise apareceram pontos como {evidence}. Posso te enviar um diagnóstico curto com o que eu melhoraria primeiro?'
    )
