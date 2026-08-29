# Lead Radar BR

Sistema local-first para descobrir, enriquecer, auditar e priorizar leads brasileiros para venda de sites.

A versão atual foi desenhada para **custo de API zero no núcleo**. Ela usa serviços abertos/gratuitos com limites responsáveis e mantém conectores pagos/oficiais como opcionais para o futuro.

## O que já está implementado

- Busca por **nicho + cidade/bairro/estado + raio de 1 a 100 km**.
- Descoberta geográfica por OpenStreetMap/Overpass.
- Deduplicação conservadora de empresas.
- Enriquecimento web por SearXNG local.
- Identificação de site oficial sem confundir Instagram, Facebook, LinkedIn, Linktree, WhatsApp, iFood e diretórios com site próprio.
- Extração de telefone, e-mail, links sociais e CNPJ quando aparecem publicamente no site.
- Enriquecimento cadastral via BrasilAPI quando um CNPJ válido é encontrado.
- Auditoria técnica do site: HTTP/HTTPS, disponibilidade, responsividade, title, meta description, H1, CTA, formulário, WhatsApp, Schema.org, sitemap, robots.txt, privacidade/LGPD, cookies, Google Maps embed, Analytics, Tag Manager, Meta Pixel, páginas de contato/serviços e sinais de tecnologia antiga.
- PageSpeed mobile para performance, SEO, acessibilidade e boas práticas.
- Detecção de página “em manutenção/em breve”.
- Verificação histórica opcional via Wayback para só marcar **manutenção ~90 dias** quando houver evidência suficiente.
- Lead Score 0–100.
- Classificação **Topo / Meio / Fundo**.
- Confiança dos dados 0–100.
- Recomendação do que vender: site, redesign, SEO, performance, conversão por WhatsApp, captação e privacidade.
- Mensagens de abordagem para WhatsApp, e-mail e Instagram com base nas falhas reais detectadas.
- CRM leve com etapas: Novo → Analisado → Contatado → Respondeu → Reunião → Proposta → Cliente / Perdido.
- Filtros e exportação CSV.
- Interface dark glassmorphism responsiva, sem estética genérica de “produto de IA”.

## Fontes gratuitas do núcleo

1. **OpenStreetMap / Overpass** — descoberta de negócios e dados geográficos.
2. **Nominatim** — geocodificação de uma localidade digitada pelo usuário.
3. **SearXNG self-hosted** — metabusca para encontrar site oficial e presença pública na web.
4. **Website público da própria empresa** — auditoria e enriquecimento de contato.
5. **Google PageSpeed Insights** — auditoria técnica; sem chave funciona para uso moderado, chave é recomendada para automação frequente.
6. **BrasilAPI** — dados empresariais por CNPJ quando o CNPJ já foi identificado.
7. **Wayback Machine** — opcional, apenas para evidência histórica de manutenção.

## Limite importante sobre “100% grátis + todas as fontes”

Não existe hoje uma maneira confiável, ilimitada e compatível com os termos das plataformas de extrair automaticamente todos os dados do Google Maps, LinkedIn, Instagram e Facebook sem custos/limites ou autorização.

Por isso esta versão não faz scraping agressivo dessas plataformas. Ela encontra links públicos por pesquisa web e deixa conectores oficiais como módulos futuros. Isso evita que o sistema dependa de algo que pode quebrar, bloquear sua conta ou violar termos de uso.

O Google Maps Platform possui franquias mensais gratuitas por SKU, mas não é um serviço ilimitado sem cobrança. LinkedIn proíbe crawling/scraping automatizado sem autorização expressa.

## Início rápido com Docker

Pré-requisitos:

- Docker Desktop
- Docker Compose
- Internet durante o uso para consultar as fontes públicas

Na pasta do projeto:

```bash
docker compose up --build
```

Depois abra:

- Interface: `http://localhost:5173`
- API: `http://localhost:8000`
- SearXNG local: `http://localhost:8080`

## Primeiro teste visual

Na tela inicial, use **Carregar demonstração** para ver a interface sem consultar a internet.

Para dados reais, vá em **Nova busca**, escolha por exemplo:

- Nicho: `dentistas`
- Localidade: `São Paulo, SP`
- Raio: `5 km`
- Profundidade: `Profunda`
- Máximo: `25`

