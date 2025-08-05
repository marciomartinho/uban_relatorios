# Contexto do Projeto - Sistema de Relatórios Orçamentários UBAN

## 📌 Visão Geral
Sistema web desenvolvido em Python/Flask para gerenciamento e geração de relatórios orçamentários, financeiros e patrimoniais. Utiliza arquitetura híbrida com PostgreSQL (VPS) para dados de saldo e DuckDB (local) para dados de lançamento.

## 🛠️ Stack Tecnológica
- **Backend**: Python 3.x, Flask (com Blueprints)
- **Bancos de Dados**:
  - PostgreSQL 16.9 (VPS) - Dados de Saldo (menor volume)
  - DuckDB (Local) - Dados de Lançamento (1.5M+ registros)
- **ORM**: SQLAlchemy (PostgreSQL)
- **Frontend**: HTML, CSS, JavaScript (jQuery, DataTables, Bootstrap)
- **ETL**: Pandas + DuckDB para processamento eficiente
- **Deploy**: Desenvolvimento local

## 🦆 Por que DuckDB?
- **Performance**: 10-100x mais rápido que PostgreSQL para análises
- **Simplicidade**: Apenas 1 arquivo .duckdb
- **Economia**: Não consome recursos da VPS
- **Autonomia**: Funciona offline
- **Escalabilidade**: Suporta bilhões de registros

## 🏗️ Arquitetura do Sistema

```
┌─────────────────┐         ┌──────────────────┐         ┌────────────────┐
│   PostgreSQL    │         │     DuckDB       │         │   Dimensões    │
│     (VPS)       │         │    (Local)       │         │   (DuckDB)     │
├─────────────────┤         ├──────────────────┤         ├────────────────┤
│ • Saldo Receita │         │ • Receita Lanç. │         │ • 20 tabelas   │
│ • Saldo Despesa │         │ • Despesa Lanç. │         │ • dim_*        │
│ • ETL Control   │         │ • 1.5M+ registros│         │ • Referências  │
└─────────────────┘         └──────────────────┘         └────────────────┘
```

## 📊 Status Atual (Agosto 2025)

### ✅ Concluído
- Sistema web funcionando com todas as 4 telas principais
- Migração completa para DuckDB (1.5M+ registros)
- ETL automatizado para carga mensal
- Sistema de cache para otimização (PostgreSQL)
- **NOVO**: Tabelas dimensão carregadas no DuckDB
- **NOVO**: Correção do campo `intipoadm` removido da despesa_saldo
- Scripts de visualização e conferência

### 🚧 Em Andamento
- Otimização de queries DuckDB
- Dashboards com dados combinados

### 📋 Próximas Etapas
- Views materializadas no DuckDB
- Sistema de autenticação
- Deploy no Railway

## 🗂️ Estrutura de Diretórios

```
relatorios_uban/
├── venv/                    # Ambiente virtual Python
├── dados_brutos/           
│   ├── dimensao/           # 20 arquivos Excel de dimensões
│   └── fato/              
│       ├── db_local/      
│       │   └── uban.duckdb # Banco único (fatos + dimensões)
│       └── *.xlsx          # Arquivos Excel mensais
├── app/                    
│   ├── routes/             # Blueprints Flask
│   └── modules/            # ETLs e conexões
├── scripts/                # Scripts numerados (01-08 + extras)
└── templates/              # HTML das telas
```

## 📚 GUIA DO USUÁRIO - Rotina Mensal

### 🎯 Carga Mensal Unificada
Todo mês você recebe 4 arquivos Excel. Use o script unificado:

```bash
# Ativar ambiente
venv\Scripts\activate

# Carga completa do mês
python scripts/carga_mensal_duckdb.py Agosto

# Conferir resultados
python scripts/relatorio_conferencia_duckdb.py
```

### 📊 Scripts Disponíveis

#### Carga Individual:
- `01_load_despesa_saldo.py` - Despesa Saldo (com opção --recriar)
- `03_load_despesa_lancamento.py` - Despesa Lançamento
- `05_load_receita_saldo.py` - Receita Saldo  
- `07_load_receita_lancamento.py` - Receita Lançamento

#### Visualização:
- `02_visualizar_tabela_despesa_saldo.py`
- `04_visualizar_tabela_despesa_lancamento.py`
- `06_visualizar_tabela_receita_saldo.py`
- `08_visualizar_tabela_receita_lancamento.py`

#### Utilitários:
- `carga_mensal_duckdb.py` - Carga unificada (recomendado!)
- `carga_dimensoes_duckdb.py` - Carrega tabelas dimensão
- `relatorio_conferencia_duckdb.py` - Relatório de conferência
- `verificar_integridade_duckdb.py` - Verifica integridade referencial
- `consultar_lancamentos_duckdb.py` - Consultas rápidas
- `documentar_duckdb.py` - Gera documentação da estrutura

## 🔧 Configuração Inicial

### 1. Ambiente Virtual
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Variáveis de Ambiente (.env)
```
DB_HOST=31.97.128.109
DB_PORT=5432
DB_NAME=relatorios_uban
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```

### 3. Primeira Execução
```bash
# Carregar dimensões
python scripts/carga_dimensoes_duckdb.py

# Carregar dados históricos
python scripts/carga_mensal_duckdb.py Janeiro
# ... repetir para cada mês

# Iniciar aplicação
python run.py
```

## 📈 Performance
- Consulta típica (1000 registros): 0.1-0.3 segundos (DuckDB)
- Agregação completa (1.5M registros): 1-3 segundos (DuckDB)
- Carga de 100k registros: 10-30 segundos (DuckDB)

## 🆘 Troubleshooting

### "Database is locked" (DuckDB)
- Feche todas as conexões Python
- Reinicie o kernel/terminal

### "Arquivo muito grande"
- Execute `VACUUM` periodicamente no DuckDB
- Considere particionar por ano

### "Campo não encontrado"
- Verifique `contexto_tabelas.md` para estrutura correta
- Alguns campos foram removidos (ex: intipoadm)

## 📝 Documentação Adicional
- **Estrutura das Tabelas**: Ver arquivo `contexto_tabelas.md`
- **Relacionamentos**: Ver output de `verificar_integridade_duckdb.py`
- **Estatísticas**: Ver output de `relatorio_conferencia_duckdb.py`

## 🚀 Comandos Rápidos

```bash
# Ativar ambiente
venv\Scripts\activate

# Rodar aplicação
python run.py

# Carga mensal completa
python scripts/carga_mensal_duckdb.py MES

# Verificar integridade
python scripts/verificar_integridade_duckdb.py

# Consultas rápidas
python scripts/consultar_lancamentos_duckdb.py

# Gerar documentação
python scripts/documentar_duckdb.py
```

## 📌 Observações Importantes
- **Backup**: Copie o arquivo `uban.duckdb` semanalmente
- **Concorrência**: DuckDB não suporta escrita simultânea
- **Excel**: SEMPRE feche o Excel antes de processar arquivos
- **Memória**: Para arquivos grandes, feche outros programas

---
*Última atualização: Agosto 2025*