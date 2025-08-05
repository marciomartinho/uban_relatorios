Contexto do Projeto - Sistema de Relatórios Orçamentários, Financeiros e Patrimoniais
Visão Geral
Sistema web desenvolvido em Python/Flask para gerenciamento e geração de relatórios orçamentários, financeiros e patrimoniais. O sistema utiliza uma arquitetura híbrida:

PostgreSQL (VPS): Para dados de SALDO (menor volume, consultas frequentes)
DuckDB (Local): Para dados de LANÇAMENTO (grande volume, 1.5M+ registros)

Stack Tecnológica

Backend: Python 3.x, Flask (com Blueprints)
Bancos de Dados:

PostgreSQL 16.9 (VPS) - Dados de Saldo
DuckDB (Local) - Dados de Lançamento


ORM: SQLAlchemy (PostgreSQL)
Frontend: HTML, CSS (separado), JavaScript (separado)
ETL: Pandas + DuckDB para processamento eficiente
Deploy: Desenvolvimento local, futura implantação no Railway

🦆 MIGRAÇÃO PARA DUCKDB - GRANDE MUDANÇA!
Por que DuckDB?

Performance: 10-100x mais rápido que PostgreSQL para análises
Simplicidade: Apenas 1 arquivo .duckdb (backup fácil)
Economia: Não consome recursos da VPS
Autonomia: Funciona offline
Escalabilidade: Suporta bilhões de registros

O que foi migrado

✅ receita_lancamento: 490.122 registros
✅ despesa_lancamento: 1.068.000 registros
Total: 1.558.122 registros migrados com sucesso!

Arquitetura Híbrida
┌─────────────────┐         ┌──────────────────┐
│   PostgreSQL    │         │     DuckDB       │
│     (VPS)       │         │    (Local)       │
├─────────────────┤         ├──────────────────┤
│ • Saldo Receita │         │ • Receita Lanç. │
│ • Saldo Despesa │         │ • Despesa Lanç. │
│ • ETL Control   │         │                  │
│ • Cache         │         │ 1.5M+ registros  │
└─────────────────┘         └──────────────────┘
Status Atual do Desenvolvimento
✅ Concluído - PostgreSQL (VPS)

Banco de Dados: relatorios_uban criado
Schemas: public, receitas, despesas, dimensoes
Tabelas de Controle ETL: etl_control, etl_log
ETL ReceitaSaldo: 11.998 registros (Jan-Jun 2025)
ETL DespesaSaldo: 560.110 registros (Jan-Jun 2025)
Sistema de Cache: Para filtros de despesa
Interface Web - Saldo Receita: Totalmente funcional
Interface Web - Saldo Despesa: Totalmente funcional

✅ Concluído - DuckDB (Local)

Banco criado: dados_brutos/fato/db_local/lancamentos.duckdb
Tabelas:

receita_lancamento: 490.122 registros migrados
despesa_lancamento: 1.068.000 registros migrados


Módulos ETL DuckDB:

database_duckdb.py: Conexão e helpers
etl_lancamento_duckdb.py: ETL base
etl_receita_lancamento_duckdb.py: ETL receitas
etl_despesa_lancamento_duckdb.py: ETL despesas


Scripts de Carga:

load_receita_lancamento_duckdb.py: Carga mensal
load_despesa_lancamento_duckdb.py: Carga mensal


Interface Web - Detalha Receita: Adaptada para DuckDB
Interface Web - Detalha Despesa: Adaptada para DuckDB

🚀 Em Andamento

Otimização de queries DuckDB
Criação de índices específicos do DuckDB

📋 Próximas Etapas

Criar views materializadas no DuckDB
Implementar backup automático do .duckdb
Desenvolver dashboards com dados combinados
Sistema de autenticação

📚 GUIA DO USUÁRIO - Como Atualizar os Dados Mensalmente
🎯 Dois Tipos de Dados, Dois Processos
1️⃣ DADOS DE SALDO (PostgreSQL - VPS)
Todo mês você recebe 2 arquivos:

ReceitaSaldoMês.xlsx
DespesaSaldoMês.xlsx

Como processar:
powershell# Ativar ambiente
venv\Scripts\activate

