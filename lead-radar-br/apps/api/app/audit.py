from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .config import ENABLE_PAGESPEED, ENABLE_WAYBACK, PAGESPEED_API_KEY, REQUEST_TIMEOUT, USER_AGENT

MAINTENANCE_MARKERS = (
    'em manutenção', 'em manutencao', 'site em manutenção', 'site em manutencao',
    'maintenance mode', 'under maintenance', 'coming soon', 'em breve', 'voltamos em breve',
)
FREE_PLATFORM_HOSTS = ('wixsite.com', 'wordpress.com', 'blogspot.com', 'weebly.com', 'sites.google.com')
SOCIAL_DOMAINS = ('instagram.com', 'facebook.com', 'linkedin.com', 'tiktok.com', 'youtube.com')
EMAIL_RE = re.compile(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', re.I)
PHONE_RE = re.compile(r'(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?(?:9\s*)?\d{4}[-\s]?\d{4}')
CNPJ_RE = re.compile(r'\b\d{2}[.\s]?\d{3}[.\s]?\d{3}[\/\s-]?\d{4}[-.\s]?\d{2}\b')


def _base_result(url: str | None) -> dict[str, Any]:
    return {
        'status': 'sem_site' if not url else 'nao_auditado',
        'reachable': False,
        'https': bool(url and url.lower().startswith('https://')),
        'response_ms': None,
        'http_status': None,
        'final_url': url,
        'title': None,
        'meta_description': None,
        'h1_count': 0,
        'has_viewport': False,
        'has_form': False,
        'has_whatsapp': False,
        'has_cta': False,
        'has_schema': False,
        'has_robots': False,
        'has_sitemap': False,
        'has_privacy': False,
        'has_cookie_notice': False,
        'has_services_page': False,
        'has_contact_page': False,
        'has_google_maps_embed': False,
        'has_analytics': False,
        'has_meta_pixel': False,
        'has_tag_manager': False,
        'social_links': {},
        'emails_found': [],
        'phones_found': [],
        'cnpjs_found': [],
        'word_count': 0,
        'free_platform': False,
        'maintenance': False,
        'maintenance_90d_confirmed': False,
        'page_speed': {},
        'issues': [],
        'evidence': [],
        'checked_at': datetime.now(timezone.utc).isoformat(),
    }


def _is_oldish_html(soup: BeautifulSoup, html: str) -> bool:
    if soup.find('frameset') or soup.find('frame'):
        return True
    if len(soup.find_all('table')) > 8 and len(soup.find_all(['section', 'article', 'main'])) == 0:
        return True
    if re.search(r'jquery[.-](?:1\.|2\.0)', html, re.I):
        return True
    return False


async def _check_aux(client: httpx.AsyncClient, url: str) -> tuple[bool, bool]:
    origin = f'{urlparse(url).scheme}://{urlparse(url).netloc}'
    async def ok(path: str) -> bool:
        try:
            r = await client.get(urljoin(origin, path), timeout=8)
            return r.status_code < 400 and len(r.text or '') > 10
        except Exception:
            return False
    robots = await ok('/robots.txt')
    sitemap = await ok('/sitemap.xml')
    return robots, sitemap


async def _pagespeed(url: str) -> dict[str, Any]:
    if not ENABLE_PAGESPEED:
        return {}
    params: list[tuple[str, str]] = [('url', url), ('strategy', 'mobile')]
    for cat in ('performance', 'seo', 'accessibility', 'best-practices'):
        params.append(('category', cat))
    if PAGESPEED_API_KEY:
        params.append(('key', PAGESPEED_API_KEY))
    try:
        async with httpx.AsyncClient(timeout=45, follow_redirects=True, headers={'User-Agent': USER_AGENT}) as client:
            r = await client.get('https://www.googleapis.com/pagespeedonline/v5/runPagespeed', params=params)
            r.raise_for_status()
            data = r.json()
        cats = (((data.get('lighthouseResult') or {}).get('categories')) or {})
        def score(name: str):
            v = (cats.get(name) or {}).get('score')
            return round(v * 100) if isinstance(v, (int, float)) else None
        return {
            'performance': score('performance'),
            'seo': score('seo'),
            'accessibility': score('accessibility'),
            'best_practices': score('best-practices'),
        }
    except Exception as exc:
        return {'error': str(exc)[:180]}




async def _wayback_maintenance_90d(url: str) -> dict[str, Any]:
    if not ENABLE_WAYBACK:
        return {'checked': False, 'confirmed': False, 'snapshots': []}
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=100)
    params = {
        'url': url,
        'from': start.strftime('%Y%m%d'),
        'to': end.strftime('%Y%m%d'),
        'output': 'json',
        'filter': 'statuscode:200',
        'fl': 'timestamp,original,statuscode,digest',
        'collapse': 'digest',
        'limit': '8',
    }
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={'User-Agent': USER_AGENT}) as client:
            r = await client.get('https://web.archive.org/cdx/search/cdx', params=params)
            r.raise_for_status()
            rows = r.json()
            if not isinstance(rows, list) or len(rows) < 2:
                return {'checked': True, 'confirmed': False, 'snapshots': []}
            data = rows[1:]
            probes = []
            if data:
                probes.append(data[0])
            if len(data) > 1:
                probes.append(data[-1])
            maintenance_hits = []
            seen = []
            for row in probes:
                ts, original = row[0], row[1]
                snap = f'https://web.archive.org/web/{ts}id_/{original}'
                try:
                    sr = await client.get(snap, timeout=20)
                    text = BeautifulSoup(sr.text[:1_000_000], 'html.parser').get_text(' ', strip=True).lower()
                    hit = any(marker in text for marker in MAINTENANCE_MARKERS)
                    seen.append({'timestamp': ts, 'maintenance': hit})
                    if hit:
                        maintenance_hits.append(ts)
                except Exception:
                    continue
            confirmed = False
            if len(maintenance_hits) >= 2:
                d1 = datetime.strptime(maintenance_hits[0][:8], '%Y%m%d')
                d2 = datetime.strptime(maintenance_hits[-1][:8], '%Y%m%d')
                confirmed = abs((d2 - d1).days) >= 85
            return {'checked': True, 'confirmed': confirmed, 'snapshots': seen}
    except Exception as exc:
        return {'checked': True, 'confirmed': False, 'snapshots': [], 'error': str(exc)[:160]}


