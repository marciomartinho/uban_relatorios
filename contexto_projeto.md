# Contexto do Projeto - Sistema de Relatórios Orçamentários, Financeiros e Patrimoniais

## Visão Geral
Sistema web desenvolvido em Python/Flask para gerenciamento e geração de relatórios orçamentários, financeiros e patrimoniais. O sistema importa dados de planilhas Excel para um banco PostgreSQL e disponibiliza relatórios via interface web.

## Stack Tecnológica
- **Backend**: Python 3.x, Flask (com Blueprints)
- **Banco de Dados**: PostgreSQL 16.9
- **ORM**: SQLAlchemy
- **Frontend**: HTML, CSS (separado), JavaScript (separado)
- **ETL**: Pandas para leitura de Excel e carga no banco
- **Deploy**: Desenvolvimento local, futura implantação no Railway

## Status Atual do Desenvolvimento

### ✅ Concluído
1. **Estrutura do Projeto**: Criada com organização modular
2. **Ambiente Virtual**: Configurado com todas as dependências
3. **Conexão com Banco**: Módulo `database.py` implementado e testado
4. **Banco de Dados**: `relatorios_uban` criado no PostgreSQL
5. **Schemas**: Criados (public, receitas, despesas, dimensoes)
6. **Tabelas de Controle ETL**: 
   - `etl_control`: Controla última carga de cada tabela
   - `etl_log`: Registra histórico de todas as cargas
   - Triggers e índices criados para performance
7. **ETL ReceitaSaldo**: 
   - Módulo `etl_receita_saldo.py` implementado
   - Tabela `receitas.fato_receita_saldo` criada e populada
   - 11.998 registros carregados (Jan-Jun 2025)
   - Transformações aplicadas com sucesso
   - Sistema de carga incremental implementado
8. **ETL DespesaSaldo**:
   - Módulo `etl_despesa_saldo.py` implementado
   - Tabela `despesas.fato_despesa_saldo` criada e populada
   - 560.110 registros carregados (Jan-Jun 2025)
   - Parse de natureza despesa implementado
   - Coluna especial `cosubelemento` para contas de 40 chars
9. **Aplicação Flask**: 
   - Servidor web funcionando
   - Sistema de blueprints configurado
   - Templates base e home criados
10. **Interface Web - Consulta Saldo Receita**:
    - Página totalmente funcional
    - Filtros dinâmicos (Ano, Conta, UG)
    - Opção "Consolidado" para somar todas UGs
    - Tabela com colunas dinâmicas (17 ou 38 chars)
    - Filtros por coluna tipo Excel
    - Exportação para CSV
    - Formatação monetária brasileira
    - Design responsivo com Bootstrap
11. **Interface Web - Consulta Saldo Despesa**: ✅ NOVO!
    - Página totalmente funcional
    - Sistema de cache implementado para performance
    - Correção de bugs SQL realizada
    - Índices otimizados criados
    - Funciona com 560k+ registros sem travar

### 🚀 Sistema de Cache (NOVO!)
- **Tabela**: `public.cache_filtros_despesa`
- **Função**: Armazena valores únicos de anos, contas e UGs
- **Performance**: Reduz tempo de carregamento de minutos para milissegundos
- **Script**: `scripts/otimizar_despesas.py` para criar/atualizar

### ⏳ Próximas Etapas
- Implementar ETL para demais planilhas
- Desenvolver dashboards com gráficos
- Implementar relatórios PDF
- Sistema de autenticação

## 📚 GUIA DO USUÁRIO - Como Atualizar os Dados Mensalmente

### 🎯 O que você vai fazer todo mês
Todo mês você vai receber 2 arquivos Excel novos com os dados do mês. Você precisa adicionar esses dados no sistema. É como adicionar páginas novas em um livro que já existe.

### 📁 PASSO 1: Preparar os Arquivos

1. **Você vai receber 2 arquivos**:
   - `ReceitaSaldoJulho.xlsx` (ou Agosto, Setembro, etc.)
   - `DespesaSaldoJulho.xlsx` (ou Agosto, Setembro, etc.)

2. **Coloque na pasta certa**:
   - Copie esses arquivos para a pasta: `dados_brutos/fato/`
   - É a mesma pasta onde estão os arquivos antigos

### 💻 PASSO 2: Abrir o Terminal

1. Abra a pasta do projeto `relatorios_uban` no Windows
2. Clique com botão direito em área vazia
3. Escolha "Abrir no Terminal" ou "Abrir PowerShell aqui"

### 🔧 PASSO 3: Ativar o Sistema

