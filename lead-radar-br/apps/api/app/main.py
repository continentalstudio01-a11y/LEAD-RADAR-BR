from __future__ import annotations

import asyncio
import csv
import io
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .audit import audit_website
from .config import MAX_DEEP_AUDITS
from .db import connect, init_db, row_to_lead, row_to_search
from .discovery import discover_overpass, enrich_from_web, geocode_location, is_non_website
from .models import LeadNoteInput, LeadStageUpdate, SearchCreate
from .recommender import approach_text, recommend_services
from .registry import lookup_cnpj
from .scoring import calculate_score

app = FastAPI(title='Lead Radar BR API', version='0.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.on_event('startup')
def startup() -> None:
    init_db()


@app.get('/health')
def health():
    return {'ok': True, 'service': 'lead-radar-br'}


def _insert_search(search_id: str, req: SearchCreate):
    conn = connect()
    conn.execute(
        '''INSERT INTO searches(id,niche,location,radius_km,depth,status,created_at,settings_json)
           VALUES(?,?,?,?,?,?,?,?)''',
        (
            search_id,
            req.niche,
            req.location,
            req.radius_km,
            req.depth,
            'queued',
            now(),
            json.dumps(req.model_dump(), ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


def _set_search(search_id: str, **fields):
    if not fields:
        return
    conn = connect()
    keys = list(fields.keys())
    sql = 'UPDATE searches SET ' + ', '.join(f'{k}=?' for k in keys) + ' WHERE id=?'
    conn.execute(sql, [fields[k] for k in keys] + [search_id])
    conn.commit()
    conn.close()


def _store_lead(search_id: str, lead: dict[str, Any]):
    lead_id = lead.get('id') or str(uuid.uuid4())
    created = now()
    conn = connect()
    try:
        conn.execute(
            '''INSERT OR REPLACE INTO leads(
                id,search_id,name,category,city,state,neighborhood,address,lat,lon,phone,email,website,cnpj,
                source_json,social_json,audit_json,recommendation_json,score,funnel,stage,confidence,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                lead_id,
                search_id,
                lead.get('name'),
                lead.get('category'),
                lead.get('city'),
                lead.get('state'),
                lead.get('neighborhood'),
                lead.get('address'),
                lead.get('lat'),
                lead.get('lon'),
                lead.get('phone'),
                lead.get('email'),
                lead.get('website'),
                lead.get('cnpj'),
                json.dumps({
                    'osm': lead.get('osm'),
                    'web_search': lead.get('web_search'),
                    'distance_km': lead.get('distance_km'),
                    'registry': lead.get('registry'),
                }, ensure_ascii=False),
                json.dumps(lead.get('social') or {}, ensure_ascii=False),
                json.dumps(lead.get('audit') or {}, ensure_ascii=False),
                json.dumps(lead.get('recommendation') or {}, ensure_ascii=False),
                int(lead.get('score') or 0),
                lead.get('funnel') or 'Topo',
                lead.get('stage') or 'Novo',
                int(lead.get('confidence') or 0),
                created,
                created,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return lead_id


async def _process_candidate(row: dict[str, Any], req: SearchCreate, index: int) -> dict[str, Any]:
    enriched = await enrich_from_web(row, req.location)

    # If OSM had a social/directory URL in website field, do not treat it as an owned website.
    if enriched.get('website') and is_non_website(enriched['website']):
        enriched.setdefault('social', {})['other'] = enriched['website']
        enriched['website'] = None

    deep = req.depth == 'profunda' and index < MAX_DEEP_AUDITS
    enriched['audit'] = await audit_website(enriched.get('website'), deep=deep)

    # Fill missing contact info from the official site audit.
    if not enriched.get('email'):
        emails = enriched['audit'].get('emails_found') or []
        enriched['email'] = emails[0] if emails else None
    if not enriched.get('phone'):
        phones = enriched['audit'].get('phones_found') or []
        enriched['phone'] = phones[0] if phones else None
    merged_social = dict(enriched.get('social') or {})
    merged_social.update(enriched['audit'].get('social_links') or {})
    enriched['social'] = merged_social

    cnpjs = enriched['audit'].get('cnpjs_found') or []
    registry = await lookup_cnpj(cnpjs[0]) if cnpjs else None
    if registry:
        enriched['cnpj'] = registry.get('cnpj')
        enriched['registry'] = registry
        if not enriched.get('email') and registry.get('email'):
            enriched['email'] = registry['email']
        if not enriched.get('phone') and registry.get('ddd_telefone_1'):
            enriched['phone'] = registry['ddd_telefone_1']
        if not enriched.get('city') and registry.get('municipio'):
            enriched['city'] = registry['municipio']
        if not enriched.get('state') and registry.get('uf'):
            enriched['state'] = registry['uf']

    score, funnel, confidence, reasons = calculate_score(enriched)
    enriched['score'] = score
    enriched['funnel'] = funnel
    enriched['confidence'] = confidence
    enriched['score_reasons'] = reasons
    enriched['recommendation'] = recommend_services(enriched)
    enriched['recommendation']['score_reasons'] = reasons
    return enriched


async def run_search(search_id: str, req: SearchCreate):
    try:
        _set_search(search_id, status='running')
        center = await geocode_location(req.location)
        candidates = await discover_overpass(
            center['lat'], center['lon'], req.radius_km, req.niche, req.max_results
        )
        _set_search(
            search_id,
            total_found=len(candidates),
            settings_json=json.dumps({**req.model_dump(), 'center': center}, ensure_ascii=False),
        )

        # Be considerate with public services: moderate concurrency.
        semaphore = asyncio.Semaphore(4)

        async def wrapped(row, idx):
            async with semaphore:
                return await _process_candidate(row, req, idx)

        tasks = [wrapped(row, idx) for idx, row in enumerate(candidates)]
        processed: list[dict[str, Any]] = []
        for coro in asyncio.as_completed(tasks):
            try:
                lead = await coro
            except Exception:
                continue
            if req.only_without_site and lead.get('website'):
                continue
            if lead.get('score', 0) < req.min_score:
                continue
            _store_lead(search_id, lead)
            processed.append(lead)

        _set_search(search_id, status='done', qualified=len(processed), finished_at=now())
    except Exception as exc:
        _set_search(search_id, status='error', error=str(exc)[:500], finished_at=now())


@app.post('/api/searches')
async def create_search(req: SearchCreate, background_tasks: BackgroundTasks):
    search_id = str(uuid.uuid4())
    _insert_search(search_id, req)
    background_tasks.add_task(run_search, search_id, req)
    return {'id': search_id, 'status': 'queued'}


@app.get('/api/searches')
def list_searches(limit: int = Query(20, ge=1, le=100)):
    conn = connect()
    rows = conn.execute('SELECT * FROM searches ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [row_to_search(r) for r in rows]


@app.get('/api/searches/{search_id}')
def get_search(search_id: str):
    conn = connect()
    row = conn.execute('SELECT * FROM searches WHERE id=?', (search_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, 'Busca não encontrada')
    return row_to_search(row)


@app.get('/api/leads')
def list_leads(
    search_id: str | None = None,
    funnel: str | None = None,
    stage: str | None = None,
    min_score: int = Query(0, ge=0, le=100),
    has_site: bool | None = None,
    q: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
):
    where = ['score >= ?']
    args: list[Any] = [min_score]
    if search_id:
        where.append('search_id=?')
        args.append(search_id)
    if funnel:
        where.append('funnel=?')
        args.append(funnel)
    if stage:
        where.append('stage=?')
        args.append(stage)
    if has_site is True:
        where.append("website IS NOT NULL AND website != ''")
    if has_site is False:
        where.append("(website IS NULL OR website = '')")
    if q:
        where.append('(lower(name) LIKE ? OR lower(city) LIKE ? OR lower(category) LIKE ?)')
        like = f'%{q.lower()}%'
        args.extend([like, like, like])
    args.append(limit)
    conn = connect()
    rows = conn.execute(
        f'SELECT * FROM leads WHERE {" AND ".join(where)} ORDER BY score DESC, confidence DESC LIMIT ?',
        args,
    ).fetchall()
    conn.close()
    return [row_to_lead(r) for r in rows]


@app.get('/api/leads/{lead_id}')
def get_lead(lead_id: str):
    conn = connect()
    row = conn.execute('SELECT * FROM leads WHERE id=?', (lead_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, 'Lead não encontrado')
    return row_to_lead(row)


@app.patch('/api/leads/{lead_id}/stage')
def update_stage(lead_id: str, payload: LeadStageUpdate):
    conn = connect()
    cur = conn.execute('UPDATE leads SET stage=?, updated_at=? WHERE id=?', (payload.stage, now(), lead_id))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(404, 'Lead não encontrado')
    return {'ok': True, 'stage': payload.stage}


@app.post('/api/leads/{lead_id}/approach')
def generate_approach(lead_id: str, payload: LeadNoteInput):
    lead = get_lead(lead_id)
    return {'channel': payload.channel, 'text': approach_text(lead, payload.channel)}


@app.get('/api/dashboard')
def dashboard():
    conn = connect()
    total = conn.execute('SELECT COUNT(*) c FROM leads').fetchone()['c']
    hot = conn.execute("SELECT COUNT(*) c FROM leads WHERE funnel='Fundo'").fetchone()['c']
    without_site = conn.execute("SELECT COUNT(*) c FROM leads WHERE website IS NULL OR website=''").fetchone()['c']
    avg = conn.execute('SELECT COALESCE(ROUND(AVG(score)),0) a FROM leads').fetchone()['a']
    by_stage = [dict(r) for r in conn.execute('SELECT stage, COUNT(*) total FROM leads GROUP BY stage ORDER BY total DESC').fetchall()]
    top = [row_to_lead(r) for r in conn.execute('SELECT * FROM leads ORDER BY score DESC, confidence DESC LIMIT 6').fetchall()]
    searches = [row_to_search(r) for r in conn.execute('SELECT * FROM searches ORDER BY created_at DESC LIMIT 5').fetchall()]
    conn.close()
    return {
        'total_leads': total,
        'hot_leads': hot,
        'without_site': without_site,
        'avg_score': avg,
        'by_stage': by_stage,
        'top_leads': top,
        'recent_searches': searches,
    }


@app.get('/api/export.csv')
def export_csv(min_score: int = Query(0, ge=0, le=100)):
    leads = list_leads(min_score=min_score, limit=1000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['empresa', 'score', 'funil', 'etapa', 'telefone', 'email', 'site', 'cidade', 'endereco', 'oportunidade'])
    for lead in leads:
        writer.writerow([
            lead.get('name'), lead.get('score'), lead.get('funnel'), lead.get('stage'), lead.get('phone'),
            lead.get('email'), lead.get('website'), lead.get('city'), lead.get('address'),
            (lead.get('recommendation') or {}).get('headline'),
        ])
    output.seek(0)
    headers = {'Content-Disposition': 'attachment; filename="lead-radar-br.csv"'}
    return StreamingResponse(iter([output.getvalue()]), media_type='text/csv; charset=utf-8', headers=headers)


@app.post('/api/demo/seed')
def seed_demo():
    search_id = 'demo-search'
    conn = connect()
    exists = conn.execute('SELECT 1 FROM searches WHERE id=?', (search_id,)).fetchone()
    if not exists:
        conn.execute(
            'INSERT INTO searches(id,niche,location,radius_km,depth,status,total_found,qualified,created_at,finished_at,settings_json) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
            (search_id, 'clinicas', 'São Paulo, SP', 12, 'profunda', 'done', 3, 3, now(), now(), '{}'),
        )
        conn.commit()
    conn.close()

    demo = [
        {
            'name': 'Clínica Horizonte', 'category': 'amenity:clinic', 'city': 'São Paulo', 'state': 'SP',
            'address': 'Pinheiros, São Paulo - SP', 'phone': '(11) 99999-0188', 'email': None, 'website': None,
            'lat': -23.56, 'lon': -46.68, 'social': {'instagram': 'https://instagram.com/exemplo'},
            'osm': {'demo': True}, 'web_search': {'result_count': 8, 'official_position': None},
            'audit': {'status': 'sem_site', 'issues': ['Não possui site próprio identificado'], 'emails_found': [], 'phones_found': []},
        },
        {
            'name': 'Odonto Prime Bairro', 'category': 'amenity:dentist', 'city': 'São Paulo', 'state': 'SP',
            'address': 'Moema, São Paulo - SP', 'phone': '(11) 98888-4422', 'email': 'contato@exemplo.com.br', 'website': 'https://exemplo.com.br',
            'lat': -23.60, 'lon': -46.66, 'social': {'instagram': 'https://instagram.com/exemplo'},
            'osm': {'demo': True}, 'web_search': {'result_count': 10, 'official_position': None},
            'audit': {'status': 'online', 'issues': ['Performance mobile baixa (42/100)', 'Meta description ausente', 'Sem dados estruturados Schema.org identificados', 'Sem formulário de contato/captação', 'Sem CTA comercial claro'], 'page_speed': {'performance': 42, 'seo': 73}, 'emails_found': [], 'phones_found': [], 'has_whatsapp': True, 'has_form': False, 'has_privacy': False},
        },
        {
            'name': 'Studio Forma', 'category': 'leisure:fitness_centre', 'city': 'São Paulo', 'state': 'SP',
            'address': 'Vila Mariana, São Paulo - SP', 'phone': '(11) 97777-3011', 'email': None, 'website': 'https://exemplo2.com.br',
            'lat': -23.59, 'lon': -46.63, 'social': {}, 'osm': {'demo': True}, 'web_search': {'result_count': 6, 'official_position': 4},
            'audit': {'status': 'online', 'issues': ['Sem WhatsApp identificável no site', 'Sem formulário de contato/captação', 'Política de privacidade não identificada'], 'page_speed': {'performance': 68, 'seo': 88}, 'emails_found': [], 'phones_found': [], 'has_whatsapp': False, 'has_form': False, 'has_privacy': False},
        },
    ]
    for item in demo:
        score, funnel, confidence, reasons = calculate_score(item)
        item.update(score=score, funnel=funnel, confidence=confidence)
        item['recommendation'] = recommend_services(item)
        item['recommendation']['score_reasons'] = reasons
        _store_lead(search_id, item)
    return {'ok': True}