# Carregar receitas
python scripts/load_receita_saldo_incremental.py ReceitaSaldoJulho.xlsx

# Carregar despesas
python scripts/load_despesa_saldo_incremental.py DespesaSaldoJulho.xlsx

# Atualizar cache
python scripts/otimizar_despesas.py
2️⃣ DADOS DE LANÇAMENTO (DuckDB - Local) 🦆
Todo mês você recebe 2 arquivos:

ReceitaLancamentoMês.xlsx
DespesaLancamentoMês.xlsx

Como processar:
powershell# Já com ambiente ativado

# Carregar receitas
python scripts/load_receita_lancamento_duckdb.py ReceitaLancamentoJulho.xlsx

# Carregar despesas  
python scripts/load_despesa_lancamento_duckdb.py DespesaLancamentoJulho.xlsx

# Consultar dados (opcional)
python scripts/consultar_lancamentos_duckdb.py
📝 Resumo Rápido - Rotina Mensal Completa
TODO MÊS - 4 ARQUIVOS:
1. Copiar os 4 arquivos Excel para dados_brutos/fato/
2. FECHAR O EXCEL!!!
3. Abrir PowerShell na pasta do projeto
4. venv\Scripts\activate

SALDO (PostgreSQL):
5. python scripts/load_receita_saldo_incremental.py ReceitaSaldoMES.xlsx
6. python scripts/load_despesa_saldo_incremental.py DespesaSaldoMES.xlsx
7. python scripts/otimizar_despesas.py

LANÇAMENTO (DuckDB):
8. python scripts/load_receita_lancamento_duckdb.py ReceitaLancamentoMES.xlsx
9. python scripts/load_despesa_lancamento_duckdb.py DespesaLancamentoMES.xlsx

TESTAR:
10. python run.py
Arquitetura do Sistema
1. Camada de Dados - ARQUITETURA HÍBRIDA 💗
O sistema utiliza dois bancos de dados para otimizar performance:
PostgreSQL (VPS) - Dados de SALDO

Localização: Servidor remoto (31.97.128.109:5432)
Função: Armazenar dados agregados (saldos mensais)
Volume: ~600k registros total
Vantagem: Acesso remoto, backups automáticos

DuckDB (Local) - Dados de LANÇAMENTO

Localização: dados_brutos/fato/db_local/lancamentos.duckdb
Função: Armazenar dados detalhados (lançamentos individuais)
Volume: 1.5M+ registros (crescendo ~200k/mês)
Vantagem: Performance extrema, processamento local

2. Estrutura de Diretórios
relatorios_uban/
├── venv/                    # Ambiente virtual Python
├── dados_brutos/           # Planilhas Excel fonte
│   ├── dimensao/          # Dados dimensionais
│   └── fato/              # Dados de fatos
│       ├── db_local/      # 🦆 NOVO! Banco DuckDB
│       │   └── lancamentos.duckdb  # 1.5M+ registros
│       └── *.xlsx         # Arquivos Excel mensais
├── app/                    # Aplicação Flask
│   ├── routes/            # Blueprints de rotas
│   │   ├── saldo_receita.py     # PostgreSQL
│   │   ├── saldo_despesa.py     # PostgreSQL
│   │   ├── detalha_receita.py   # DuckDB 🦆
│   │   └── detalha_despesa.py   # DuckDB 🦆
│   └── modules/           # Módulos reutilizáveis
│       ├── database.py              # Conexão PostgreSQL
│       ├── database_duckdb.py       # 🦆 Conexão DuckDB
│       ├── etl_lancamento_duckdb.py # 🦆 ETL base DuckDB
│       ├── etl_receita_lancamento_duckdb.py # 🦆
│       └── etl_despesa_lancamento_duckdb.py # 🦆
├── scripts/              # Scripts de manutenção
│   ├── PostgreSQL (VPS)/
│   │   ├── load_receita_saldo_incremental.py
│   │   ├── load_despesa_saldo_incremental.py
│   │   └── otimizar_despesas.py
│   └── DuckDB (Local)/ 🦆
│       ├── criar_tabelas_duckdb.py
│       ├── migrar_lancamentos_para_duckdb.py
│       ├── load_receita_lancamento_duckdb.py
│       ├── load_despesa_lancamento_duckdb.py
│       └── consultar_lancamentos_duckdb.py
3. Módulos DuckDB Criados
database_duckdb.py
python# Classe para gerenciar conexões DuckDB
class DuckDBManager:
    - get_connection(): Retorna conexão
    - execute_query(): Executa queries
    - read_sql(): Retorna DataFrame
    - get_table_info(): Info sobre tabelas
