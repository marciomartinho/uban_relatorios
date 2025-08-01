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
9. **ETL ReceitaLancamento**: ✅ NOVO!
   - Módulo `etl_receita_lancamento.py` implementado
   - Tabela `receitas.fato_receita_lancamento` criada e populada
   - 490.122 registros carregados (2024-01 a 2025-06)
   - Parse de COCONTACORRENTE (17, 38 e 40 chars)
   - Campo `tipo_lancamento` (DEBITO/CREDITO)
   - Sistema de carga incremental implementado
10. **Aplicação Flask**: 
    - Servidor web funcionando
    - Sistema de blueprints configurado
    - Templates base e home criados
11. **Interface Web - Consulta Saldo Receita**:
    - Página totalmente funcional
    - Filtros dinâmicos (Ano, Conta, UG)
    - Opção "Consolidado" para somar todas UGs
    - Tabela com colunas dinâmicas (17 ou 38 chars)
    - Filtros por coluna tipo Excel
    - Exportação para CSV
    - Formatação monetária brasileira
    - Design responsivo com Bootstrap
12. **Interface Web - Consulta Saldo Despesa**: ✅ NOVO!
    - Página totalmente funcional
    - Sistema de cache implementado para performance
    - Correção de bugs SQL realizada
    - Índices otimizados criados
    - Funciona com 560k+ registros sem travar
    - Ordenação por mês (Janeiro a Dezembro)
    - Esfera mostra número do banco (não texto)

### 🚀 Sistema de Cache (NOVO!)
- **Tabela**: `public.cache_filtros_despesa`
- **Função**: Armazena valores únicos de anos, contas e UGs
- **Performance**: Reduz tempo de carregamento de minutos para milissegundos
- **Script**: `scripts/otimizar_despesas.py` para criar/atualizar

### ⏳ Próximas Etapas
- Implementar ETL para DespesaLancamento
- Desenvolver dashboards com gráficos
- Implementar relatórios PDF
- Sistema de autenticação
- Criar páginas de consulta para lançamentos

## 📚 GUIA DO USUÁRIO - Como Atualizar os Dados Mensalmente

### 🎯 O que você vai fazer todo mês
Todo mês você vai receber 4 arquivos Excel novos com os dados do mês:
- ReceitaSaldoMês.xlsx
- DespesaSaldoMês.xlsx
- ReceitaLancamentoMês.xlsx
- DespesaLancamentoMês.xlsx (futuro)

Você precisa adicionar esses dados no sistema. É como adicionar páginas novas em um livro que já existe.

### 📁 PASSO 1: Preparar os Arquivos

1. **Você vai receber 4 arquivos** (exemplo para Julho):
   - `ReceitaSaldoJulho.xlsx`
   - `DespesaSaldoJulho.xlsx`
   - `ReceitaLancamentoJulho.xlsx`
   - `DespesaLancamentoJulho.xlsx`

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

### 📊 PASSO 4: Adicionar RECEITA SALDO

Digite e aperte Enter (substitua "Julho" pelo mês correto):
```powershell
python scripts/load_receita_saldo_incremental.py ReceitaSaldoJulho.xlsx
```

**O que vai acontecer**:
1. Vai mostrar os períodos encontrados no arquivo
2. Vai perguntar se quer continuar (digite `S` e Enter)
3. Vai processar (demora 1-2 minutos)
4. No final mostra "✅ Carga incremental concluída com sucesso!"

### 📈 PASSO 5: Adicionar DESPESA SALDO

Digite e aperte Enter (substitua "Julho" pelo mês correto):
```powershell
python scripts/load_despesa_saldo_incremental.py DespesaSaldoJulho.xlsx
```

**O que vai acontecer**:
1. Mesma coisa que receitas
2. Mas demora mais (5-10 minutos) porque tem mais dados
3. No final mostra "✅ Carga incremental concluída com sucesso!"

### 📋 PASSO 6: Adicionar RECEITA LANÇAMENTO

Digite e aperte Enter (substitua "Julho" pelo mês correto):
```powershell
python scripts/load_receita_lancamento_incremental.py ReceitaLancamentoJulho.xlsx
```

**O que vai acontecer**:
1. Similar aos anteriores
2. Demora uns 5-8 minutos (quase 500 mil registros)
3. No final mostra "✅ Carga incremental concluída com sucesso!"

### ⚡ PASSO 7: Atualizar o CACHE (MUITO IMPORTANTE!)

**Por que isso é importante?** O cache é como um índice de livro. Se você não atualizar, o sistema não vai mostrar os novos meses nos filtros!

Digite e aperte Enter:
```powershell
python scripts/otimizar_despesas.py
```

**O que vai acontecer**:
1. Vai recriar a lista de anos, contas e UGs
2. Demora 2-3 minutos
3. No final mostra "✨ OTIMIZAÇÃO CONCLUÍDA COM SUCESSO!"

### ✅ PASSO 8: Verificar se Funcionou

1. **Inicie o sistema**:
```powershell
python run.py
```