No terminal, digite e aperte Enter:
```powershell
venv\Scripts\activate
```

**O que vai aparecer**: `(venv)` no início da linha

### 📊 PASSO 4: Adicionar RECEITAS

Digite e aperte Enter (substitua "Julho" pelo mês correto):
```powershell
python scripts/load_receita_saldo_incremental.py ReceitaSaldoJulho.xlsx
```

**O que vai acontecer**:
1. Vai mostrar os períodos encontrados no arquivo
2. Vai perguntar se quer continuar (digite `S` e Enter)
3. Vai processar (demora 1-2 minutos)
4. No final mostra "✅ Carga incremental concluída com sucesso!"

### 📈 PASSO 5: Adicionar DESPESAS

Digite e aperte Enter (substitua "Julho" pelo mês correto):
```powershell
python scripts/load_despesa_saldo_incremental.py DespesaSaldoJulho.xlsx
```

**O que vai acontecer**:
1. Mesma coisa que receitas
2. Mas demora mais (5-10 minutos) porque tem mais dados
3. No final mostra "✅ Carga incremental concluída com sucesso!"

### ⚡ PASSO 6: Atualizar o CACHE (MUITO IMPORTANTE!)

**Por que isso é importante?** O cache é como um índice de livro. Se você não atualizar, o sistema não vai mostrar os novos meses nos filtros!

Digite e aperte Enter:
```powershell
python scripts/otimizar_despesas.py
```

**O que vai acontecer**:
1. Vai recriar a lista de anos, contas e UGs
2. Demora 2-3 minutos
3. No final mostra "✨ OTIMIZAÇÃO CONCLUÍDA COM SUCESSO!"

### ✅ PASSO 7: Verificar se Funcionou

1. **Inicie o sistema**:
```powershell
python run.py
```

2. **Abra o navegador** em: http://localhost:5000

3. **Teste**:
   - Vá em "Consulta Saldo Receita" ou "Consulta Saldo Despesa"
   - Verifique se o novo mês aparece no filtro de Anos

### 📋 Ver Histórico de Importações

Para ver todas as importações já feitas:
```powershell
python scripts/consultar_etl_log.py
```

### 🆘 Se Der Erro

**"Arquivo não encontrado"**:
- Verifique se o nome do arquivo está correto
- Verifique se está na pasta `dados_brutos/fato/`

**"Período já existe"**:
- O sistema vai perguntar se quer sobrescrever
- Digite `S` se quiser substituir os dados

**"Erro de conexão"**:
- Verifique se está conectado na internet
- Verifique se o banco de dados está acessível

### 📝 Resumo Rápido (Cola no Post-it!)

```
TODO MÊS:
1. Copiar arquivos Excel para dados_brutos/fato/
2. Abrir PowerShell na pasta do projeto
3. venv\Scripts\activate
4. python scripts/load_receita_saldo_incremental.py ReceitaSaldoMES.xlsx
5. python scripts/load_despesa_saldo_incremental.py DespesaSaldoMES.xlsx
6. python scripts/otimizar_despesas.py
7. python run.py (para testar)
```

## Arquitetura do Sistema

### 1. Camada de Dados - CORAÇÃO DO SISTEMA 💗
O banco de dados PostgreSQL é o componente central do sistema, responsável por:
- **Armazenar** todos os dados importados das planilhas Excel
- **Processar** consultas complexas para geração de relatórios
- **Garantir** integridade e consistência dos dados
- **Controlar** o versionamento através de cargas incrementais

#### Estratégia de Carga de Dados
1. **Carga Inicial**: 
   - Dados de Janeiro a Junho (já existentes)
   - Apaga e recarrega toda a tabela
   - Registra no `etl_control`

2. **Cargas Incrementais**:
   - Dados mensais (Julho, Agosto, etc.)
   - Apenas adiciona novos registros
   - Valida duplicatas por período
   - Mantém histórico em `etl_log`

#### Tabelas de Controle ETL
```sql
etl_control: Última carga de cada tabela
- tabela_nome: Nome da tabela fato/dimensão
- ultimo_periodo_carregado: Ex: "2025-07"
- tipo_ultima_carga: "inicial" ou "incremental"
- total_registros_carregados: Contador acumulado

etl_log: Histórico detalhado de todas as cargas
- Registra cada execução de ETL
- Permite rastreabilidade completa
- Identifica erros e reprocessamentos

cache_filtros_despesa: Cache para performance (NOVO!)
- tipo_filtro: 'ano', 'conta' ou 'ug'
- valor: Valor único do filtro
- descricao: Descrição (para UGs)
- ordem: Para ordenação
```

