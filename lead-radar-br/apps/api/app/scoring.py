from __future__ import annotations

from typing import Any


def calculate_score(lead: dict[str, Any]) -> tuple[int, str, int, list[str]]:
    audit = lead.get('audit') or {}
    social = lead.get('social') or {}
    web_search = lead.get('web_search') or {}
    score = 0
    confidence = 20
    reasons: list[str] = []

    website = lead.get('website')
    if not website:
        score += 38
        reasons.append('Sem site próprio identificado')
    elif audit.get('status') in ('quebrado', 'timeout', 'erro'):
        score += 32
        reasons.append('Site quebrado ou indisponível')
    elif audit.get('maintenance'):
        score += 28
        reasons.append('Site em manutenção/em breve')
    else:
        issues = audit.get('issues') or []
        score += min(30, len(issues) * 3)
        if len(issues) >= 5:
            reasons.append(f'{len(issues)} falhas digitais encontradas')

    # Contactability: opportunity is more valuable when it can actually be prospected.
    if lead.get('phone') or (audit.get('phones_found') or []):
        score += 8
        confidence += 12
        reasons.append('Telefone disponível')
    if lead.get('email') or (audit.get('emails_found') or []):
        score += 7
        confidence += 10
        reasons.append('E-mail disponível')
    if social:
        score += min(8, 3 + len(social) * 2)
        confidence += 8
        reasons.append('Presença em redes sociais')

    # Business existence and data consistency signals.
    if lead.get('address'):
        score += 4
        confidence += 8
    if lead.get('category'):
        confidence += 5
    if lead.get('osm'):
        confidence += 12

    ps = audit.get('page_speed') or {}
    perf = ps.get('performance')
    seo = ps.get('seo')
    if isinstance(perf, int) and perf < 50:
        score += 6
        reasons.append('Site lento no mobile')
    if isinstance(seo, int) and seo < 80:
        score += 6
        reasons.append('SEO técnico fraco')

    if website and web_search.get('result_count', 0) > 0 and web_search.get('official_position') is None:
        score += 8
        reasons.append('Site oficial não apareceu na busca pública consultada')
        confidence += 5
    elif web_search.get('official_position'):
        confidence += 8

    if audit.get('free_platform'):
        score += 8
        reasons.append('Usa plataforma/domínio gratuito')

    score = max(0, min(100, score))
    confidence = max(0, min(100, confidence))
    funnel = 'Fundo' if score >= 78 and (lead.get('phone') or lead.get('email') or social) else 'Meio' if score >= 55 else 'Topo'
    return score, funnel, confidence, reasons[:8]
