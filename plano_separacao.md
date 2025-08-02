# Plano de Separação Web/Local - Sistema de Relatórios

## 📋 Resumo Executivo

### Decisão Arquitetural
Separar o sistema em duas partes:
1. **WEB (Railway → VPS PostgreSQL)**: Apenas tabelas de SALDO para consultas gerenciais
2. **LOCAL (DuckDB/SQLite)**: Tabelas de LANÇAMENTO para auditoria interna e conferências

### Arquitetura Final
```
VPS (31.97.128.109):
└── PostgreSQL
    ├── receitas.fato_receita_saldo (12k registros/mês)
    ├── despesas.fato_despesa_saldo (93k registros/mês)
    └── tabelas de controle e cache

Railway:
└── Aplicação Flask (apenas código Python)
    └── Conecta no PostgreSQL da VPS para saldos

Máquina Local:
├── DuckDB/SQLite (lançamentos)
│   ├── receitas.fato_receita_lancamento (27k registros/mês)
│   └── despesas.fato_despesa_lancamento (170k registros/mês)
└── Scripts Python para:
    ├── Conectar na VPS (buscar saldos)
    └── Conectar local (buscar lançamentos)
```

### Motivação
- Tabelas de lançamento têm ~1M registros (crescendo ~200k/mês)
- Usuários web NUNCA precisam ver lançamentos detalhados
- Lançamentos são exclusivamente para auditoria interna
- Performance e custo no Railway serão drasticamente melhores
- Conferências saldo vs lançamento serão feitas localmente

## 🎯 O que NÃO muda (permanece igual)

### Tabelas que ficam na VPS PostgreSQL:
- `receitas.fato_receita_saldo` ✅ Não mexer
- `despesas.fato_despesa_saldo` ✅ Não mexer
- `etl_control` ✅ Não mexer
- `etl_log` ✅ Não mexer (registrar apenas ETLs de saldo)
- `cache_filtros_despesa` ✅ Não mexer

### Páginas/Códigos que NÃO mudam:
- ✅ `app/routes/saldo_receita.py` - Continua igual
- ✅ `app/routes/saldo_despesa.py` - Continua igual
- ✅ `app/templates/saldo_receita/*` - Continua igual
- ✅ `app/templates/saldo_despesa/*` - Continua igual
- ✅ Todos os ETLs de SALDO - Continuam iguais
- ✅ Scripts de carga incremental de SALDO - Continuam iguais

## 🔄 O que MUDA

### 1. Remover da VPS PostgreSQL:
- ❌ Tabela `receitas.fato_receita_lancamento` (migrar para local)
- ❌ Tabela `despesas.fato_despesa_lancamento` (migrar para local)
- ❌ Registros de ETL de lançamentos no `etl_control` e `etl_log`

### 2. Remover da Aplicação Web:
- ❌ Página "Detalha Conta Contábil - Receita"
- ❌ Página "Detalha Conta Contábil - Despesa" (não implementada)

### 3. Arquivos para REMOVER/DESATIVAR:
```
app/routes/detalha_receita.py         # Remover
app/templates/detalha_receita/*       # Remover pasta toda
app/static/css/detalha_receita.css    # Remover
app/static/js/detalha_receita.js      # Remover
```

### 4. Modificar `app/templates/base.html`:
```html
<!-- REMOVER o menu dropdown "Detalha Conta Contábil" -->
<!-- Manter apenas:
     - Home
     - Consulta Saldo Receita
     - Consulta Saldo Despesa
-->
```

### 5. Modificar `app/__init__.py`:
```python
# REMOVER estas linhas:
# from app.routes.detalha_receita import detalha_receita
# app.register_blueprint(detalha_receita, url_prefix='/detalha-receita')
```

