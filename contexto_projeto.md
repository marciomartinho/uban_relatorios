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

### 🔄 Em Progresso
- ETL para outras planilhas fato
- Página de Consulta Saldo Despesa

### ⏳ Próximas Etapas
- Criar página de consulta para despesas
- Implementar ETL para demais planilhas
- Desenvolver dashboards com gráficos
- Implementar relatórios PDF

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
- ultimo_periodo_carregado: Ex: "2024-07"
- tipo_ultima_carga: "inicial" ou "incremental"
- total_registros_carregados: Contador acumulado

etl_log: Histórico detalhado de todas as cargas
- Registra cada execução de ETL
- Permite rastreabilidade completa
- Identifica erros e reprocessamentos
```

#### Transformações de Dados
Durante o ETL, serão aplicadas transformações como:
- Extração de ano/mês de colunas de período
- Cálculos de campos derivados
- Padronização de formatos
- Validação de integridade referencial

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
│   │   ├── relatorios.py  # Blueprint de relatórios
│   │   └── api.py         # Blueprint da API REST
│   ├── static/            # Assets estáticos
│   │   ├── css/          # Arquivos CSS
│   │   └── js/           # Arquivos JavaScript
│   ├── templates/         # Templates HTML (Jinja2)
│   │   ├── base.html     # Template base
│   │   └── relatorios/   # Templates específicos
│   └── modules/           # Módulos reutilizáveis
│       ├── database.py    # Conexão e helpers do banco
│       └── etl.py        # Lógica de importação Excel→DB
├── models/                # Modelos SQLAlchemy (ORM)
├── config.py             # Configurações da aplicação
├── .env                  # Variáveis de ambiente (credenciais)
├── run.py                # Entry point da aplicação
├── scripts/                # Scripts de manutenção e setup
│   ├── create_etl_tables.py # ✅ Criação das tabelas de controle
│   ├── setup_database.py    # Setup inicial completo
│   └── load_initial_data.py # Carga inicial dos dados
```

### 3. Configuração do Banco de Dados
- **Host**: 31.97.128.109:5432
- **Versão**: PostgreSQL 16.9 (Ubuntu)
- **Banco criado**: `relatorios_uban` ✅
- **Conexão**: SQLAlchemy com psycopg2
- **Tabelas de controle**: `etl_control` e `etl_log` ✅

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

## Cargas Incrementais - IMPORTANTE! 📌

### Como Funcionam
1. **Carga Inicial** (já feita): Janeiro a Junho 2025
2. **Cargas Incrementais**: Julho, Agosto, etc. (um mês por vez)

### Processo para Carga Incremental

#### Opção 1: Arquivo com Nome Fixo
```bash
# Substituir ReceitaSaldo.xlsx pelo arquivo do novo mês
# Executar:
python scripts/load_receita_saldo_incremental.py
```

#### Opção 2: Arquivo com Nome do Mês (RECOMENDADO)
```bash
# Manter arquivos separados: ReceitaSaldoJulho.xlsx, ReceitaSaldoAgosto.xlsx
# Executar passando o nome do arquivo:
python scripts/load_receita_saldo_incremental.py ReceitaSaldoJulho.xlsx
```

### Script de Carga Incremental (A CRIAR)
Precisamos criar `scripts/load_receita_saldo_incremental.py` que:
- NÃO limpa a tabela (mantém dados existentes)
- Valida se o período já foi carregado (evita duplicatas)
- Adiciona apenas os novos registros
- Atualiza o controle ETL

### Validações Importantes
- Verificar período do arquivo antes de carregar
- Impedir carga duplicada do mesmo mês
- Validar totais de crédito/débito para conferência

## Scripts de Análise

### Scripts deletados (não mais necessários)
- ~~analyze_excel.py~~ - Substituído por inspect_despesa_saldo.py
- ~~analyze_cocontacorrente.py~~ - Análise inicial concluída  
- ~~amostra_receitasaldo.xlsx~~ - Arquivo temporário