etl_lancamento_duckdb.py
python# ETL base para lançamentos
class ETLLancamentoDuckDB:
    - validar_periodo_novo(): Verifica duplicatas
    - processar_arquivo(): Processa Excel
    - aplicar_transformacoes(): Parse de campos
    - carregar_dados(): Insere no DuckDB
Tabelas DuckDB - Estrutura
receita_lancamento
sql-- 490.122 registros
CREATE TABLE receita_lancamento (
    coexercicio INTEGER,
    periodo VARCHAR(7),
    coug INTEGER,
    nudocumento VARCHAR(20),
    dalancamento DATE,
    valancamento DOUBLE,
    tipo_lancamento VARCHAR(10),
    -- ... 40+ campos totais
);
despesa_lancamento
sql-- 1.068.000 registros
CREATE TABLE despesa_lancamento (
    coexercicio INTEGER,
    periodo VARCHAR(7),
    coug INTEGER,
    nudocumento VARCHAR(20),
    dalancamento DATE,
    valancamento DOUBLE,
    tipo_lancamento VARCHAR(10),
    conatureza VARCHAR(6),
    -- ... 40+ campos totais
);
Performance Comparada
Consulta típica (1000 registros):

PostgreSQL (VPS): 2-5 segundos
DuckDB (Local): 0.1-0.3 segundos

Agregação completa (1.5M registros):

PostgreSQL (VPS): 30-60 segundos
DuckDB (Local): 1-3 segundos

Carga de 100k registros:

PostgreSQL (VPS): 5-10 minutos
DuckDB (Local): 10-30 segundos

Comandos Úteis - DuckDB
Consultas rápidas
bash# Ver estatísticas
python scripts/consultar_lancamentos_duckdb.py

# Consulta SQL customizada
python
>>> from app.modules.database_duckdb import db_duckdb
>>> conn = db_duckdb.get_connection()
>>> conn.execute("SELECT COUNT(*) FROM receita_lancamento").fetchone()
>>> conn.close()
Backup do DuckDB
bash# Fazer backup (copiar arquivo)
copy dados_brutos\fato\db_local\lancamentos.duckdb backup_lancamentos.duckdb

# Verificar integridade
python -c "import duckdb; conn = duckdb.connect('lancamentos.duckdb'); print(conn.execute('PRAGMA integrity_check').fetchall())"
Decisões Técnicas - DuckDB
Por que arquitetura híbrida?

Saldos no PostgreSQL: Menor volume, backup automático na VPS
Lançamentos no DuckDB: Grande volume, performance crítica
Separação clara: Cada banco otimizado para seu uso

Vantagens do DuckDB

Columnar storage: Ideal para análises
Vetorização: Processa dados em blocos
Zero configuração: Funciona out-of-the-box
SQL completo: Suporta CTEs, window functions, etc.

Limitações aceitas

Local only: Backup manual necessário
Single file: Pode crescer muito (GB)
No concurrent writes: Adequado para ETL batch

Próximos Passos Recomendados

Otimizações DuckDB:

Criar índices específicos
Implementar particionamento por ano
Views materializadas para consultas frequentes


Backup Automático:

Script para backup diário do .duckdb
Compressão e versionamento
Upload para cloud (opcional)


Dashboards Híbridos:

Combinar dados de ambos os bancos
Cache de resultados agregados
Gráficos interativos


Migração Completa (futuro):

Considerar migrar saldos para DuckDB também
Unificar toda análise local
PostgreSQL apenas para sistema web



🆘 Troubleshooting DuckDB
"Database is locked":

Feche todas as conexões Python
Reinicie o kernel/terminal

"Out of memory":

Processe em chunks menores
Use PRAGMA memory_limit='2GB'

