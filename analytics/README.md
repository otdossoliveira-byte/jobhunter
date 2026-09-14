# analytics/ — Relatórios em SQL puro

Módulo de análise de dados do JobHunter, escrito com `sqlite3` (sem ORM),
para consultar diretamente o banco que o robô já popula.

## O que demonstra

- `SELECT`, `WHERE`, `GROUP BY`, `ORDER BY`, `LIMIT`
- `JOIN` (LEFT JOIN) entre `vagas` e `perfis_busca`
- Filtro por data com função nativa do SQLite (`date('now', ...)`)
- Parâmetros preparados (evita SQL injection)

## Como rodar

```bash
python main.py            # roda o robô ao menos uma vez, pra criar/popular o banco
python analytics/relatorios.py
```

## Relatórios gerados

- Total de vagas no banco
- Vagas por cidade
- Vagas por fonte (site de origem)
- Vagas por status
- Top empresas que mais aparecem
- Desempenho por perfil de busca (via JOIN)
- Vagas encontradas nos últimos N dias
