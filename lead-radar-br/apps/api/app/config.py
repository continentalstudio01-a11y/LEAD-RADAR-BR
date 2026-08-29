from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / '.env')

DB_PATH = os.getenv('DB_PATH', str(ROOT / 'data' / 'leads.db'))
USER_AGENT = os.getenv('USER_AGENT', 'LeadRadarBR/0.1 (local research tool; contact: local-user)')
OVERPASS_URL = os.getenv('OVERPASS_URL', 'https://overpass-api.de/api/interpreter')
NOMINATIM_URL = os.getenv('NOMINATIM_URL', 'https://nominatim.openstreetmap.org')
SEARXNG_URL = os.getenv('SEARXNG_URL', 'http://localhost:8080')
ENABLE_SEARXNG = os.getenv('ENABLE_SEARXNG', 'true').lower() == 'true'
ENABLE_PAGESPEED = os.getenv('ENABLE_PAGESPEED', 'true').lower() == 'true'
PAGESPEED_API_KEY = os.getenv('PAGESPEED_API_KEY', '')
ENABLE_WAYBACK = os.getenv('ENABLE_WAYBACK', 'false').lower() == 'true'
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
ENABLE_OLLAMA = os.getenv('ENABLE_OLLAMA', 'false').lower() == 'true'
REQUEST_TIMEOUT = float(os.getenv('REQUEST_TIMEOUT', '15'))
MAX_DISCOVERY_RESULTS = int(os.getenv('MAX_DISCOVERY_RESULTS', '250'))
MAX_DEEP_AUDITS = int(os.getenv('MAX_DEEP_AUDITS', '30'))