Arquivo muito grande:

Execute VACUUM periodicamente
Considere particionar por ano

Performance degradada:

Execute ANALYZE após grandes cargas
Crie índices nas colunas de filtro

Observações Importantes

🦆 DuckDB = Performance: Use para análises pesadas
🐘 PostgreSQL = Confiabilidade: Use para dados críticos
Backup regular: Copie o arquivo .duckdb semanalmente
Fechar conexões: Sempre use conn.close() com DuckDB
Um processo por vez: DuckDB não suporta escrita concorrente

Estrutura e Regras de Montagem das Tabelas
📊 1. RECEITA SALDO (PostgreSQL)
Campos da Tabela receitas.fato_receita_saldo
sql-- Campos principais (do Excel)
1. coexercicio (integer) - Ano do exercício
2. inmes (integer) - Mês (1-12)
3. coug (varchar(10)) - Código da UG
4. cocontacontabil (varchar(20)) - Conta contábil
5. cocontacorrente (varchar(50)) - Conta corrente (17 ou 38 chars)
6. intipoadm (integer) - Tipo de administração
7. vacredito (decimal(18,2)) - Valor crédito
8. vadebito (decimal(18,2)) - Valor débito

-- Campo calculado
9. saldo_contabil_receita (decimal(18,2)) - Calculado baseado no 1º dígito da conta:
   - Se conta começa com '5': saldo = vadebito - vacredito
   - Se conta começa com '6': saldo = vacredito - vadebito

-- Campos derivados do parse de COCONTACORRENTE
-- Para contas de 17 caracteres:
10. coclasseorc (varchar(8)) - chars 1-8 (Classificação orçamentária)
11. cofonte (varchar(10)) - chars 9-18 (Fonte de recursos)
12. cocategoriareceita (varchar(1)) - char 1 (Categoria)
13. cofontereceita (varchar(2)) - chars 1-2 (Fonte)
14. cosubfontereceita (varchar(3)) - chars 1-3 (Subfonte)
15. corubrica (varchar(4)) - chars 1-4 (Rubrica)
16. coalinea (varchar(6)) - chars 1-6 (Alínea)

-- Para contas de 38 caracteres:
17. inesfera (varchar(1)) - char 1 (Esfera: 1=Federal, 2=Estadual, 3=Municipal)
18. couo (varchar(5)) - chars 2-6 (Unidade orçamentária)
19. cofuncao (varchar(2)) - chars 7-8 (Função)
20. cosubfuncao (varchar(3)) - chars 9-11 (Subfunção)
21. coprograma (varchar(4)) - chars 12-15 (Programa)
22. coprojeto (varchar(4)) - chars 16-19 (Projeto/Atividade)
23. cosubtitulo (varchar(4)) - chars 20-23 (Subtítulo)
24. cofonte (varchar(10)) - chars 24-32 (Fonte - UNIFICADO com 17 chars)
25. conatureza (varchar(6)) - chars 33-38 (Natureza da despesa)
26. incategoria (varchar(1)) - char 33 (Categoria econômica)
27. cogrupo (varchar(1)) - char 34 (Grupo de despesa)
28. comodalidade (varchar(2)) - chars 35-36 (Modalidade)
29. coelemento (varchar(2)) - chars 37-38 (Elemento de despesa)

-- Campos de controle
30. periodo (varchar(7)) - Formato YYYY-MM
31. data_carga (timestamp) - Data/hora da carga
💰 2. DESPESA SALDO (PostgreSQL)
Campos da Tabela despesas.fato_despesa_saldo
sql-- Campos principais (do Excel)
1. coexercicio (integer) - Ano do exercício
2. coug (integer) - Código da UG
3. cogestao (integer) - Código de gestão
4. cocontacontabil (bigint) - Conta contábil
5. cocontacorrente (varchar(50)) - Conta corrente (38 ou 40 chars)
6. inmes (integer) - Mês (1-12)
7. inesfera (integer) - Esfera governamental
8. couo (integer) - Unidade orçamentária
9. cofuncao (integer) - Função
10. cosubfuncao (integer) - Subfunção
11. coprograma (integer) - Programa
12. coprojeto (integer) - Projeto/Atividade
13. cosubtitulo (integer) - Subtítulo
14. cofonte (bigint) - Fonte de recursos
15. conatureza (integer) - Natureza da despesa (6 dígitos)
16. incategoria (integer) - Categoria econômica
17. vacredito (decimal(18,2)) - Valor crédito
18. vadebito (decimal(18,2)) - Valor débito
19. noug (varchar(255)) - Nome da UG
20. cogestao_1 (integer) - Código de gestão (duplicado)
21. nogestao (varchar(255)) - Nome da gestão
22. intipoadm (integer) - Tipo de administração
23. instatus (integer) - Status
24. ultalteracao (varchar(50)) - Última alteração