### 2. Estrutura de Diretórios
```
relatorios_uban/
├── venv/                    # Ambiente virtual Python
├── dados_brutos/           # Planilhas Excel fonte
│   ├── dimensao/          # Dados dimensionais
│   └── fato/              # Dados de fatos
├── app/                    # Aplicação Flask
│   ├── __init__.py        # Inicialização e configuração Flask
│   ├── routes/            # Blueprints de rotas
│   │   ├── main.py        # Rotas principais
│   │   ├── saldo_receita.py  # Página de receitas
│   │   └── saldo_despesa.py  # Página de despesas
│   ├── static/            # Assets estáticos
│   │   ├── css/          # Arquivos CSS
│   │   └── js/           # Arquivos JavaScript
│   ├── templates/         # Templates HTML (Jinja2)
│   │   ├── base.html     # Template base
│   │   └── saldo_receita/ # Templates de receita
│   │   └── saldo_despesa/ # Templates de despesa
│   └── modules/           # Módulos reutilizáveis
│       ├── database.py    # Conexão e helpers do banco
│       ├── etl_receita_saldo.py  # ETL de receitas
│       └── etl_despesa_saldo.py  # ETL de despesas
├── models/                # Modelos SQLAlchemy (ORM)
├── config.py             # Configurações da aplicação
├── .env                  # Variáveis de ambiente (credenciais)
├── run.py                # Entry point da aplicação
├── scripts/              # Scripts de manutenção e setup
│   ├── create_etl_tables.py     # Criação das tabelas de controle
│   ├── create_filter_cache.py   # Criação do cache de filtros
│   ├── otimizar_despesas.py     # Otimização completa (cache + índices)
│   ├── load_receita_saldo_incremental.py # Carga incremental receitas
│   └── load_despesa_saldo_incremental.py # Carga incremental despesas
```

### 3. Configuração do Banco de Dados
- **Host**: 31.97.128.109:5432
- **Versão**: PostgreSQL 16.9 (Ubuntu)
- **Banco criado**: `relatorios_uban` ✅
- **Conexão**: SQLAlchemy com psycopg2
- **Tabelas de controle**: `etl_control` e `etl_log` ✅
- **Cache**: `cache_filtros_despesa` ✅

## Scripts de Manutenção

### Scripts Principais
```
# Otimização e Cache
otimizar_despesas.py       # Cria cache e índices (executar após cada carga)

# Carga incremental (usar mensalmente)
load_receita_saldo_incremental.py # Adiciona novos meses de receita
load_despesa_saldo_incremental.py # Adiciona novos meses de despesa

# Consultas e verificações
consultar_etl_log.py       # Ver histórico de cargas (A CRIAR)
```

### Tabelas no Banco
```sql
-- Schemas
public                     -- Tabelas de sistema e cache
receitas                   -- Dados de receitas
despesas                   -- Dados de despesas
dimensoes                  -- Futuras tabelas dimensão

-- Tabelas de Controle (schema public)
etl_control                -- Controle de cargas por tabela
etl_log                    -- Log detalhado de todas as cargas
cache_filtros_despesa      -- Cache para performance (NOVO!)

-- Tabelas Fato
receitas.fato_receita_saldo  -- 11.998 registros (Jan-Jun 2025)
despesas.fato_despesa_saldo  -- 560.110 registros (Jan-Jun 2025)
```

## Comandos Úteis

### Ativar ambiente virtual
```bash
# Windows PowerShell
venv\Scripts\activate
```

### Rotina Mensal de Atualização
```bash
# 1. Adicionar receitas do mês
python scripts/load_receita_saldo_incremental.py ReceitaSaldoMES.xlsx

# 2. Adicionar despesas do mês
python scripts/load_despesa_saldo_incremental.py DespesaSaldoMES.xlsx

# 3. Atualizar cache (IMPORTANTE!)
python scripts/otimizar_despesas.py

# 4. Verificar cargas
python scripts/consultar_etl_log.py

# 5. Testar sistema
python run.py
```

### Manutenção e Correções
```bash
# Recriar cache do zero
python scripts/create_filter_cache.py

# Corrigir tabelas de controle
python scripts/fix_etl_control.py

# Ver estrutura de arquivo Excel
python scripts/inspect_despesa_saldo.py
```

## Observações Importantes
- O desenvolvedor é iniciante, então o código deve ser claro e bem comentado
- Preferência por explicações passo a passo
- Sistema inicialmente local, depois será deployado no Railway
- Dados sensíveis (financeiros/patrimoniais) - atenção à segurança
- **SEMPRE atualizar o cache após cargas incrementais!**