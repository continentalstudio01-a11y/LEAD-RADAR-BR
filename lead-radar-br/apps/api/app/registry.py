from __future__ import annotations

import re
from typing import Any
import httpx

from .config import REQUEST_TIMEOUT, USER_AGENT

CNPJ_DIGITS_RE = re.compile(r'\b\d{14}\b')


def normalize_cnpj(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r'\D', '', value)
    return digits if len(digits) == 14 else None


async def lookup_cnpj(cnpj: str | None) -> dict[str, Any] | None:
    cnpj = normalize_cnpj(cnpj)
    if not cnpj:
        return None
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers={'User-Agent': USER_AGENT}) as client:
            r = await client.get(f'https://brasilapi.com.br/api/cnpj/v1/{cnpj}')
            if r.status_code == 404:
                return None
            r.raise_for_status()
            data = r.json()
        return {
            'cnpj': cnpj,
            'razao_social': data.get('razao_social'),
            'nome_fantasia': data.get('nome_fantasia'),
            'situacao_cadastral': data.get('descricao_situacao_cadastral'),
            'cnae_fiscal': data.get('cnae_fiscal'),
            'cnae_fiscal_descricao': data.get('cnae_fiscal_descricao'),
            'porte': data.get('porte'),
            'capital_social': data.get('capital_social'),
            'municipio': data.get('municipio'),
            'uf': data.get('uf'),
            'email': data.get('email'),
            'ddd_telefone_1': data.get('ddd_telefone_1'),
            'ddd_telefone_2': data.get('ddd_telefone_2'),
            'data_inicio_atividade': data.get('data_inicio_atividade'),
        }
    except Exception:
        return None