-- Campo calculado
25. saldo_contabil_despesa (decimal(18,2)) - Calculado baseado no 1º dígito:
    - Se conta começa com '5': saldo = vadebito - vacredito
    - Se conta começa com '6': saldo = vacredito - vadebito

-- Campos derivados do parse de CONATUREZA (6 dígitos)
26. cogrupo (varchar(1)) - 2º dígito (Grupo de despesa)
27. comodalidade (varchar(2)) - 3º e 4º dígitos (Modalidade)
28. coelemento (varchar(2)) - 5º e 6º dígitos (Elemento)

-- Campo especial para contas de 40 chars
29. cosubelemento (varchar(2)) - chars 39-40 (Subelemento)

-- Campos de controle
30. periodo (varchar(7)) - Formato YYYY-MM
31. data_carga (timestamp) - Data/hora da carga
🦆 3. RECEITA LANÇAMENTO (DuckDB)
Campos da Tabela receita_lancamento
sql-- Campos principais (do Excel)
1. coexercicio (integer) - Ano do exercício
2. coug (integer) - Código da UG
3. cogestao (integer) - Código de gestão
4. nudocumento (varchar(20)) - Número do documento
5. nulancamento (integer) - Número do lançamento
6. coevento (integer) - Código do evento
7. cocontacontabil (varchar(20)) - Conta contábil
8. cocontacorrente (varchar(50)) - Conta corrente (17, 38 ou 40 chars)
9. inmes (integer) - Mês do lançamento
10. dalancamento (date) - Data do lançamento
11. valancamento (double) - Valor do lançamento
12. indebitocredito (varchar(1)) - Indicador D/C
13. inabreencerra (integer) - Indicador abre/encerra
14. cougdestino (integer) - UG destino
15. cogestaodestino (integer) - Gestão destino
16. datransacao (date) - Data da transação
17. hotransacao (varchar(10)) - Hora da transação
18. cougcontab (integer) - UG contábil (usado nos filtros)
19. cogestaocontab (integer) - Gestão contábil

-- Campo derivado
20. tipo_lancamento (varchar(10)) - Baseado em INDEBITOCREDITO:
    - 'D' → 'DEBITO'
    - 'C' → 'CREDITO'

-- Campos derivados do parse de COCONTACORRENTE
-- Para contas de 17 caracteres:
21. coclasseorc (varchar(8)) - chars 1-8
22. cofonte (varchar(10)) - chars 9-18
23. cocategoriareceita (varchar(1)) - char 1
24. cofontereceita (varchar(2)) - chars 1-2
25. cosubfontereceita (varchar(3)) - chars 1-3
26. corubrica (varchar(4)) - chars 1-4
27. coalinea (varchar(6)) - chars 1-6

-- Para contas de 38 ou 40 caracteres:
28. inesfera (varchar(1)) - char 1
29. couo (varchar(5)) - chars 2-6
30. cofuncao (varchar(2)) - chars 7-8
31. cosubfuncao (varchar(3)) - chars 9-11
32. coprograma (varchar(4)) - chars 12-15
33. coprojeto (varchar(4)) - chars 16-19
34. cosubtitulo (varchar(4)) - chars 20-23
35. cofonte (varchar(10)) - chars 24-32 (sobrescreve o de 17 chars)
36. conatureza (varchar(6)) - chars 33-38
37. incategoria (varchar(1)) - char 33
38. cogrupo (varchar(1)) - char 34
39. comodalidade (varchar(2)) - chars 35-36
40. coelemento (varchar(2)) - chars 37-38