async def audit_website(url: str | None, deep: bool = True) -> dict[str, Any]:
    result = _base_result(url)
    if not url:
        result['issues'] = ['Não possui site próprio identificado']
        result['evidence'] = ['Nenhuma URL oficial foi encontrada nas fontes consultadas']
        return result

    if not re.match(r'^https?://', url, flags=re.I):
        url = 'https://' + url
    headers = {'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml'}
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True, headers=headers) as client:
            r = await client.get(url)
            elapsed = int((time.perf_counter() - start) * 1000)
            result['response_ms'] = elapsed
            result['http_status'] = r.status_code
            result['final_url'] = str(r.url)
            result['https'] = str(r.url).lower().startswith('https://')
            result['reachable'] = r.status_code < 500
            if r.status_code >= 400:
                result['status'] = 'quebrado'
                result['issues'].append(f'Site retorna HTTP {r.status_code}')
                return result

            content_type = r.headers.get('content-type', '')
            if 'text/html' not in content_type and '<html' not in (r.text[:1000].lower()):
                result['status'] = 'conteudo_invalido'
                result['issues'].append('URL oficial não retornou uma página HTML normal')
                return result

            html = r.text[:3_000_000]
            soup = BeautifulSoup(html, 'html.parser')
            text = ' '.join(soup.stripped_strings)
            low = text.lower()
            result['status'] = 'online'
            result['title'] = (soup.title.string.strip() if soup.title and soup.title.string else None)
            meta_desc = soup.find('meta', attrs={'name': re.compile('description', re.I)})
            result['meta_description'] = meta_desc.get('content', '').strip() if meta_desc else None
            result['h1_count'] = len(soup.find_all('h1'))
            result['has_viewport'] = bool(soup.find('meta', attrs={'name': re.compile('viewport', re.I)}))
            result['has_form'] = bool(soup.find('form'))
            result['has_schema'] = bool(soup.find('script', attrs={'type': 'application/ld+json'}))
            result['word_count'] = len(re.findall(r'\b\w+\b', text))
            result['maintenance'] = any(marker in low for marker in MAINTENANCE_MARKERS)
            result['free_platform'] = any(h in urlparse(str(r.url)).netloc.lower() for h in FREE_PLATFORM_HOSTS)
            result['has_whatsapp'] = 'wa.me/' in html.lower() or 'api.whatsapp.com' in html.lower() or 'whatsapp' in low
            cta_terms = ('orçamento', 'orcamento', 'agende', 'fale conosco', 'entre em contato', 'solicite', 'comprar', 'reservar', 'saiba mais')
            result['has_cta'] = any(term in low for term in cta_terms)
            result['has_privacy'] = 'política de privacidade' in low or 'politica de privacidade' in low or 'privacy policy' in low
            result['has_cookie_notice'] = 'cookie' in low and any(t in low for t in ('aceitar', 'consent', 'preferências', 'preferencias'))
            result['has_google_maps_embed'] = 'google.com/maps' in html.lower() or 'maps.google.com' in html.lower()
            result['has_analytics'] = 'google-analytics.com' in html.lower() or 'gtag(' in html.lower()
            result['has_tag_manager'] = 'googletagmanager.com' in html.lower()
            result['has_meta_pixel'] = 'connect.facebook.net' in html.lower() or 'fbq(' in html.lower()
            result['emails_found'] = sorted(set(EMAIL_RE.findall(text)))[:8]
            result['phones_found'] = sorted(set(m.group(0).strip() for m in PHONE_RE.finditer(text)))[:8]
            result['cnpjs_found'] = sorted(set(re.sub(r'\D', '', m.group(0)) for m in CNPJ_RE.finditer(text)))[:3]

            social = {}
            links = []
            for a in soup.find_all('a', href=True):
                href = urljoin(str(r.url), a['href'])
                label = ' '.join(a.stripped_strings).lower()
                links.append((href, label))
                host = urlparse(href).netloc.lower().replace('www.', '')
                for domain in SOCIAL_DOMAINS:
                    if domain in host:
                        social[domain.split('.')[0]] = href
            result['social_links'] = social
            result['has_contact_page'] = any('contat' in href.lower() or 'contat' in label for href, label in links)
            result['has_services_page'] = any(any(x in href.lower() or x in label for x in ('servic', 'tratamento', 'especialidade', 'solucoes', 'soluções')) for href, label in links)

            robots, sitemap = await _check_aux(client, str(r.url))
            result['has_robots'] = robots
            result['has_sitemap'] = sitemap

            if not result['https']:
                result['issues'].append('Site sem HTTPS')
            if not result['title'] or len(result['title']) < 8:
                result['issues'].append('Título SEO ausente ou fraco')
            if not result['meta_description']:
                result['issues'].append('Meta description ausente')
            if result['h1_count'] == 0:
                result['issues'].append('Sem H1 principal')
            if not result['has_viewport']:
                result['issues'].append('Sem viewport responsivo')
            if not result['has_whatsapp']:
                result['issues'].append('Sem WhatsApp identificável no site')
            if not result['has_form']:
                result['issues'].append('Sem formulário de contato/captação')
            if not result['has_cta']:
                result['issues'].append('Sem CTA comercial claro')
            if not result['has_schema']:
                result['issues'].append('Sem dados estruturados Schema.org identificados')
            if not result['has_sitemap']:
                result['issues'].append('Sitemap XML não identificado')
            if not result['has_robots']:
                result['issues'].append('robots.txt não identificado')
            if not result['has_privacy']:
                result['issues'].append('Política de privacidade não identificada')
            if result['free_platform']:
                result['issues'].append('Site hospedado em plataforma/domínio gratuito')
            if result['maintenance']:
                result['status'] = 'manutencao'
                result['issues'].append('Página indica manutenção/em breve')
            if _is_oldish_html(soup, html):
                result['issues'].append('Sinais técnicos de estrutura antiga/legada')
            if elapsed > 3000:
                result['issues'].append('Resposta inicial lenta (>3s)')

        if deep and result['reachable']:
            result['page_speed'] = await _pagespeed(result['final_url'])
            if result.get('maintenance'):
                history = await _wayback_maintenance_90d(result['final_url'])
                result['maintenance_history'] = history
                result['maintenance_90d_confirmed'] = bool(history.get('confirmed'))
                if result['maintenance_90d_confirmed']:
                    result['issues'].append('Manutenção confirmada historicamente por aproximadamente 90 dias')
            ps = result['page_speed']
            if isinstance(ps.get('performance'), int) and ps['performance'] < 50:
                result['issues'].append(f'Performance mobile baixa ({ps["performance"]}/100)')
            if isinstance(ps.get('seo'), int) and ps['seo'] < 80:
                result['issues'].append(f'SEO técnico abaixo do ideal ({ps["seo"]}/100)')
            if isinstance(ps.get('accessibility'), int) and ps['accessibility'] < 75:
                result['issues'].append(f'Acessibilidade baixa ({ps["accessibility"]}/100)')

    except httpx.TimeoutException:
        result['status'] = 'timeout'
        result['issues'].append('Site não respondeu dentro do tempo limite')
    except Exception as exc:
        result['status'] = 'erro'
        result['issues'].append(f'Falha ao abrir o site: {str(exc)[:140]}')
    return result