### 6. Scripts de ETL para MOVER para sistema local:
```
# Mover para pasta relatorios_auditoria_local/scripts/
scripts/load_receita_lancamento.py
scripts/load_receita_lancamento_incremental.py
scripts/load_despesa_lancamento.py
scripts/load_despesa_lancamento_incremental.py
scripts/inspect_receita_lancamento.py
scripts/inspect_despesa_lancamento.py
```

## 🏗️ Nova Estrutura LOCAL

### Sistema de Auditoria Local:
```
relatorios_auditoria_local/
├── config/
│   └── database.py          # Conexões VPS e local
├── data/
│   ├── lancamentos.duckdb   # Banco DuckDB com lançamentos
│   └── excel_brutos/        # Excel mensais de lançamentos
│       ├── 2024/
│       └── 2025/
├── scripts/
│   ├── setup/
│   │   ├── 01_criar_banco_duckdb.py      # Setup inicial
│   │   └── 02_migrar_dados_historicos.py # Importar Jan/2024-Jun/2025
│   ├── etl/
│   │   ├── importar_receita_lancamento.py
│   │   └── importar_despesa_lancamento.py
│   └── relatorios/
│       ├── conferencia_saldo_lancamento.py # Cruza VPS + local
│       ├── auditoria_documentos.py
│       └── analise_divergencias.py
├── relatorios_gerados/
│   └── [Excel/PDF dos relatórios]
├── requirements.txt         # pandas, duckdb, sqlalchemy, psycopg2
└── README.md               # Documentação do sistema local
```

## 📝 Implementação Passo a Passo

### FASE 0 - Preparação (1 dia)
1. [ ] Fazer backup completo do PostgreSQL VPS
2. [ ] Exportar dados de lançamentos existentes para CSV/Excel
3. [ ] Documentar estado atual do sistema
4. [ ] Comunicar usuários sobre mudanças

### FASE 1 - Criar Sistema Local (2 dias)
1. [ ] Criar estrutura de pastas local
2. [ ] Instalar DuckDB e dependências
3. [ ] Criar script de setup do banco DuckDB
4. [ ] Importar dados históricos (Jan/2024 - Jun/2025)
5. [ ] Testar queries básicas
6. [ ] Criar script de conexão com VPS

### FASE 2 - Limpar Sistema Web (1 dia)
1. [ ] Remover arquivos de rotas de lançamento
2. [ ] Remover templates de lançamento
3. [ ] Atualizar menu no base.html
4. [ ] Atualizar __init__.py
5. [ ] Testar sistema web (deve funcionar apenas com saldos)
6. [ ] Deploy no Railway

### FASE 3 - Implementar Relatórios Cruzados (2 dias)
1. [ ] Script de conferência saldo vs lançamento
2. [ ] Script de análise de divergências
3. [ ] Templates de relatórios em Excel
4. [ ] Testes com dados reais
5. [ ] Documentação de uso

## 💻 Configuração do Sistema Local

### `config/database.py`:
```python
from sqlalchemy import create_engine
import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

# Conexão VPS PostgreSQL (saldos)
def get_vps_engine():
    """Conecta no PostgreSQL da VPS para buscar saldos"""
    return create_engine(os.getenv('VPS_DATABASE_URL'))
    

# Conexão DuckDB local (lançamentos)
def get_local_db():
    """Conecta no DuckDB local com lançamentos"""
    return duckdb.connect('data/lancamentos.duckdb')
```

