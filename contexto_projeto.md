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
9. **ETL ReceitaLancamento**:
   - Módulo `etl_receita_lancamento.py` implementado
   - Tabela `receitas.fato_receita_lancamento` criada e populada
   - 490.122 registros carregados (2024-01 a 2025-06)
   - Parse de COCONTACORRENTE (17, 38 e 40 chars)
   - Campo `tipo_lancamento` (DEBITO/CREDITO)
   - Sistema de carga incremental implementado
10. **ETL DespesaLancamento**: ✅ NOVO!
    - Módulo `etl_despesa_lancamento.py` implementado
    - Tabela `despesas.fato_despesa_lancamento` criada
    - Preparado para ~1.000.000 registros
    - Parse de COCONTACORRENTE (38 e 40 chars com strip())
    - Campo `tipo_lancamento` baseado em INDEBITOCREDITO
    - Sistema otimizado para grandes volumes
11. **Aplicação Flask**: 
    - Servidor web funcionando
    - Sistema de blueprints configurado
    - Templates base e home criados
12. **Interface Web - Consulta Saldo Receita**:
    - Página totalmente funcional
    - Filtros dinâmicos (Ano, Conta, UG)
    - Opção "Consolidado" para somar todas UGs
    - Tabela com colunas dinâmicas (17 ou 38 chars)
    - Filtros por coluna tipo Excel
    - Exportação para CSV
    - Formatação monetária brasileira
    - Design responsivo com Bootstrap
13. **Interface Web - Consulta Saldo Despesa**:
    - Página totalmente funcional
    - Sistema de cache implementado para performance
    - Correção de bugs SQL realizada
    - Índices otimizados criados
    - Funciona com 560k+ registros sem travar
    - Ordenação por mês (Janeiro a Dezembro)
    - Esfera mostra número do banco (não texto)
14. **Interface Web - Detalha Conta Contábil Receita**: ✅ NOVO!
    - Página totalmente funcional para análise detalhada de lançamentos
    - Filtros: Ano, Conta Contábil e UG Contábil (com opção CONSOLIDADO)
    - Cards de resumo: Total Créditos, Total Débitos, Saldo e Total de Lançamentos
    - Saldo calculado dinamicamente: contas 5* (Débito-Crédito), contas 6* (Crédito-Débito)
    - Tabela detalhada com colunas: Mês, Documento, Evento, Conta Corrente, Valor, D/C, UG, Data, Tipo
    - Filtros tipo Excel nas colunas: Mês, Documento, Evento e Conta Corrente
    - Ordenação por mês e depois por data
    - Exportação para CSV com resumo no final
    - Valores coloridos: verde para créditos, vermelho para débitos

### 🚀 Sistema de Cache
- **Tabela**: `public.cache_filtros_despesa`
- **Função**: Armazena valores únicos de anos, contas e UGs
- **Performance**: Reduz tempo de carregamento de minutos para milissegundos
- **Script**: `scripts/otimizar_despesas.py` para criar/atualizar

### ⏳ Em Andamento
- Carregamento inicial de DespesaLancamento (tabela criada, aguardando processamento)
- Interface Web - Detalha Conta Contábil Despesa (próxima etapa)

### 📋 Próximas Etapas
- Completar carga inicial de DespesaLancamento
- Criar página Detalha Conta Contábil Despesa (similar à de Receita)
- Desenvolver dashboards com gráficos
- Implementar relatórios PDF
- Sistema de autenticação

## 📚 GUIA DO USUÁRIO - Como Atualizar os Dados Mensalmente

### 🎯 O que você vai fazer todo mês
Todo mês você vai receber 4 arquivos Excel novos com os dados do mês:
- ReceitaSaldoMês.xlsx
- DespesaSaldoMês.xlsx
- ReceitaLancamentoMês.xlsx
- DespesaLancamentoMês.xlsx

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

3. **IMPORTANTE**: Feche o Excel! Não deixe nenhum arquivo aberto no Excel durante o processamento.

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

### 💸 PASSO 7: Adicionar DESPESA LANÇAMENTO ✅ NOVO!

Digite e aperte Enter (substitua "Julho" pelo mês correto):
```powershell
python scripts/load_despesa_lancamento_incremental.py DespesaLancamentoJulho.xlsx
```

**O que vai acontecer**:
1. Similar aos anteriores
2. Demora mais (15-25 minutos) porque tem ~1 milhão de registros
3. Primeiro lê o arquivo todo (1-3 minutos)
4. Depois processa com barra de progresso
5. No final mostra "✅ Carga incremental concluída com sucesso!"

