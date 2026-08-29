from __future__ import annotations

import re

# Common PT-BR commercial niches -> OSM tags. Fallback searches named POIs/business-like features.
NICHE_TAGS: dict[str, list[tuple[str, str]]] = {
    'dentista': [('amenity', 'dentist')],
    'dentistas': [('amenity', 'dentist')],
    'clinica odontologica': [('amenity', 'dentist')],
    'restaurante': [('amenity', 'restaurant')],
    'restaurantes': [('amenity', 'restaurant')],
    'pizzaria': [('amenity', 'restaurant')],
    'lanchonete': [('amenity', 'fast_food')],
    'academia': [('leisure', 'fitness_centre')],
    'academias': [('leisure', 'fitness_centre')],
    'advogado': [('office', 'lawyer')],
    'advogados': [('office', 'lawyer')],
    'contabilidade': [('office', 'accountant')],
    'contador': [('office', 'accountant')],
    'imobiliaria': [('office', 'estate_agent')],
    'imobiliarias': [('office', 'estate_agent')],
    'farmacia': [('amenity', 'pharmacy')],
    'farmacias': [('amenity', 'pharmacy')],
    'veterinario': [('amenity', 'veterinary')],
    'clinica veterinaria': [('amenity', 'veterinary')],
    'salao': [('shop', 'hairdresser')],
    'salao de beleza': [('shop', 'hairdresser')],
    'barbearia': [('shop', 'hairdresser')],
    'oficina': [('shop', 'car_repair')],
    'oficina mecanica': [('shop', 'car_repair')],
    'auto escola': [('amenity', 'driving_school')],
    'escola': [('amenity', 'school')],
    'creche': [('amenity', 'kindergarten')],
    'hotel': [('tourism', 'hotel')],
    'pousada': [('tourism', 'guest_house')],
    'pet shop': [('shop', 'pet')],
    'mercado': [('shop', 'supermarket')],
    'supermercado': [('shop', 'supermarket')],
    'loja de roupa': [('shop', 'clothes')],
    'otica': [('shop', 'optician')],
    'clinica': [('amenity', 'clinic')],
    'fisioterapia': [('healthcare', 'physiotherapist')],
    'psicologo': [('healthcare', 'psychotherapist')],
    'arquiteto': [('office', 'architect')],
    'construtora': [('office', 'construction_company')],
}


def normalize_niche(niche: str) -> str:
    x = niche.lower().strip()
    x = re.sub(r'[^a-z0-9à-ÿ ]+', ' ', x)
    return re.sub(r'\s+', ' ', x)


def overpass_filters(niche: str) -> list[tuple[str, str]]:
    n = normalize_niche(niche)
    if n in NICHE_TAGS:
        return NICHE_TAGS[n]
    for key, tags in NICHE_TAGS.items():
        if key in n or n in key:
            return tags
    return []