-- Campo especial para contas de 40 chars
41. cosubelemento (varchar(2)) - chars 39-40

-- Campo de controle
42. periodo (varchar(7)) - Formato YYYY-MM
43. data_carga (timestamp default now()) - Data/hora da carga
🦆 4. DESPESA LANÇAMENTO (DuckDB)
Campos da Tabela despesa_lancamento
sql-- Campos principais (do Excel)
1. coexercicio (integer) - Ano do exercício
2. coug (integer) - Código da UG
3. cogestao (integer) - Código de gestão
4. nudocumento (varchar(20)) - Número do documento
5. nulancamento (integer) - Número do lançamento
6. coevento (integer) - Código do evento
7. cocontacontabil (varchar(20)) - Conta contábil
8. cocontacorrente (varchar(50)) - Conta corrente (38 ou 40 chars) - COM STRIP()!
9. inmes (integer) - Mês do lançamento
10. dalancamento (date) - Data do lançamento
11. valancamento (double) - Valor do lançamento
12. indebitocredito (varchar(1)) - Indicador D/C
13. inabreencerra (integer) - Indicador abre/encerra
14. cougdestino (integer) - UG destino
15. cogestaodestino (integer) - Gestão destino
16. datransacao (date) - Data da transação
17. hotransacao (varchar(10)) - Hora da transação
18. cougcontab (integer) - UG contábil (usado nos filtros)
19. cogestaocontab (integer) - Gestão contábil

-- Campo derivado
20. tipo_lancamento (varchar(10)) - Baseado em INDEBITOCREDITO:
    - 'D' → 'DEBITO'
    - 'C' → 'CREDITO'

-- Campos derivados do parse de COCONTACORRENTE
-- Para contas de 38 ou 40 caracteres (após strip):
21. inesfera (varchar(1)) - char 1
22. couo (varchar(5)) - chars 2-6
23. cofuncao (varchar(2)) - chars 7-8
24. cosubfuncao (varchar(3)) - chars 9-11
25. coprograma (varchar(4)) - chars 12-15
26. coprojeto (varchar(4)) - chars 16-19
27. cosubtitulo (varchar(4)) - chars 20-23
28. cofonte (varchar(10)) - chars 24-32
29. conatureza (varchar(6)) - chars 33-38
30. incategoria (varchar(1)) - char 33
31. cogrupo (varchar(1)) - char 34
32. comodalidade (varchar(2)) - chars 35-36
33. coelemento (varchar(2)) - chars 37-38

-- Campo especial para contas de 40 chars
34. cosubelemento (varchar(2)) - chars 39-40

-- Campo de controle
35. periodo (varchar(7)) - Formato YYYY-MM
36. data_carga (timestamp default now()) - Data/hora da carga
🔑 Diferenças Importantes
Entre Saldo e Lançamento:

Saldo: Agregado mensal por conta
Lançamento: Detalhe individual de cada operação
Volume: Lançamento tem ~100x mais registros

Entre Receita e Despesa:

Receita: Suporta contas de 17 chars (classificação orçamentária)
Despesa: Apenas 38/40 chars (natureza de despesa)
Strip(): Despesa faz strip() automático do COCONTACORRENTE

Entre PostgreSQL e DuckDB:

PostgreSQL: Usado para Saldos (menor volume)
DuckDB: Usado para Lançamentos (1.5M+ registros)
Performance: DuckDB é 10-100x mais rápido para análises

----

Como usar mensalmente:

Coloque os 4 arquivos Excel do mês na pasta dados_brutos/fato/:

DespesaLancamentoJulho.xlsx
DespesaSaldoJulho.xlsx
ReceitaLancamentoJulho.xlsx
ReceitaSaldoJulho.xlsx


Execute o comando:
bashpython scripts/carga_mensal_duckdb.py Julho

Após a carga, gere o relatório de conferência:
bashpython scripts/relatorio_conferencia_duckdb.py


O script unificado carga_mensal_duckdb.py irá processar os 4 arquivos automaticamente, verificando se os períodos já existem e perguntando se deseja sobrescrever.