### ⚡ PASSO 8: Atualizar o CACHE (MUITO IMPORTANTE!)

**Por que isso é importante?** O cache é como um índice de livro. Se você não atualizar, o sistema não vai mostrar os novos meses nos filtros!

Digite e aperte Enter:
```powershell
python scripts/otimizar_despesas.py
```

**O que vai acontecer**:
1. Vai recriar a lista de anos, contas e UGs
2. Demora 2-3 minutos
3. No final mostra "✨ OTIMIZAÇÃO CONCLUÍDA COM SUCESSO!"

### ✅ PASSO 9: Verificar se Funcionou

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

**"Permission denied" ou "Permissão negada"**:
- FECHE O EXCEL! O arquivo está aberto
- Verifique se nenhum programa está usando o arquivo

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
1. Copiar 4 arquivos Excel para dados_brutos/fato/
2. FECHAR O EXCEL!!!
3. Abrir PowerShell na pasta do projeto
4. venv\Scripts\activate
5. python scripts/load_receita_saldo_incremental.py ReceitaSaldoMES.xlsx
6. python scripts/load_despesa_saldo_incremental.py DespesaSaldoMES.xlsx
7. python scripts/load_receita_lancamento_incremental.py ReceitaLancamentoMES.xlsx
8. python scripts/load_despesa_lancamento_incremental.py DespesaLancamentoMES.xlsx
9. python scripts/otimizar_despesas.py
10. python run.py (para testar)
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

cache_filtros_despesa: Cache para performance
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
│   └── fato/              # Dados de fatos (4 arquivos principais)
├── app/                    # Aplicação Flask
│   ├── __init__.py        # Inicialização e configuração Flask
│   ├── routes/            # Blueprints de rotas
│   │   ├── main.py        # Rotas principais
│   │   ├── saldo_receita.py  # Página de receitas
│   │   ├── saldo_despesa.py  # Página de despesas
│   │   └── detalha_receita.py # Página detalha conta contábil receita ✅ NOVO!
│   ├── static/            # Assets estáticos
│   │   ├── css/          # Arquivos CSS
│   │   │   ├── base.css
│   │   │   ├── saldo_receita.css
│   │   │   ├── saldo_despesa.css
│   │   │   └── detalha_receita.css ✅ NOVO!
│   │   └── js/           # Arquivos JavaScript
│   │       ├── base.js
│   │       ├── saldo_receita.js
│   │       ├── saldo_despesa.js
│   │       └── detalha_receita.js ✅ NOVO!
│   ├── templates/         # Templates HTML (Jinja2)
│   │   ├── base.html     # Template base (atualizado com novo menu)
│   │   ├── home.html
│   │   ├── saldo_receita/ # Templates de receita
│   │   │   └── consulta_saldo_receita.html
│   │   ├── saldo_despesa/ # Templates de despesa
│   │   │   └── consulta_saldo_despesa.html
│   │   └── detalha_receita/ # Templates detalha receita ✅ NOVO!
│   │       └── consulta_detalha_receita.html
│   └── modules/           # Módulos reutilizáveis
│       ├── database.py    # Conexão e helpers do banco
│       ├── etl_receita_saldo.py      # ETL de receitas saldo
│       ├── etl_despesa_saldo.py      # ETL de despesas saldo
│       ├── etl_receita_lancamento.py # ETL de receitas lançamento
│       └── etl_despesa_lancamento.py # ETL de despesas lançamento ✅ NOVO!
├── models/                # Modelos SQLAlchemy (ORM)
├── config.py             # Configurações da aplicação
├── .env                  # Variáveis de ambiente (credenciais)
├── run.py                # Entry point da aplicação
├── scripts/              # Scripts de manutenção e setup
│   ├── load_receita_saldo_incremental.py     # Carga incremental receitas saldo
│   ├── load_despesa_saldo_incremental.py     # Carga incremental despesas saldo
│   ├── load_receita_lancamento.py            # Carga inicial receitas lançamento
│   ├── load_receita_lancamento_incremental.py # Carga incremental receitas lançamento
│   ├── load_despesa_lancamento.py            # Carga inicial despesas lançamento ✅ NOVO!
│   ├── load_despesa_lancamento_incremental.py # Carga incremental despesas lançamento ✅ NOVO!
│   ├── otimizar_despesas.py                  # Otimização completa (cache + índices)
│   ├── inspect_despesa_lancamento.py         # Inspeção de estrutura ✅ NOVO!
│   └── inspect_campos_lancamentos.py         # Inspeção campos das tabelas lançamento ✅ NOVO!
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