### Scripts mantidos em scripts/
```
create_schemas.py                  # Criar schemas
create_etl_tables.py              # Criar tabelas de controle
fix_etl_control.py                # Corrigir registros ETL
inspect_despesa_saldo.py          # Analisar arquivos Excel
load_receita_saldo.py             # Carga inicial receitas
load_receita_saldo_incremental.py # Carga incremental receitas
load_despesa_saldo.py             # Carga inicial despesas
load_despesa_saldo_incremental.py # Carga incremental despesas
```

### Organização dos Arquivos de Dados
```
dados_brutos/
├── fato/
│   ├── ReceitaSaldo.xlsx          # Jan-Jun (carga inicial) ✅
│   ├── DespesaSaldo.xlsx          # Jan-Jun (carga inicial) ✅
│   ├── ReceitaSaldoJulho.xlsx     # Julho (incremental) - A carregar
│   ├── DespesaSaldoJulho.xlsx     # Julho (incremental) - A carregar
│   └── ...
└── dimensao/
    └── (arquivos de dimensões) - A implementar
```

### Tabelas Criadas no Banco
```sql
-- Schemas
public                              -- Tabelas de sistema
receitas                           -- Dados de receitas
despesas                           -- Dados de despesas
dimensoes                          -- Futuras tabelas dimensão

-- Tabelas de Controle (schema public)
etl_control                        -- Controle de cargas por tabela
etl_log                           -- Log detalhado de todas as cargas

-- Tabelas Fato
receitas.fato_receita_saldo       -- 11.998 registros (Jan-Jun 2025)
despesas.fato_despesa_saldo       -- 560.110 registros (Jan-Jun 2025)
```

## Próximos Passos Recomendados

1. **Criar página Consulta Saldo Despesa**:
   - Similar à de receita mas com mais campos
   - Filtros por natureza, elemento, modalidade
   - Visualização hierárquica de despesas

2. **Carregar dados incrementais (Julho em diante)**:
   ```bash
   python scripts/load_receita_saldo_incremental.py ReceitaSaldoJulho.xlsx
   python scripts/load_despesa_saldo_incremental.py DespesaSaldoJulho.xlsx
   ```

3. **Implementar ETL para outras tabelas fato**:
   - Identificar outros arquivos Excel disponíveis
   - Criar módulos ETL específicos
   - Seguir padrão estabelecido

4. **Criar tabelas dimensão**:
   - Dimensão Fonte (cofonte)
   - Dimensão Conta Contábil (cocontacontabil)
   - Dimensão UG (coug, noug)
   - Dimensão Natureza Despesa
   - Outras dimensões necessárias

5. **Expandir interface web**:
   - Dashboard com totais e gráficos
   - Relatórios comparativos receita x despesa
   - Análise temporal (evolução mensal)
   - Exportação para PDF

6. **Melhorias futuras**:
   - Autenticação de usuários
   - Agendamento automático de cargas
   - Notificações por email
   - Cache de consultas frequentes
   - API REST documentada

#### Fase 1 - ETL e Banco
1. Criação automática de tabelas baseada nas planilhas Excel
2. Importação inicial de dados
3. Sistema de atualização (reimportação) de dados
4. Validação e tratamento de erros

#### Fase 2 - API e Relatórios
1. API REST para consulta de dados
2. Interface web para visualização de relatórios
3. Filtros dinâmicos (período, categoria, etc.)
4. Exportação de relatórios (PDF, Excel)

#### Fase 3 - Recursos Avançados
1. Dashboard com gráficos interativos
2. Sistema de permissões/usuários
3. Agendamento de atualizações automáticas
4. Notificações e alertas

## Padrões e Boas Práticas

### Segurança
- Credenciais em arquivo `.env` (nunca commitar)
- Validação de inputs
- Prepared statements para queries SQL

### Código
- Blueprints Flask para modularização
- Separação de responsabilidades (MVC)
- Docstrings e comentários em português
- Tratamento de exceções

### Frontend
- CSS e JS em arquivos separados
- Mobile-responsive
- Acessibilidade (ARIA labels)

