# Arquitetura funcional — Lead Radar BR

## Entidades

### Search
- niche
- location
- radius_km
- depth
- min_score
- only_without_site
- max_results
- status
- center coordinates

### Lead
- identity: name, category, location, coordinates
- contact: phone, email, website, socials, CNPJ
- evidence: OSM, web search, registry
- audit: technical/commercial findings
- score + confidence + funnel
- recommendation
- CRM stage

## Pipeline de busca

1. Geocodifica a localidade uma vez.
2. Converte o nicho em tags OSM conhecidas; se o nicho não for conhecido, usa fallback por nome.
3. Consulta Overpass no raio escolhido.
4. Deduplica por nome normalizado + coordenadas.
5. Pesquisa cada empresa no SearXNG para encontrar site e redes.
6. Rejeita redes sociais/diretórios como “site próprio”.
7. Abre o site oficial e executa auditoria.
8. Extrai contatos e CNPJ exibidos publicamente.
9. Consulta BrasilAPI se houver CNPJ.
10. Executa PageSpeed em uma quantidade controlada de sites por busca profunda.
11. Calcula score e confiança.
12. Gera recomendação de serviço.
13. Persiste no SQLite e disponibiliza no CRM.

## Estratégia de escala futura

- trocar BackgroundTasks por Redis + worker;
- SQLite → PostgreSQL;
- limitar e enfileirar requests por domínio;
- cache por empresa, domínio e coordenada;
- histórico de auditoria por data;
- provider interface para OSM, Google Places, bases empresariais e APIs oficiais;
- resolver entidades com fuzzy matching + CNPJ/telefone/domínio;
- observabilidade de cada evidência e timestamp;
- autenticação e RBAC para SaaS.