### Campos da Tabela receitas.fato_receita_lancamento
```sql
-- Campos principais
1. coexercicio (integer NOT NULL) - Ano do exercício
2. coug (integer NOT NULL) - Código da UG
3. nudocumento (varchar(20) NOT NULL) - Número do documento
4. nulancamento (integer NOT NULL) - Número do lançamento
5. coevento (integer) - Código do evento
6. cocontacontabil (bigint) - Conta contábil
7. cocontacorrente (varchar(50)) - Conta corrente (17, 38 ou 40 chars)
8. inmes (integer) - Mês do lançamento
9. dalancamento (date) - Data do lançamento (ATENÇÃO: nome é dalancamento, não dtlancamento)
10. valancamento (numeric) - Valor do lançamento
11. indebitocredito (varchar(1)) - Indicador D/C
12. cougcontab (integer) - UG contábil (usado no filtro da página)
13. tipo_lancamento (varchar(10)) - DEBITO ou CREDITO

-- Campos derivados do parse de cocontacorrente
14-26. Campos de 17 chars (classificação orçamentária)
27-39. Campos de 38 chars (natureza despesa)
40. cosubelemento (varchar(2)) - Para contas de 40 chars

-- Campos de controle
41. periodo (varchar(7)) - Período no formato YYYY-MM
42. data_carga (timestamp) - Data/hora da carga
```

### ⚠️ IMPORTANTE - Erros Comuns e Como Resolver

1. **Nome do campo de data**: O campo é `dalancamento` (com apenas um 'l'), NÃO `dtlancamento`
2. **UG vs UG Contábil**: 
   - No filtro da página usar: `cougcontab` (UG Contábil)
   - Na tabela mostrar: `coug` (UG)
3. **Cálculo do Saldo**:
   - Contas começando com 5: Saldo = Débitos - Créditos
   - Contas começando com 6: Saldo = Créditos - Débitos
4. **Ordem de exibição**: Primeiro por mês (numérico), depois por data

## ETL DespesaLancamento - Detalhamento ✅ NOVO!

### Estrutura da Tabela
A tabela `despesas.fato_despesa_lancamento` possui:
- **Preparada para ~1.000.000 registros**
- **Período**: Esperado similar ao ReceitaLancamento
- **Diferencial**: Volume muito maior que receitas
- **Campo adicional**: `tipo_lancamento` (DEBITO/CREDITO) baseado em INDEBITOCREDITO
- **Parse otimizado**: Apenas contas de 38 e 40 caracteres (com strip() automático)
- **Processamento**: Em chunks de 10.000 registros para otimizar memória

### Características Especiais
1. **Tratamento de espaços**: Excel adiciona padding, sistema faz strip() automático
2. **Otimização para grandes volumes**: Leitura completa + processamento em chunks
3. **Índices específicos**: Adicionados em `conatureza` e `coevento` para performance
4. **Validação de tamanhos**: Log da distribuição de tamanhos de COCONTACORRENTE

## Interface Web - Detalha Conta Contábil Receita ✅ NOVO!

### Arquivos Criados
1. **app/routes/detalha_receita.py** - Blueprint com 3 rotas:
   - `/consulta` - Página principal
   - `/api/filtros` - Retorna valores únicos para os filtros
   - `/api/dados` - Retorna lançamentos filtrados
   - `/api/totais` - Retorna totais de débito/crédito e saldo

2. **app/templates/detalha_receita/consulta_detalha_receita.html**:
   - Layout com cards de resumo no topo
   - Tabela detalhada dos lançamentos
   - Modal de loading

3. **app/static/css/detalha_receita.css**:
   - Estilos para cards coloridos
   - Classes para valores positivos/negativos
   - Badges para tipo de lançamento

4. **app/static/js/detalha_receita.js**:
   - Carregamento dinâmico de filtros
   - Construção da tabela com DataTables
   - Filtros tipo Excel nas colunas
   - Exportação para CSV

### Integração no Sistema
1. **Atualização do base.html**:
   - Novo menu dropdown "Detalha Conta Contábil"
   - Submenu para Receita (funcional)
   - Submenu para Despesa (desabilitado temporariamente)

2. **Registro no __init__.py**:
   ```python
   from app.routes.detalha_receita import detalha_receita
   app.register_blueprint(detalha_receita, url_prefix='/detalha-receita')
   ```

