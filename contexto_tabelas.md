# Documentação - Estrutura das Tabelas DESPESA no DuckDB

## 📅 Data da Documentação
- **Data**: 05 de Agosto de 2025
- **Banco**: dados_brutos/fato/db_local/uban.duckdb

## 🗂️ Organização dos Arquivos

### Scripts de ETL e Carga:
```
scripts/
├── 01_load_despesa_saldo.py
├── 02_visualizar_tabela_despesa_saldo.py
├── 03_load_despesa_lancamento.py
└── 04_visualizar_tabela_despesa_lancamento.py

modules/
├── 01_etl_despesa_saldo_duckdb.py
└── 02_etl_despesa_lancamento_duckdb.py
```

---

## 💰 1. DESPESA_SALDO

### 📊 Estrutura da Tabela - 24 campos totais:

#### Campos do Excel (17 campos):
1. `coexercicio` (INTEGER) - Ano do exercício
2. `coug` (INTEGER) - Código da UG
3. `cogestao` (INTEGER) - Código de gestão
4. `cocontacontabil` (BIGINT) - Conta contábil
5. `cocontacorrente` (VARCHAR(50)) - Conta corrente (11, 38 ou 40 chars)
6. `inmes` (INTEGER) - Mês (1-12)
7. `inesfera` (INTEGER) - Esfera governamental
8. `couo` (INTEGER) - Unidade orçamentária
9. `cofuncao` (INTEGER) - Função
10. `cosubfuncao` (INTEGER) - Subfunção
11. `coprograma` (INTEGER) - Programa
12. `coprojeto` (INTEGER) - Projeto/Atividade
13. `cosubtitulo` (INTEGER) - Subtítulo
14. `cofonte` (BIGINT) - Fonte de recursos
15. `conatureza` (INTEGER) - Natureza da despesa (6 dígitos)
16. `vacredito` (DECIMAL(18,2)) - Valor crédito
17. `vadebito` (DECIMAL(18,2)) - Valor débito

#### Campos Calculados (7 campos):
18. `saldo_contabil_despesa` (DECIMAL(18,2)) - Calculado baseado no 1º dígito:
    - Se conta começa com '5': saldo = vadebito - vacredito
    - Se conta começa com '6': saldo = vacredito - vadebito
19. `incategoria` (VARCHAR(1)) - 1º dígito de CONATUREZA
20. `cogrupo` (VARCHAR(1)) - 2º dígito de CONATUREZA
21. `comodalidade` (VARCHAR(2)) - 3º e 4º dígitos de CONATUREZA
22. `coelemento` (VARCHAR(2)) - 5º e 6º dígitos de CONATUREZA
23. `cosubelemento` (VARCHAR(2)) - Chars 39-40 de COCONTACORRENTE (apenas contas 40 chars)
24. `periodo` (VARCHAR(7)) - Formato YYYY-MM

### 🚀 Comandos de Uso:
```bash
# Primeira carga (recria tabela)
python scripts/01_load_despesa_saldo.py DespesaSaldoJulho.xlsx --recriar

# Cargas incrementais
python scripts/01_load_despesa_saldo.py DespesaSaldoAgosto.xlsx

# Visualizar dados
python scripts/02_visualizar_tabela_despesa_saldo.py
```

### ⚠️ Mudanças Recentes (05/08/2025):
- Removidas colunas: NOUG, COGESTAO_1, NOGESTAO, INTIPOADM, INSTATUS, ULTALTERACAO
- Parse de CONATUREZA ajustado para 6 dígitos
- Adicionada opção --recriar no script de carga

---

## 📝 2. DESPESA_LANCAMENTO

### 📊 Estrutura da Tabela - 35 campos totais:

#### Campos do Excel (19 campos principais):
1. `coexercicio` (INTEGER) - Ano do exercício
2. `coug` (INTEGER) - Código da UG
3. `cogestao` (INTEGER) - Código de gestão
4. `nudocumento` (VARCHAR) - Número do documento
5. `nulancamento` (INTEGER) - Número do lançamento
6. `coevento` (INTEGER) - Código do evento
7. `cocontacontabil` (VARCHAR) - Conta contábil
8. `cocontacorrente` (VARCHAR) - Conta corrente (38 ou 40 chars)
9. `inmes` (INTEGER) - Mês (1-12)
10. `dalancamento` (DATE) - Data do lançamento
11. `valancamento` (DECIMAL(18,2)) - Valor do lançamento
12. `indebitocredito` (VARCHAR) - Indicador D/C
13. `inabreencerra` (INTEGER) - Indicador abre/encerra
14. `cougdestino` (INTEGER) - UG destino
15. `cogestaodestino` (INTEGER) - Gestão destino
16. `datransacao` (DATE) - Data da transação
17. `hotransacao` (VARCHAR) - Hora da transação
18. `cougcontab` (INTEGER) - UG contábil
19. `cogestaocontab` (INTEGER) - Gestão contábil

