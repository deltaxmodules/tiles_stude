# Explicação do Projeto: Cognitive Streaming (MVP)

## 1. O que é este projeto
O **Cognitive Streaming** é um MVP de investigação para runtime local de IA, inspirado no conceito de carregamento progressivo por módulos.

A ideia principal é:
- Não tratar todos os pedidos com a mesma lógica/modelo.
- Classificar o pedido por tipo (ex.: `code`, `reasoning`, `general`).
- Encaminhar para um "tile" especializado.
- Reutilizar respostas semanticamente semelhantes via cache.
- Pré-aquecer modelos para reduzir latência em pedidos futuros.

## 2. Objetivo do MVP
Este MVP valida quatro hipóteses:
1. **Routing semântico** melhora adequação do modelo ao pedido.
2. **Tiles especializados** permitem controlo de comportamento por domínio.
3. **Cache semântica** reduz custo/latência em perguntas parecidas.
4. **Prewarm** melhora experiência em cenários repetitivos.

## 3. Estrutura atual (modular)
A base do projeto foi refatorada para arquitetura modular:

- `app/main.py`
  - Inicializa FastAPI.
  - Monta assets estáticos da UI.
  - Expõe endpoint `/` (interface).

- `app/api/routes.py`
  - Endpoints HTTP (`/health`, `/tiles`, `/v1/chat/completions`).
  - Orquestra fluxo: route -> cache -> geração -> persistência -> trace.

- `app/services/router.py`
  - Classificação semântica do pedido em rotas (`code`, `reasoning`, `general`).

- `app/services/tile_loader.py`
  - Carrega manifestos YAML dos tiles em `tiles/*.yaml`.

- `app/services/streaming.py`
  - Comunicação com Ollama para gerar tokens/resposta.

- `app/services/scheduler.py`
  - Prewarm de tiles com base no histórico de rotas.

- `app/infra/cache_layer.py`
  - Cache semântica em SQLite com embeddings.

- `app/infra/ollama_client.py`
  - Cliente de apoio para chamadas ao Ollama.

- `app/config.py`
  - Configuração centralizada por environment variables (com validação tipada).

- `app/web/`
  - Interface web de experimentação (chat + execution trace).

## 4. Como funciona o mecanismo (passo a passo)
Quando o frontend (ou cliente externo) chama:

`POST /v1/chat/completions`

ocorre o seguinte:

1. **Routing semântico**
   - O texto do utilizador é analisado pelo `semantic-router`.
   - O sistema escolhe uma rota (`code`, `reasoning`, `general`) e, por consequência, o tile/modelo.

2. **Leitura de configuração do tile**
   - O tile define, entre outros:
     - modelo base;
     - prompt de sistema;
     - TTL da cache;
     - threshold de similaridade;
     - regras de prewarm.

3. **Cache semântica**
   - A query atual é embebida em vetor.
   - Compara-se com embeddings já guardados para esse tile.
   - Se similaridade >= threshold, retorna resposta cacheada (**cache hit**).

4. **Geração no modelo (se cache miss)**
   - Chama-se Ollama (`/api/chat`) com o modelo do tile.
   - Resposta é agregada (modo não-stream) ou enviada progressivamente (stream).

5. **Persistência em cache**
   - A nova resposta e embedding são guardados com expiração (`ttl_seconds`).

6. **Trace técnico opcional**
   - Se `include_trace=true`, a API devolve métricas reais:
     - rota/tile/model;
     - cache hit/miss;
     - warm/cold;
     - tempos de routing/cache/generation em ms.

## 5. Tiles: o que são
Um **tile** é uma unidade de especialização declarativa (YAML) com:
- `model.base`
- `model.system_prompt`
- `routing.utterances`
- `cache.ttl_seconds`
- `cache.similarity_threshold`
- `scheduler.keep_warm_after`
- `scheduler.prewarm_on`

Isto permite ajustar comportamento sem alterar lógica core.

## 6. Interface web (estado atual)
Endpoint da interface:
- `GET /` (ex.: `http://127.0.0.1:8000/`)

A interface está focada em experimentação:
- Chat simples.
- **Execution Trace** visível.
- Badge por resposta com:
  - cache hit/miss,
  - tile,
  - route,
  - model.

## 7. Endpoints principais
- `GET /health`
  - Estado do serviço e tiles carregados.

- `GET /tiles`
  - Lista de tiles e estado warm.

- `POST /v1/chat/completions`
  - Compatível com formato de chat completion.
  - Campos úteis neste projeto:
    - `messages`
    - `stream`
    - `include_trace` (MVP específico)

## 8. Configuração (env)
As variáveis centrais incluem:
- `OLLAMA_BASE_URL` (preferida)
- `OLLAMA_HOST`, `OLLAMA_PORT` (fallback)
- `HTTP_TIMEOUT_SECONDS`
- `PREWARM_HTTP_TIMEOUT_SECONDS`
- `DEFAULT_TILE_NAME`
- `DEFAULT_TILE_TTL_SECONDS`
- `DEFAULT_CACHE_SIMILARITY_THRESHOLD`
- `EMBEDDING_MODEL_NAME`
- `APP_HOST`, `APP_PORT`

Arquivo de referência:
- `.env.example`

## 9. Pré-requisitos de execução
1. Ollama acessível (ex.: `http://127.0.0.1:11434`).
2. Modelos necessários disponíveis (ex.: `qwen3:4b`, `qwen2.5-coder:3b`).
3. Ambiente Python com dependências instaladas.

## 10. Testes e qualidade
A base já inclui testes automatizados com `pytest`, cobrindo:
- Configuração.
- Carregamento de tiles.
- API (`/health`, chat stream/non-stream, trace).
- Render básico da UI.

Comando:

```bash
pytest -q
```

## 11. O que foi melhorado nesta iteração
- Remoção de hardcodes críticos e centralização de config.
- Refatoração para arquitetura modular em `app/`.
- Criação de interface web de investigação.
- Adição de trace real de backend para observabilidade funcional.
- Testes automatizados para reduzir regressões.

## 12. Limitações atuais (esperadas num MVP)
- Foco em cenário local/single-node.
- Sem autenticação/controle de acesso.
- Sem histórico persistente multiutilizador no frontend.
- Sem pipeline de deploy/monitorização de produção.

## 13. Próximos passos naturais
1. Persistir histórico de sessões de chat na UI.
2. Exportar métricas do trace para ficheiro/telemetria.
3. Adicionar testes E2E de UI.
4. Definir estratégia de versionamento de tiles.
5. Endurecer tratamento de erros com códigos e payloads padronizados.

---
Se quiser, no próximo passo posso também gerar uma versão curta deste documento para README (sumário executivo) e manter este ficheiro como documentação técnica detalhada.
