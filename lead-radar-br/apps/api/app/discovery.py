from __future__ import annotations

import math
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from .config import (
    ENABLE_SEARXNG,
    MAX_DISCOVERY_RESULTS,
    NOMINATIM_URL,
    OVERPASS_URL,
    REQUEST_TIMEOUT,
    SEARXNG_URL,
    USER_AGENT,
)
from .niches import overpass_filters

SOCIAL_HOSTS = {
    'instagram.com': 'instagram',
    'www.instagram.com': 'instagram',
    'facebook.com': 'facebook',
    'www.facebook.com': 'facebook',
    'linkedin.com': 'linkedin',
    'www.linkedin.com': 'linkedin',
    'tiktok.com': 'tiktok',
    'www.tiktok.com': 'tiktok',
}
DIRECTORY_HOST_PARTS = (
    'facebook.com', 'instagram.com', 'linkedin.com', 'tiktok.com', 'youtube.com',
    'ifood.com.br', 'tripadvisor.', 'yelp.', 'guiamais.com.br', 'solutudo.com.br',
    'telelistas.net', 'apontador.com.br', 'linktr.ee', 'wa.me', 'whatsapp.com',
    'google.', 'maps.', 'waze.com',
)


def _host(url: str) -> str:
    try:
        return urlparse(url if '://' in url else f'https://{url}').netloc.lower().split(':')[0]
    except Exception:
        return ''


def _clean_url(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if not re.match(r'^https?://', url, flags=re.I):
        url = 'https://' + url
    return url


def is_non_website(url: str | None) -> bool:
    if not url:
        return True
    host = _host(url)
    return any(part in host for part in DIRECTORY_HOST_PARTS)


async def geocode_location(location: str) -> dict[str, Any]:
    headers = {'User-Agent': USER_AGENT, 'Accept-Language': 'pt-BR,pt;q=0.9'}
    params = {'q': f'{location}, Brasil', 'format': 'jsonv2', 'limit': 1, 'countrycodes': 'br'}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True, headers=headers) as client:
        response = await client.get(f'{NOMINATIM_URL}/search', params=params)
        response.raise_for_status()
        data = response.json()
    if not data:
        raise ValueError(f'Local não encontrado: {location}')
    item = data[0]
    return {
        'lat': float(item['lat']),
        'lon': float(item['lon']),
        'display_name': item.get('display_name', location),
        'type': item.get('type'),
    }


def _overpass_query(lat: float, lon: float, radius_km: float, niche: str, max_results: int) -> str:
    radius_m = int(radius_km * 1000)
    filters = overpass_filters(niche)
    clauses: list[str] = []
    if filters:
        for key, value in filters:
            clauses.extend([
                f'node(around:{radius_m},{lat},{lon})["{key}"="{value}"]["name"];',
                f'way(around:{radius_m},{lat},{lon})["{key}"="{value}"]["name"];',
                f'relation(around:{radius_m},{lat},{lon})["{key}"="{value}"]["name"];',
            ])
    else:
        safe = re.sub(r'[^\wÀ-ÿ .&+-]', ' ', niche).strip()
        safe = safe.replace('"', '')
        clauses.extend([
            f'node(around:{radius_m},{lat},{lon})["name"~"{safe}",i];',
            f'way(around:{radius_m},{lat},{lon})["name"~"{safe}",i];',
            f'relation(around:{radius_m},{lat},{lon})["name"~"{safe}",i];',
        ])
    return f'''[out:json][timeout:60];(
{chr(10).join(clauses)}
);out center {min(max_results, MAX_DISCOVERY_RESULTS)};'''


def _address_from_tags(tags: dict[str, Any]) -> str | None:
    parts = [
        tags.get('addr:street'),
        tags.get('addr:housenumber'),
        tags.get('addr:suburb') or tags.get('addr:neighbourhood'),
        tags.get('addr:city'),
        tags.get('addr:state'),
    ]
    return ', '.join(str(x) for x in parts if x) or None