Comece pequeno porque Overpass, Nominatim e PageSpeed são serviços públicos com limites de uso responsável.

## Execução sem Docker

### Backend

```bash
cd apps/api
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### SearXNG

A forma mais simples é subir apenas o serviço do compose:

```bash
docker compose up searxng
```

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

## Configuração

Copie `.env.example` para `.env` se executar fora do Docker.

Principais opções:

- `MAX_DISCOVERY_RESULTS` — limite absoluto por busca.
- `MAX_DEEP_AUDITS` — quantidade de sites que recebem PageSpeed por busca profunda.
- `ENABLE_SEARXNG` — ativa/desativa enriquecimento web.
- `ENABLE_PAGESPEED` — ativa/desativa PageSpeed.
- `PAGESPEED_API_KEY` — opcional.
- `ENABLE_WAYBACK` — ativa a verificação histórica de manutenção.

## Como funciona o score

O score não significa “certeza de compra”. Ele prioriza **oportunidade + possibilidade de contato + evidência**.

Exemplos de sinais positivos para prospecção:

- sem site próprio;
- site quebrado/fora do ar;
- página em manutenção;
- várias falhas técnicas/comerciais;
- performance mobile ruim;
- SEO técnico fraco;
- site em plataforma gratuita;
- telefone/e-mail disponíveis;
- presença social;
- endereço/categoria consistentes em fonte geográfica;
- site existente que não apareceu na busca pública consultada.

A classificação atual:

- **Fundo**: score ≥ 78 e existe algum canal de contato.
- **Meio**: score ≥ 55.
- **Topo**: abaixo de 55 ou ainda precisa de mais evidência.

## Precisão e evidência

O sistema nunca deve transformar “não encontrei” em “não existe” sem contexto. Por isso cada lead tem **confiança dos dados** e alertas.

Exemplo: se um site existe mas não aparece no SearXNG, o sistema diz que **não apareceu na busca pública consultada**. Ele não afirma automaticamente “não aparece no Google”. Para essa afirmação, a etapa futura deve usar um conector Google apropriado ou confirmação no Search Console.

## Arquitetura

```text
Discovery Engine
  └─ OSM/Overpass + Nominatim
        ↓
Enrichment Engine
  └─ SearXNG + site público + BrasilAPI
        ↓
Audit Engine
  └─ HTML + PageSpeed + histórico opcional
        ↓
Qualification Engine
  └─ score + confiança + Topo/Meio/Fundo
        ↓
Sales Intelligence
  └─ serviço recomendado + abordagem
        ↓
CRM / Pipeline / Exportação
```

## Próximos módulos recomendados

- Conector opcional Google Places para nota, avaliações, categoria e Place ID dentro da franquia/cota configurada.
- Importador da base aberta do CNPJ/Receita para descoberta nacional por CNAE + município sem depender de mapas.
- Validador de WhatsApp com método oficial/consentido.
- Verificação SMTP de e-mail com cuidado para evitar falsos positivos e bloqueios.
- Histórico de notas e follow-ups no CRM.
- Agenda e lembretes.
- Busca recorrente e alertas de novos leads.
- Multiusuário, autenticação e cobrança para futura versão SaaS.
- Worker/queue persistente para buscas grandes.
- PostgreSQL no lugar de SQLite quando houver múltiplos usuários.
- Conectores oficiais para Google/Meta/LinkedIn quando houver acesso autorizado.

## Referências das políticas/documentações usadas no desenho

- Nominatim Usage Policy: https://operations.osmfoundation.org/policies/nominatim/
- Overpass API: https://wiki.openstreetmap.org/wiki/Overpass_API
- SearXNG Search API: https://docs.searxng.org/dev/search_api.html
- PageSpeed Insights API: https://developers.google.com/speed/docs/insights/v5/get-started
- BrasilAPI CNPJ: https://brasilapi.com.br/docs
- Google Maps pricing: https://mapsplatform.google.com/pricing/
- LinkedIn crawling terms: https://www.linkedin.com/legal/crawling-terms

## Observação sobre uso dos serviços públicos

O endpoint público do Nominatim não é adequado para consultas sistemáticas em massa e exige limite baixo de requisições. O projeto usa Nominatim apenas para geocodificar a localidade digitada. A descoberta em raio é feita pelo Overpass. Para escala comercial no futuro, hospede sua própria infraestrutura geográfica ou use um provedor adequado.