## Dependências Principais
```
flask              # Framework web
psycopg2-binary   # Driver PostgreSQL
pandas            # Manipulação de dados
openpyxl          # Leitura de Excel
sqlalchemy        # ORM
python-dotenv     # Variáveis de ambiente
```

## Próximos Passos Imediatos
1. ✅ Estrutura de pastas criada
2. ✅ Configurar conexão segura com PostgreSQL (.env configurado)
3. ✅ Criar novo banco de dados (relatorios_uban criado)
4. ✅ Criar tabelas de controle ETL
5. ⏳ Analisar estrutura das planilhas Excel
6. ⏳ Implementar ETL básico com transformações
7. ⏳ Criar primeira rota Flask

## Decisões Técnicas Importantes

### Estratégia de ETL
- **Pandas** para ler Excel e manipular dados
- **SQLAlchemy** para gravar no PostgreSQL
- Transformações aplicadas antes da carga
- Validações para evitar duplicatas em cargas incrementais

### Organização de Scripts
- Pasta `scripts/` para manutenção e setup
- Separação clara entre aplicação (`app/`) e utilitários
- Scripts podem ser executados independentemente

## Comandos Úteis

### Ativar ambiente virtual
```bash
# Windows PowerShell
venv\Scripts\activate
```

### Scripts de manutenção
```bash
# Setup inicial
python scripts/create_schemas.py        # Criar schemas no banco
python scripts/create_etl_tables.py     # Criar tabelas de controle

# Carga inicial de dados
python scripts/load_receita_saldo.py    # Receitas (apaga e recarrega)
python scripts/load_despesa_saldo.py    # Despesas (apaga e recarrega)

# Carga incremental
python scripts/load_receita_saldo_incremental.py [arquivo.xlsx]
python scripts/load_despesa_saldo_incremental.py [arquivo.xlsx]

# Manutenção
python scripts/fix_etl_control.py       # Corrigir tabelas de controle
python scripts/inspect_despesa_saldo.py # Analisar estrutura de arquivo

# Executar aplicação web
python run.py                           # Inicia servidor Flask em http://localhost:5000
```

### Executar aplicação
```bash
python run.py
```

## Observações Importantes
- O desenvolvedor é iniciante, então o código deve ser claro e bem comentado
- Preferência por explicações passo a passo
- Sistema inicialmente local, depois será deployado no Railway
- Dados sensíveis (financeiros/patrimoniais) - atenção à segurança

## Contexto de Negócio
Sistema para gestão de relatórios organizacionais com foco em:
- **Relatórios orçamentários**: Análise de planejamento vs realizado
- **Relatórios financeiros**: Fluxo de caixa, receitas e despesas
- **Relatórios patrimoniais**: Evolução de ativos e passivos

### Características dos Dados
- **Volume**: 4+ planilhas fato, com até 1 milhão+ de linhas cada
- **Periodicidade**: Dados mensais
- **Histórico**: Janeiro a Junho 2025 (carga inicial)
- **Atualizações**: Incrementais mensais (Julho em diante)
- **Transformações**: Parse de strings, cálculos de saldo, múltiplas colunas derivadas

### Tabelas Criadas
1. **public.etl_control**: Controle de cargas por tabela
2. **public.etl_log**: Log detalhado de todas as cargas
3. **receitas.fato_receita_saldo**: Dados de saldo de receitas (11.998 registros)

Os dados fonte estão em planilhas Excel que precisam ser consolidadas em um banco de dados PostgreSQL para permitir análises mais complexas e geração de relatórios padronizados.

## Arquivos e Módulos Principais

### Configuração
- **.env**: Credenciais do banco (NUNCA commitar!)
- **config.py**: Centraliza configurações do sistema
- **.gitignore**: Protege arquivos sensíveis

### Banco de Dados  
- **app/modules/database.py**: Classe Database com todos os métodos de acesso
- **scripts/create_etl_tables.py**: Cria tabelas de controle ETL

### ETL (a implementar)
- **app/modules/etl.py**: Lógica principal de ETL
- **scripts/load_initial_data.py**: Carga inicial (Jan-Jun)
- **scripts/update_incremental.py**: Cargas mensais incrementais