#### Campos Calculados/Parseados (16 campos):
20. `tipo_lancamento` (VARCHAR) - DEBITO/CREDITO (baseado em indebitocredito)
21. `periodo` (VARCHAR(7)) - Formato YYYY-MM
22. `inesfera` (VARCHAR) - Parse de COCONTACORRENTE[0:1]
23. `couo` (VARCHAR) - Parse de COCONTACORRENTE[1:6]
24. `cofuncao` (VARCHAR) - Parse de COCONTACORRENTE[6:8]
25. `cosubfuncao` (VARCHAR) - Parse de COCONTACORRENTE[8:11]
26. `coprograma` (VARCHAR) - Parse de COCONTACORRENTE[11:15]
27. `coprojeto` (VARCHAR) - Parse de COCONTACORRENTE[15:19]
28. `cosubtitulo` (VARCHAR) - Parse de COCONTACORRENTE[19:23]
29. `cofonte` (VARCHAR) - Parse de COCONTACORRENTE[23:32]
30. `conatureza` (VARCHAR) - Parse de COCONTACORRENTE[32:38]
31. `incategoria` (VARCHAR) - Parse de COCONTACORRENTE[32:33]
32. `cogrupo` (VARCHAR) - Parse de COCONTACORRENTE[33:34]
33. `comodalidade` (VARCHAR) - Parse de COCONTACORRENTE[34:36]
34. `coelemento` (VARCHAR) - Parse de COCONTACORRENTE[36:38]
35. `cosubelemento` (VARCHAR) - Parse de COCONTACORRENTE[38:40] (apenas contas 40 chars)

### 🚀 Comandos de Uso:
```bash
# Carga inicial ou sobrescrever período
python scripts/03_load_despesa_lancamento.py DespesaLancamentoJulho.xlsx

# Cargas incrementais (pergunta se quer sobrescrever se período existe)
python scripts/03_load_despesa_lancamento.py DespesaLancamentoAgosto.xlsx

# Visualizar dados
python scripts/04_visualizar_tabela_despesa_lancamento.py
```

### 📋 Características:
- Parse de COCONTACORRENTE para contas de 38 e 40 caracteres
- Não tem opção --recriar (tabela criada na migração inicial)
- Suporta sobrescrita de períodos existentes
- Chunks de 50.000 registros para melhor performance

---

# Documentação - Estrutura das Tabelas RECEITA no DuckDB

## 📅 Data da Documentação
- **Data**: 05 de Agosto de 2025
- **Banco**: dados_brutos/fato/db_local/lancamentos.duckdb

## 🗂️ Organização dos Arquivos

### Scripts de ETL e Carga:
```
scripts/
├── 05_load_receita_saldo.py
├── 06_visualizar_tabela_receita_saldo.py
├── 07_load_receita_lancamento.py
└── 08_visualizar_tabela_receita_lancamento.py

modules/
├── 03_etl_receita_saldo_duckdb.py
└── 04_etl_receita_lancamento_duckdb.py
```

---

## 💵 3. RECEITA_SALDO

### 📊 Estrutura da Tabela - 29 campos totais:

#### Campos do Excel (8 campos):
1. `coexercicio` (INTEGER) - Ano do exercício
2. `inmes` (INTEGER) - Mês (1-12)
3. `coug` (VARCHAR) - Código da UG
4. `cocontacontabil` (VARCHAR) - Conta contábil
5. `cocontacorrente` (VARCHAR) - Conta corrente (17 ou 38 chars)
6. `intipoadm` (INTEGER) - Tipo de administração
7. `vacredito` (DECIMAL(18,2)) - Valor crédito
8. `vadebito` (DECIMAL(18,2)) - Valor débito

#### Campos Calculados (21 campos):
9. `saldo_contabil_receita` (DECIMAL(18,2)) - Calculado baseado no 1º dígito:
    - Se conta começa com '5': saldo = vadebito - vacredito
    - Senão: saldo = vacredito - vadebito