### Exemplo de Relatório Cruzado:
```python
# scripts/relatorios/conferencia_saldo_lancamento.py
import pandas as pd
from config.database import get_vps_engine, get_local_db

def conferir_periodo(ano, mes):
    # 1. Buscar saldos da VPS
    engine_vps = get_vps_engine()
    df_saldos = pd.read_sql(f"""
        SELECT cocontacontabil, coug, vadebito, vacredito, 
               saldo_inicial, saldo_final
        FROM despesas.fato_despesa_saldo
        WHERE coexercicio = {ano} AND inmes = {mes}
    """, engine_vps)
    
    # 2. Buscar lançamentos agregados local
    conn_local = get_local_db()
    df_lancamentos = conn_local.execute(f"""
        SELECT cocontacontabil, coug,
               SUM(CASE WHEN tipo_lancamento = 'DEBITO' 
                   THEN valancamento ELSE 0 END) as total_debitos,
               SUM(CASE WHEN tipo_lancamento = 'CREDITO' 
                   THEN valancamento ELSE 0 END) as total_creditos
        FROM despesa_lancamento
        WHERE coexercicio = {ano} AND inmes = {mes}
        GROUP BY cocontacontabil, coug
    """).df()
    
    # 3. Cruzar e identificar divergências
    df_conferencia = pd.merge(df_saldos, df_lancamentos, 
                             on=['cocontacontabil', 'coug'], 
                             how='outer')
    
    return df_conferencia
```

## 📅 Processo Mensal Atualizado

### Para VPS/Web (continua igual):
```bash
# Na pasta relatorios_uban
python scripts/load_receita_saldo_incremental.py ReceitaSaldoJulho.xlsx
python scripts/load_despesa_saldo_incremental.py DespesaSaldoJulho.xlsx
python scripts/otimizar_despesas.py
```

### Para Local (novo processo):
```bash
# Na pasta relatorios_auditoria_local
python scripts/etl/importar_receita_lancamento.py ReceitaLancamentoJulho.xlsx
python scripts/etl/importar_despesa_lancamento.py DespesaLancamentoJulho.xlsx

# Rodar conferências
python scripts/relatorios/conferencia_saldo_lancamento.py --mes 7
```

## 🎯 Resultado Final

### Sistema Web (Railway → VPS):
- ✅ Apenas consultas de saldo
- ✅ Performance excelente (~200k registros totais)
- ✅ Custo mínimo no Railway (só aplicação)
- ✅ Ideal para gestão/dashboards
- ✅ Acesso multi-usuário

### Sistema Local:
- ✅ Todos os lançamentos detalhados (~2M registros)
- ✅ Conferências saldo vs lançamento
- ✅ Análises complexas de auditoria
- ✅ Processamento local (sem latência)
- ✅ Dados sensíveis protegidos

### Integração VPS + Local:
- ✅ Python conecta em ambos simultaneamente
- ✅ Relatórios cruzados funcionam perfeitamente
- ✅ Saldos sempre atualizados (fonte única)
- ✅ Flexibilidade total para análises

## ⚠️ Pontos Críticos de Atenção

1. **Credenciais VPS**: Guardar com segurança no `.env` local
2. **Backup dos lançamentos**: Antes de remover da VPS
3. **Validação**: Conferir se todos os dados migraram corretamente
4. **Performance DuckDB**: Testar com volume real antes de migrar
5. **Documentação**: Criar guias separados para cada sistema

## 📊 Métricas de Sucesso

- **Redução de 80%** no tamanho do banco VPS
- **Queries de saldo 10x mais rápidas** (menos dados)
- **Custo Railway reduzido** (menos processamento)
- **Conferências locais em segundos** (sem latência de rede)
- **Zero impacto** para usuários web

## 🚀 Benefícios da Arquitetura

1. **Separação de Responsabilidades**:
   - Web: Visualização gerencial
   - Local: Auditoria e conferência

2. **Otimização de Recursos**:
   - VPS: Apenas dados essenciais
   - Local: Processamento pesado

3. **Segurança**:
   - Lançamentos detalhados não expostos na web
   - Controle total sobre dados sensíveis

4. **Escalabilidade**:
   - Web cresce devagar (só saldos)
   - Local suporta milhões de registros

5. **Manutenibilidade**:
   - Sistemas independentes
   - Atualizações sem impacto cruzado

## 📝 Notas de Implementação

- DuckDB é recomendado sobre SQLite para análises
- Manter scripts ETL originais como referência
- Criar testes de validação pós-migração
- Considerar particionamento no DuckDB por ano
- Documentar queries de conferência mais usadas