### Funcionalidades Implementadas
- **Filtros**: Ano, Conta Contábil, UG Contábil (com opção CONSOLIDADO)
- **Cards de Resumo**: Total Créditos, Total Débitos, Saldo, Total de Lançamentos
- **Fórmula do Saldo**: Mostra dinamicamente (D-C) ou (C-D) baseado na conta
- **Tabela**: Mês, Documento, Evento, Conta Corrente, Valor, D/C, UG, Data, Tipo
- **Filtros nas Colunas**: Mês, Documento, Evento e Conta Corrente
- **Ordenação**: Por mês (numérico) e depois por data
- **Cores**: Verde para créditos, vermelho para débitos
- **Exportação**: CSV com resumo dos totais no final

### Possíveis Problemas e Soluções
1. **Erro de sintaxe JavaScript**: Verificar final do arquivo, sem caracteres extras
2. **Campos não encontrados**: Usar `dalancamento` em vez de `dtlancamento`
3. **Filtros não carregam**: Verificar se as queries SQL estão corretas
4. **Performance**: Considerar limitar resultados ou implementar paginação server-side

## Scripts de Manutenção

### Scripts Principais Ativos
```
# Otimização e Cache
otimizar_despesas.py              # Cria cache e índices (executar após cada carga)

# Cargas incrementais mensais (4 arquivos)
load_receita_saldo_incremental.py        # Adiciona novos meses de receita saldo
load_despesa_saldo_incremental.py        # Adiciona novos meses de despesa saldo
load_receita_lancamento_incremental.py   # Adiciona novos meses de receita lançamento
load_despesa_lancamento_incremental.py   # Adiciona novos meses de despesa lançamento ✅ NOVO!

# Cargas iniciais (se precisar recarregar)
load_receita_lancamento.py        # Carga inicial de receita lançamento
load_despesa_lancamento.py        # Carga inicial de despesa lançamento ✅ NOVO!

# Inspeção de arquivos
inspect_receita_lancamento.py     # Analisa estrutura de arquivo de receita
inspect_despesa_lancamento.py     # Analisa estrutura de arquivo de despesa ✅ NOVO!
inspect_campos_lancamentos.py     # Lista campos das tabelas de lançamento ✅ NOVO!
```

### Scripts Removidos (já executados)
- ~~create_schemas.py~~ - Schemas já criados
- ~~create_etl_tables.py~~ - Tabelas ETL já criadas
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
despesas.fato_despesa_lancamento  -- Aguardando carga (~1M registros) ⏳
```

## Comandos Úteis

### Ativar ambiente virtual
```bash
# Windows PowerShell
venv\Scripts\activate
```

### Rotina Mensal de Atualização (4 arquivos)
```bash
# 1. Adicionar receitas saldo do mês
python scripts/load_receita_saldo_incremental.py ReceitaSaldoMES.xlsx

# 2. Adicionar despesas saldo do mês
python scripts/load_despesa_saldo_incremental.py DespesaSaldoMES.xlsx

# 3. Adicionar receitas lançamento do mês
python scripts/load_receita_lancamento_incremental.py ReceitaLancamentoMES.xlsx

# 4. Adicionar despesas lançamento do mês ✅ NOVO!
python scripts/load_despesa_lancamento_incremental.py DespesaLancamentoMES.xlsx

# 5. Atualizar cache (IMPORTANTE!)
python scripts/otimizar_despesas.py

# 6. Testar sistema
python run.py
```

### Manutenção e Correções
```bash
# Ver estrutura de arquivo Excel novo
python scripts/inspect_despesa_lancamento.py

# Carregar dados iniciais (se necessário)
python scripts/load_despesa_lancamento.py