10. `periodo` (VARCHAR(7)) - Formato YYYY-MM
11. `coclasseorc` (VARCHAR) - Chars 0-8 de COCONTACORRENTE (contas 17 chars)
12. `cofonte` (VARCHAR) - Chars 8-18 de COCONTACORRENTE (contas 17 chars) ou chars 23-32 (contas 38 chars)
13. `cocategoriareceita` (VARCHAR) - Char 0 de COCONTACORRENTE (contas 17 chars)
14. `cofontereceita` (VARCHAR) - Chars 0-2 de COCONTACORRENTE (contas 17 chars)
15. `cosubfontereceita` (VARCHAR) - Chars 0-3 de COCONTACORRENTE (contas 17 chars)
16. `corubrica` (VARCHAR) - Chars 0-4 de COCONTACORRENTE (contas 17 chars)
17. `coalinea` (VARCHAR) - Chars 0-6 de COCONTACORRENTE (contas 17 chars)
18. `inesfera` (VARCHAR) - Char 0 de COCONTACORRENTE (contas 38 chars)
19. `couo` (VARCHAR) - Chars 1-6 de COCONTACORRENTE (contas 38 chars)
20. `cofuncao` (VARCHAR) - Chars 6-8 de COCONTACORRENTE (contas 38 chars)
21. `cosubfuncao` (VARCHAR) - Chars 8-11 de COCONTACORRENTE (contas 38 chars)
22. `coprograma` (VARCHAR) - Chars 11-15 de COCONTACORRENTE (contas 38 chars)
23. `coprojeto` (VARCHAR) - Chars 15-19 de COCONTACORRENTE (contas 38 chars)
24. `cosubtitulo` (VARCHAR) - Chars 19-23 de COCONTACORRENTE (contas 38 chars)
25. `conatureza` (VARCHAR) - Chars 32-38 de COCONTACORRENTE (contas 38 chars)
26. `incategoria` (VARCHAR) - Char 32 de COCONTACORRENTE (contas 38 chars)
27. `cogrupo` (VARCHAR) - Char 33 de COCONTACORRENTE (contas 38 chars)
28. `comodalidade` (VARCHAR) - Chars 34-36 de COCONTACORRENTE (contas 38 chars)
29. `coelemento` (VARCHAR) - Chars 36-38 de COCONTACORRENTE (contas 38 chars)

### 🚀 Comandos de Uso:
```bash
# Carga inicial ou incremental
python scripts/05_load_receita_saldo.py ReceitaSaldoJulho.xlsx

# Cargas incrementais (pergunta se quer sobrescrever se período existe)
python scripts/05_load_receita_saldo.py ReceitaSaldoAgosto.xlsx

# Visualizar dados
python scripts/06_visualizar_tabela_receita_saldo.py
```

### 📋 Características:
- Parse diferenciado para contas de 17 caracteres (classificação orçamentária) e 38 caracteres (execução)
- Suporta sobrescrita de períodos existentes
- Chunks de 5.000 registros para melhor performance
- Validação de períodos antes da carga

---

## 📝 4. RECEITA_LANCAMENTO

### 📊 Estrutura da Tabela - 40 campos totais:

#### Campos do Excel (19 campos principais):
1. `coexercicio` (INTEGER) - Ano do exercício
2. `coug` (INTEGER) - Código da UG
3. `cogestao` (INTEGER) - Código de gestão
4. `nudocumento` (VARCHAR) - Número do documento
5. `nulancamento` (INTEGER) - Número do lançamento
6. `coevento` (INTEGER) - Código do evento
7. `cocontacontabil` (VARCHAR) - Conta contábil
8. `cocontacorrente` (VARCHAR) - Conta corrente (17, 38 ou 40 chars)
9. `inmes` (INTEGER) - Mês (1-12)
10. `dalancamento` (DATE) - Data do lançamento
11. `valancamento` (DECIMAL(18,2)) - Valor do lançamento
12. `indebitocredito` (VARCHAR) - Indicador D/C
13. `inabreencerra` (INTEGER) - Indicador abre/encerra
14. `cougdestino` (INTEGER) - UG destino
15. `cogestaodestino` (INTEGER) - Gestão destino
16. `datransacao` (DATE) - Data da transação
17. `hotransacao` (VARCHAR) - Hora da transação
18. `cougcontab` (INTEGER) - UG contábil
19. `cogestaocontab` (INTEGER) - Gestão contábil