def _category_from_tags(tags: dict[str, Any]) -> str | None:
    for key in ('amenity', 'shop', 'office', 'tourism', 'leisure', 'healthcare', 'craft'):
        if tags.get(key):
            return f'{key}:{tags[key]}'
    return None


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def discover_overpass(lat: float, lon: float, radius_km: float, niche: str, max_results: int) -> list[dict[str, Any]]:
    query = _overpass_query(lat, lon, radius_km, niche, max_results)
    headers = {'User-Agent': USER_AGENT}
    async with httpx.AsyncClient(timeout=75, follow_redirects=True, headers=headers) as client:
        response = await client.post(OVERPASS_URL, data={'data': query})
        response.raise_for_status()
        data = response.json()

    rows: list[dict[str, Any]] = []
    for el in data.get('elements', []):
        tags = el.get('tags') or {}
        name = (tags.get('name') or '').strip()
        if not name:
            continue
        item_lat = el.get('lat') or (el.get('center') or {}).get('lat')
        item_lon = el.get('lon') or (el.get('center') or {}).get('lon')
        if item_lat is None or item_lon is None:
            continue
        website = _clean_url(tags.get('website') or tags.get('contact:website') or tags.get('url'))
        phone = tags.get('contact:phone') or tags.get('phone') or tags.get('contact:mobile')
        email = tags.get('contact:email') or tags.get('email')
        social: dict[str, str] = {}
        for key, value in tags.items():
            if not value:
                continue
            if key in ('contact:instagram', 'instagram'):
                social['instagram'] = str(value)
            elif key in ('contact:facebook', 'facebook'):
                social['facebook'] = str(value)
            elif key in ('contact:linkedin', 'linkedin'):
                social['linkedin'] = str(value)
        rows.append({
            'name': name,
            'category': _category_from_tags(tags),
            'city': tags.get('addr:city'),
            'state': tags.get('addr:state'),
            'neighborhood': tags.get('addr:suburb') or tags.get('addr:neighbourhood'),
            'address': _address_from_tags(tags),
            'lat': float(item_lat),
            'lon': float(item_lon),
            'distance_km': round(_distance_km(lat, lon, float(item_lat), float(item_lon)), 2),
            'phone': phone,
            'email': email,
            'website': website,
            'social': social,
            'osm': {'type': el.get('type'), 'id': el.get('id'), 'tags': tags},
        })

    # De-duplicate conservatively by normalized name + rounded coordinates.
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, float, float]] = set()
    for row in rows:
        key = (re.sub(r'\W+', '', row['name'].lower()), round(row['lat'], 4), round(row['lon'], 4))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped[:max_results]


async def searx_search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    if not ENABLE_SEARXNG:
        return []
    headers = {'User-Agent': USER_AGENT}
    params = {'q': query, 'format': 'json', 'language': 'pt-BR', 'safesearch': 1}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True, headers=headers) as client:
            response = await client.get(f'{SEARXNG_URL.rstrip("/")}/search', params=params)
            response.raise_for_status()
            data = response.json()
        return (data.get('results') or [])[:limit]
    except Exception:
        return []


async def enrich_from_web(row: dict[str, Any], location_hint: str) -> dict[str, Any]:
    query = f'"{row["name"]}" {location_hint}'
    results = await searx_search(query, limit=12)
    social = dict(row.get('social') or {})
    website = row.get('website')
    web_candidates: list[dict[str, str]] = []

    for result in results:
        url = result.get('url') or ''
        if not url:
            continue
        host = _host(url)
        social_name = SOCIAL_HOSTS.get(host)
        if social_name and social_name not in social:
            social[social_name] = url
            continue
        if any(p in host for p in DIRECTORY_HOST_PARTS):
            continue
        web_candidates.append({'url': url, 'title': result.get('title') or '', 'engine': ','.join(result.get('engines') or [])})

    if not website and web_candidates:
        # Require brand-token overlap to reduce false official-site matches.
        brand_tokens = [t for t in re.findall(r'[a-z0-9]+', row['name'].lower()) if len(t) >= 4]
        for candidate in web_candidates:
            hay = (candidate['title'] + ' ' + candidate['url']).lower()
            if not brand_tokens or any(token in hay for token in brand_tokens):
                website = _clean_url(candidate['url'])
                break

    official_position = None
    official_engines: list[str] = []
    if website:
        official_host = _host(website).replace('www.', '')
        for idx, result in enumerate(results, start=1):
            host = _host(result.get('url') or '').replace('www.', '')
            if host == official_host or host.endswith('.' + official_host):
                official_position = idx
                official_engines = result.get('engines') or []
                break

    return {
        **row,
        'website': website,
        'social': social,
        'web_search': {
            'query': query,
            'result_count': len(results),
            'official_position': official_position,
            'official_engines': official_engines,
            'candidates': web_candidates[:5],
        },
    }