# Inspecionar campos das tabelas
python scripts/inspect_campos_lancamentos.py
```

## Próximos Passos Recomendados

1. **Completar carga de DespesaLancamento**:
   - Executar carga inicial
   - Validar dados carregados
   - Testar performance com 1M+ registros

2. **Criar página Detalha Conta Contábil Despesa**:
   - Copiar estrutura da página de Receita
   - Ajustar queries para tabela `despesas.fato_despesa_lancamento`
   - Considerar paginação server-side devido ao volume

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
   - Análise por natureza de despesa

5. **Melhorias de performance**:
   - Criar views materializadas para lançamentos
   - Implementar particionamento por ano
   - Cache de consultas frequentes
   - Considerar índices adicionais para consultas específicas

## Observações Importantes
- O desenvolvedor é iniciante, então o código deve ser claro e bem comentado
- Preferência por explicações passo a passo
- Sistema inicialmente local, depois será deployado no Railway
- Dados sensíveis (financeiros/patrimoniais) - atenção à segurança
- **SEMPRE atualizar o cache após cargas incrementais!**
- **SEMPRE fechar o Excel antes de processar arquivos!**
- **Campo de data é `dalancamento`, NÃO `dtlancamento`!**

## Contexto de Negócio
Sistema para gestão de relatórios organizacionais com foco em:
- **Relatórios orçamentários**: Análise de planejamento vs realizado
- **Relatórios financeiros**: Fluxo de caixa, receitas e despesas
- **Relatórios patrimoniais**: Evolução de ativos e passivos

### Características dos Dados
- **Volume**: 4 planilhas fato principais
  - ReceitaSaldo: ~12k registros/mês
  - DespesaSaldo: ~93k registros/mês
  - ReceitaLancamento: ~27k registros/mês
  - DespesaLancamento: ~170k registros/mês (maior volume)
- **Periodicidade**: Dados mensais
- **Histórico**: Janeiro 2024 a Junho 2025 (lançamentos), Janeiro a Junho 2025 (saldos)
- **Atualizações**: Incrementais mensais (Julho em diante)
- **Transformações**: Parse de strings, cálculos de saldo, múltiplas colunas derivadas

## Decisões Técnicas Importantes

### Estratégia de ETL
- **Pandas** para ler Excel e manipular dados
- **SQLAlchemy** para gravar no PostgreSQL
- **Chunks**: Processamento em blocos de 5k-10k linhas
- Transformações aplicadas antes da carga
- Validações para evitar duplicatas em cargas incrementais
- **Strip()** automático em campos de texto para remover padding do Excel

### Performance
- **Cache de filtros**: Tabela dedicada para valores únicos
- **Índices otimizados**: Por período, conta, UG, natureza, evento
- **Processamento em chunks**: Para arquivos grandes (especialmente DespesaLancamento)
- **Leitura otimizada**: Arquivo completo + processamento em blocos

### Organização de Scripts
- Pasta `scripts/` para manutenção e setup
- Separação clara entre aplicação (`app/`) e utilitários
- Scripts podem ser executados independentemente
- Nomenclatura clara: load_[tabela]_incremental.py
- Scripts de inspeção para análise de novos arquivos

Sistema de Lançamentos com DuckDB
✅ O que fizemos hoje:

Instalamos o DuckDB no ambiente virtual existente
Criamos a estrutura local para armazenar lançamentos:

Pasta: dados_brutos/fato/db_local/
Banco: lancamentos.duckdb


Migramos 1.5 milhão de registros do PostgreSQL para DuckDB
Criamos módulos ETL otimizados para processar Excel direto no DuckDB
Criamos scripts de carga mensal para você usar todo mês

📁 Arquivos criados:
relatorios_uban/
├── app/modules/
│   ├── database_duckdb.py              # Conexão com DuckDB
│   ├── etl_lancamento_duckdb.py        # ETL base
│   ├── etl_receita_lancamento_duckdb.py # ETL receitas
│   └── etl_despesa_lancamento_duckdb.py # ETL despesas
├── scripts/
│   ├── criar_tabelas_duckdb.py         # Cria estrutura (já executado)
│   ├── migrar_lancamentos_para_duckdb.py # Migração inicial (já executado)
│   ├── load_receita_lancamento_duckdb.py # Carga mensal receitas
│   ├── load_despesa_lancamento_duckdb.py # Carga mensal despesas
│   └── consultar_lancamentos_duckdb.py   # Consultas rápidas
└── dados_brutos/fato/db_local/
    └── lancamentos.duckdb               # Banco com 1.5M registros
🎯 Como usar MENSALMENTE:
Para carregar ReceitaLancamentoJulho.xlsx:
bash# 1. Ativar ambiente virtual
venv\Scripts\activate

# 2. Carregar receitas
python scripts/load_receita_lancamento_duckdb.py ReceitaLancamentoJulho.xlsx
Para carregar DespesaLancamentoJulho.xlsx:
bashpython scripts/load_despesa_lancamento_duckdb.py DespesaLancamentoJulho.xlsx
Para fazer consultas rápidas:
bashpython scripts/consultar_lancamentos_duckdb.py
🚀 Vantagens do novo sistema:

Performance: DuckDB é MUITO mais rápido para análises locais
Simplicidade: Apenas 1 arquivo .duckdb para backup
Economia: Não consome recursos da VPS
Autonomia: Funciona offline, sem depender de internet
Escalabilidade: Suporta bilhões de registros facilmente

⚠️ IMPORTANTE - O que NÃO muda:

✅ Sistema web continua funcionando normalmente
✅ Tabelas de SALDO continuam no PostgreSQL da VPS
✅ Scripts de saldo (load_receita_saldo_incremental.py, etc) continuam iguais
✅ Páginas web de consulta de saldo continuam funcionando