2. **Abra o navegador** em: http://localhost:5000

3. **Teste**:
   - Vá em "Consulta Saldo Receita" ou "Consulta Saldo Despesa"
   - Verifique se o novo mês aparece no filtro de Anos

### 📋 Ver Histórico de Importações

Para ver todas as importações já feitas, crie e execute:
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
6. python scripts/load_receita_lancamento_incremental.py ReceitaLancamentoMES.xlsx
7. python scripts/otimizar_despesas.py
8. python run.py (para testar)
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
   - Dados de Janeiro a Junho 2025 (ou período inicial disponível)
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
│       ├── etl_receita_saldo.py      # ETL de receitas saldo
│       ├── etl_despesa_saldo.py      # ETL de despesas saldo
│       └── etl_receita_lancamento.py # ETL de receitas lançamento
├── models/                # Modelos SQLAlchemy (ORM)
├── config.py             # Configurações da aplicação
├── .env                  # Variáveis de ambiente (credenciais)
├── run.py                # Entry point da aplicação
├── scripts/              # Scripts de manutenção e setup
│   ├── load_receita_saldo_incremental.py     # Carga incremental receitas saldo
│   ├── load_despesa_saldo_incremental.py     # Carga incremental despesas saldo
│   ├── load_receita_lancamento.py            # Carga inicial receitas lançamento
│   ├── load_receita_lancamento_incremental.py # Carga incremental receitas lançamento
│   ├── otimizar_despesas.py                  # Otimização completa (cache + índices)
│   └── optimize_despesa_indexes.py           # Criar índices (opcional)
```

### 3. Configuração do Banco de Dados
- **Host**: 31.97.128.109:5432
- **Versão**: PostgreSQL 16.9 (Ubuntu)
- **Banco criado**: `relatorios_uban` ✅
- **Conexão**: SQLAlchemy com psycopg2
- **Tabelas de controle**: `etl_control` e `etl_log` ✅
- **Cache**: `cache_filtros_despesa` ✅

## ETL ReceitaSaldo - Detalhamento

### Estrutura da Tabela
A tabela `receitas.fato_receita_saldo` possui:
- **Colunas originais**: Dados diretos do Excel
- **Colunas calculadas**: `saldo_contabil_receita` baseado no primeiro dígito de `cocontacontabil`
- **Colunas derivadas**: Parse de `cocontacorrente` baseado no tamanho (17 ou 38 chars)

### Transformações Aplicadas
1. **Saldo Contábil**:
   - Se `cocontacontabil` começa com 5: `saldo = vadebito - vacredito`
   - Se `cocontacontabil` começa com 6: `saldo = vacredito - vadebito`

2. **Parse de COCONTACORRENTE (17 chars)**:
   - `coclasseorc`: chars 1-8
   - `cofonte`: chars 9-18
   - `cocategoriareceita`: char 1
   - `cofontereceita`: chars 1-2
   - `cosubfontereceita`: chars 1-3
   - `corubrica`: chars 1-4
   - `coalinea`: chars 1-6

3. **Parse de COCONTACORRENTE (38 chars)**:
   - `inesfera`: char 1 (esfera do governo)
   - `couo`: chars 2-6 (unidade orçamentária)
   - `cofuncao`: chars 7-8 (função)
   - `cosubfuncao`: chars 9-11 (subfunção)
   - `coprograma`: chars 12-15 (programa)
   - `coprojeto`: chars 16-19 (projeto/atividade)
   - `cosubtitulo`: chars 20-23 (subtítulo)
   - `cofonte`: chars 24-32 (fonte - unificado com receitas)
   - `conatureza`: chars 33-38 (natureza da despesa)
   - `incategoria`: char 33 (categoria econômica)
   - `cogrupo`: char 34 (grupo de despesa)
   - `comodalidade`: chars 35-36 (modalidade)
   - `coelemento`: chars 37-38 (elemento de despesa)

## ETL DespesaSaldo - Detalhamento

### Estrutura da Tabela
A tabela `despesas.fato_despesa_saldo` possui estrutura similar à ReceitaSaldo, com adição de:
- **Parse de CONATUREZA**: Extração de grupo, modalidade e elemento
- **Campo especial**: `cosubelemento` para contas de 40 caracteres (chars 39-40)

## ETL ReceitaLancamento - Detalhamento

### Estrutura da Tabela
A tabela `receitas.fato_receita_lancamento` possui:
- **490.122 registros** carregados
- **Período**: Janeiro 2024 a Junho 2025
- **Diferencial**: São lançamentos individuais, não saldos
- **Campo adicional**: `tipo_lancamento` (DEBITO/CREDITO) baseado em INDEBITOCREDITO
- **Documentos**: Campo NUDOCUMENTO identifica cada lançamento
- **Parse completo**: Suporta contas de 17, 38 e 40 caracteres

## Scripts de Manutenção

### Scripts Principais Ativos
```
# Otimização e Cache
otimizar_despesas.py              # Cria cache e índices (executar após cada carga)

