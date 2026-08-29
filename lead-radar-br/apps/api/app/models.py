from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


class SearchCreate(BaseModel):
    niche: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=180)
    radius_km: float = Field(default=10, ge=1, le=100)
    depth: Literal['rapida', 'profunda'] = 'profunda'
    min_score: int = Field(default=0, ge=0, le=100)
    only_without_site: bool = False
    max_results: int = Field(default=100, ge=10, le=500)


class LeadStageUpdate(BaseModel):
    stage: Literal['Novo', 'Analisado', 'Contatado', 'Respondeu', 'Reuniao', 'Proposta', 'Cliente', 'Perdido']


class LeadNoteInput(BaseModel):
    channel: Literal['whatsapp', 'email', 'instagram'] = 'whatsapp'