#### Campos Calculados/Parseados (21 campos):
20. `tipo_lancamento` (VARCHAR) - DEBITO/CREDITO (baseado em indebitocredito)
21. `periodo` (VARCHAR(7)) - Formato YYYY-MM
22. `coclasseorc` (VARCHAR) - Chars 0-8 de COCONTACORRENTE (contas 17 chars)
23. `cofonte` (VARCHAR) - Chars 8-18 (contas 17) ou 23-32 (contas 38/40)
24. `cocategoriareceita` (VARCHAR) - Char 0 de COCONTACORRENTE (contas 17 chars)
25. `cofontereceita` (VARCHAR) - Chars 0-2 de COCONTACORRENTE (contas 17 chars)
26. `cosubfontereceita` (VARCHAR) - Chars 0-3 de COCONTACORRENTE (contas 17 chars)
27. `corubrica` (VARCHAR) - Chars 0-4 de COCONTACORRENTE (contas 17 chars)
28. `coalinea` (VARCHAR) - Chars 0-6 de COCONTACORRENTE (contas 17 chars)
29. `inesfera` (VARCHAR) - Char 0 de COCONTACORRENTE (contas 38/40 chars)
30. `couo` (VARCHAR) - Chars 1-6 de COCONTACORRENTE (contas 38/40 chars)
31. `cofuncao` (VARCHAR) - Chars 6-8 de COCONTACORRENTE (contas 38/40 chars)
32. `cosubfuncao` (VARCHAR) - Chars 8-11 de COCONTACORRENTE (contas 38/40 chars)
33. `coprograma` (VARCHAR) - Chars 11-15 de COCONTACORRENTE (contas 38/40 chars)
34. `coprojeto` (VARCHAR) - Chars 15-19 de COCONTACORRENTE (contas 38/40 chars)
35. `cosubtitulo` (VARCHAR) - Chars 19-23 de COCONTACORRENTE (contas 38/40 chars)
36. `conatureza` (VARCHAR) - Chars 32-38 de COCONTACORRENTE (contas 38/40 chars)
37. `incategoria` (VARCHAR) - Char 32 de COCONTACORRENTE (contas 38/40 chars)
38. `cogrupo` (VARCHAR) - Char 33 de COCONTACORRENTE (contas 38/40 chars)
39. `comodalidade` (VARCHAR) - Chars 34-36 de COCONTACORRENTE (contas 38/40 chars)
40. `coelemento` (VARCHAR) - Chars 36-38 de COCONTACORRENTE (contas 38/40 chars)
41. `cosubelemento` (VARCHAR) - Chars 38-40 de COCONTACORRENTE (apenas contas 40 chars)

### 🚀 Comandos de Uso:
```bash
# Carga inicial ou sobrescrever período
python scripts/07_load_receita_lancamento.py ReceitaLancamentoJulho.xlsx

# Cargas incrementais (pergunta se quer sobrescrever se período existe)
python scripts/07_load_receita_lancamento.py ReceitaLancamentoAgosto.xlsx

# Visualizar dados
python scripts/08_visualizar_tabela_receita_lancamento.py
```

### 📋 Características:
- Parse de COCONTACORRENTE para contas de 17, 38 e 40 caracteres
- Herda estrutura base da classe ETLLancamentoDuckDB
- Suporta sobrescrita de períodos existentes
- Chunks de 10.000 registros para melhor performance

---

## 🔍 Integridade Referencial

### Relacionamentos Comuns:
- `coug` → `dim_unidade_gestora`
- `cogestao` → `dim_gestao`
- `coevento` → `dim_evento` (apenas lançamento)
- `cocontacontabil` → `dim_conta_contabil`

### Relacionamentos Específicos de Despesa:
- `cofuncao` → `dim_funcao`
- `cosubfuncao` → `dim_subfuncao`
- `coprograma` → `dim_programa`
- `coprojeto` → `dim_projeto`
- `cosubtitulo` → `dim_subtitulo`
- `cofonte` → `dim_fonte`
- `incategoria` → `dim_categoria_despesa`
- `cogrupo` → `dim_grupo_despesa`
- `comodalidade` → `dim_modalidade`
- `coelemento` → `dim_elemento`

### Relacionamentos Específicos de Receita:
- `coclasseorc` → `dim_classificacao_orcamentaria`
- `cocategoriareceita` → `dim_categoria_receita`
- `cofontereceita` → `dim_fonte_receita`
- `cosubfontereceita` → `dim_subfonte_receita`
- `corubrica` → `dim_rubrica`
- `coalinea` → `dim_alinea`

## 📝 Validações Recomendadas

Após qualquer carga:
```bash
# Verificar integridade referencial
python scripts/verificar_integridade_duckdb.py

# Gerar relatório de conferência
python scripts/relatorio_conferencia_duckdb.py
```

---
*Documento para preservar o contexto da estrutura das tabelas de despesa e receita no DuckDB*