# Cargas incrementais mensais
load_receita_saldo_incremental.py        # Adiciona novos meses de receita saldo
load_despesa_saldo_incremental.py        # Adiciona novos meses de despesa saldo
load_receita_lancamento_incremental.py   # Adiciona novos meses de receita lançamento

# Cargas iniciais (se precisar recarregar)
load_receita_lancamento.py        # Carga inicial de receita lançamento

# Manutenção opcional
optimize_despesa_indexes.py       # Criar índices se necessário
```

### Scripts Removidos (já executados)
- ~~create_schemas.py~~ - Schemas já criados
- ~~create_etl_tables.py~~ - Tabelas ETL já criadas
- ~~fix_etl_control.py~~ - Correções já aplicadas
- ~~load_receita_saldo.py~~ - Carga inicial já feita
- ~~load_despesa_saldo.py~~ - Carga inicial já feita

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
cache_filtros_despesa      -- Cache para performance

-- Tabelas Fato
receitas.fato_receita_saldo       -- 11.998 registros (Jan-Jun 2025)
receitas.fato_receita_lancamento  -- 490.122 registros (Jan/2024-Jun/2025)
despesas.fato_despesa_saldo       -- 560.110 registros (Jan-Jun 2025)
```

## Comandos Úteis

### Ativar ambiente virtual
```bash
# Windows PowerShell
venv\Scripts\activate
```

### Rotina Mensal de Atualização
```bash
# 1. Adicionar receitas saldo do mês
python scripts/load_receita_saldo_incremental.py ReceitaSaldoMES.xlsx

# 2. Adicionar despesas saldo do mês
python scripts/load_despesa_saldo_incremental.py DespesaSaldoMES.xlsx

# 3. Adicionar receitas lançamento do mês
python scripts/load_receita_lancamento_incremental.py ReceitaLancamentoMES.xlsx

# 4. Atualizar cache (IMPORTANTE!)
python scripts/otimizar_despesas.py

# 5. Testar sistema
python run.py
```

### Manutenção e Correções
```bash
# Ver estrutura de arquivo Excel novo
python scripts/inspect_receita_lancamento.py

# Recriar índices se necessário
python scripts/optimize_despesa_indexes.py
```

## Próximos Passos Recomendados

1. **Implementar ETL para DespesaLancamento**:
   - Criar `etl_despesa_lancamento.py`
   - Seguir padrão do ReceitaLancamento
   - Volume esperado: ~1 milhão de registros

2. **Criar páginas de consulta para lançamentos**:
   - Interface para ReceitaLancamento
   - Interface para DespesaLancamento
   - Filtros por documento, período, tipo

3. **Criar tabelas dimensão**:
   - Dimensão Fonte (cofonte)
   - Dimensão Conta Contábil (cocontacontabil)
   - Dimensão UG (coug, noug)
   - Dimensão Natureza Despesa
   - Dimensão Evento (coevento)

4. **Desenvolver dashboards**:
   - Totais por período
   - Comparativo receita x despesa
   - Evolução temporal
   - Análise por UG

5. **Melhorias de performance**:
   - Criar views materializadas
   - Implementar particionamento por ano
   - Cache de consultas frequentes

## Observações Importantes
- O desenvolvedor é iniciante, então o código deve ser claro e bem comentado
- Preferência por explicações passo a passo
- Sistema inicialmente local, depois será deployado no Railway
- Dados sensíveis (financeiros/patrimoniais) - atenção à segurança
- **SEMPRE atualizar o cache após cargas incrementais!**

## Contexto de Negócio
Sistema para gestão de relatórios organizacionais com foco em:
- **Relatórios orçamentários**: Análise de planejamento vs realizado
- **Relatórios financeiros**: Fluxo de caixa, receitas e despesas
- **Relatórios patrimoniais**: Evolução de ativos e passivos

### Características dos Dados
- **Volume**: 4+ planilhas fato, com até 1 milhão+ de linhas cada
- **Periodicidade**: Dados mensais
- **Histórico**: Janeiro a Junho 2025 (saldos), Janeiro 2024 a Junho 2025 (lançamentos)
- **Atualizações**: Incrementais mensais (Julho em diante)
- **Transformações**: Parse de strings, cálculos de saldo, múltiplas colunas derivadas

## Decisões Técnicas Importantes

### Estratégia de ETL
- **Pandas** para ler Excel e manipular dados
- **SQLAlchemy** para gravar no PostgreSQL
- **Chunks**: Processamento em blocos de 5k-10k linhas
- Transformações aplicadas antes da carga
- Validações para evitar duplicatas em cargas incrementais

### Performance
- **Cache de filtros**: Tabela dedicada para valores únicos
- **Índices otimizados**: Por período, conta, UG
- **Processamento em chunks**: Para arquivos grandes

### Organização de Scripts
- Pasta `scripts/` para manutenção e setup
- Separação clara entre aplicação (`app/`) e utilitários
- Scripts podem ser executados independentemente
- Nomenclatura clara: load_[tabela]_incremental.py