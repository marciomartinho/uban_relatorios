# Regras de Negócio - RREO Demonstrativo de Receitas

## 1. Visão Geral

O Relatório Resumido da Execução Orçamentária (RREO) - Demonstrativo de Receitas é um relatório bimestral obrigatório que apresenta a execução das receitas públicas do Distrito Federal, comparando valores previstos com valores realizados.

## 2. Estrutura do Relatório

### 2.1 Períodos e Bimestres

O relatório é gerado por bimestre:
- **1º Bimestre**: Janeiro e Fevereiro
- **2º Bimestre**: Março e Abril  
- **3º Bimestre**: Maio e Junho
- **4º Bimestre**: Julho e Agosto
- **5º Bimestre**: Setembro e Outubro
- **6º Bimestre**: Novembro e Dezembro

### 2.2 Colunas do Demonstrativo

1. **RECEITAS**: Descrição da receita
2. **PREVISÃO INICIAL**: Valor originalmente previsto na LOA
3. **PREVISÃO ATUALIZADA (a)**: Valor previsto após atualizações
4. **NO BIMESTRE (b)**: Valores realizados apenas no bimestre selecionado
   - R$: Valor em reais
   - %: Percentual sobre a previsão atualizada
5. **ATÉ O BIMESTRE (c)**: Valores realizados acumulados do início do ano até o bimestre
   - R$: Valor em reais
   - %: Percentual sobre a previsão atualizada
6. **SALDO (a-c)**: Diferença entre previsão atualizada e realizado até o bimestre

## 3. Classificação das Receitas

### 3.1 Grupos Principais

1. **RECEITAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)**
   - Receitas Correntes
   - Receitas de Capital

2. **RECEITAS (INTRA-ORÇAMENTÁRIAS) (II)**
   - Receitas Correntes - Intra-Orçamentárias
   - Receitas de Capital - Intra-Orçamentárias

3. **SALDOS DE EXERCÍCIOS ANTERIORES**
   - Recursos Arrecadados em Exercícios Anteriores - RPPS
   - Superávit Financeiro Utilizado para Créditos Adicionais

### 3.2 Códigos de Fonte de Receita

#### Receitas Correntes (Exceto Intra)
- **11 a 19**: Todas as receitas correntes regulares

#### Receitas de Capital (Exceto Intra)
- **21 a 29**: Todas as receitas de capital regulares

#### Receitas Intra-Orçamentárias Correntes
- **71 a 79**: Receitas correntes intra-orçamentárias

#### Receitas Intra-Orçamentárias de Capital
- **81 a 89**: Receitas de capital intra-orçamentárias

## 4. Regras de Cálculo

### 4.1 Identificação das Contas Contábeis

#### Previsão Inicial
- **Contas**: 521100000 a 521199999
- **Período**: Valores acumulados até o último mês do bimestre selecionado

#### Previsão Atualizada
- **Contas**: 521100000 a 521299999
- **Período**: Valores acumulados até o último mês do bimestre selecionado

#### Receita Realizada
- **Contas**: 621200000 a 621399999
- **Período**: 
  - "No Bimestre": Soma apenas dos meses do bimestre selecionado
  - "Até o Bimestre": Soma acumulada do mês 1 até o último mês do bimestre

### 4.2 Saldos de Exercícios Anteriores

#### Recursos Arrecadados em Exercícios Anteriores - RPPS
- Usa as mesmas contas contábeis das receitas regulares
- **Filtro adicional**: `cocontacorrente LIKE '99%'`
- Aplica-se a todas as colunas (previsão inicial, atualizada, realizado)
- **Observação**: Se a coluna `cocontacorrente` não existir na tabela, retorna valores zerados

#### Superávit Financeiro Utilizado para Créditos Adicionais
- **Contas**: 522130100 a 522130199
- **Características especiais**:
  - Não tem previsão inicial (sempre zero)
  - Não tem realizado no bimestre (sempre zero)
  - O valor aparece apenas em "Previsão Atualizada" e "Realizado até o Bimestre" (mesmo valor)

#### Regras de Exibição
- A seção "SALDOS DE EXERCÍCIOS ANTERIORES" só aparece se houver algum valor diferente de zero
- As linhas filhas (Recursos RPPS e Superávit) só aparecem se tiverem valores
- Aparecem após a linha "TOTAL (V) = (III + IV)"

### 4.3 Fórmulas

1. **Percentual No Bimestre**:
   ```
   % = (Realizado no Bimestre / Previsão Atualizada) × 100
   ```

2. **Percentual Até o Bimestre**:
   ```
   % = (Realizado até o Bimestre / Previsão Atualizada) × 100
   ```

3. **Saldo**:
   ```
   Saldo = Previsão Atualizada - Realizado até o Bimestre
   ```

4. **Totalizações**:
   - Total Receitas Exceto Intra (I) = Soma(Receitas Correntes + Receitas de Capital)
   - Total Receitas Intra (II) = Soma(Receitas Correntes Intra + Receitas de Capital Intra)
   - Total das Receitas (III) = (I) + (II)
   - Déficit (IV) = 0 (sempre zerado neste demonstrativo)
   - Total (V) = (III) + (IV)

## 5. Regras de Apresentação

### 5.1 Hierarquia Visual

1. **Nível 1** - Títulos principais (negrito, fundo azul claro - mesma cor dos totais)
   - RECEITAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)
   - RECEITAS (INTRA-ORÇAMENTÁRIAS) (II)

2. **Nível 2** - Categorias (negrito, fundo cinza)
   - RECEITAS CORRENTES
   - RECEITAS DE CAPITAL

3. **Nível 3** - Fontes de receita (semi-negrito, indentado 20px)
   - Ex: Impostos, Taxas e Contribuições de Melhoria
   - **Regra especial**: Quando houver apenas uma subfonte, exibir apenas o nível 3 com os valores da subfonte

4. **Nível 4** - Subfontes/Espécies (itálico, indentado 40px)
   - Ex: Impostos
   - **Só aparece quando há múltiplas subfontes dentro de uma fonte**

### 5.2 Formatação de Valores

- **Valores monetários**: 
  - Formato: 999.999.999,99
  - Negativos: (999.999,99) em vermelho
  - Zeros: 0,00 em cinza itálico

- **Percentuais**:
  - Formato: 99,99
  - Zeros: mostrar "-"

### 5.3 Filtros de Exibição

- Só exibir linhas onde pelo menos um dos seguintes valores seja diferente de zero:
  - Previsão Inicial
  - Previsão Atualizada
  - Realizado no Bimestre
  - Realizado até o Bimestre

## 6. Fonte de Dados

### 6.1 Tabelas Utilizadas

1. **receita_saldo**: Tabela principal com os saldos contábeis
   - coexercicio: Ano do exercício
   - inmes: Mês de referência
   - cofontereceita: Código da fonte de receita
   - cosubfontereceita: Código da subfonte/espécie
   - cocontacontabil: Código da conta contábil
   - saldo_contabil_receita: Valor do saldo

2. **dim_receita_origem**: Dimensão com nomes das fontes
   - cofontereceita: Código da fonte
   - nofontereceita: Nome da fonte

3. **dim_receita_especie**: Dimensão com nomes das subfontes
   - cosubfontereceita: Código da subfonte
   - nosubfontereceita: Nome da subfonte

### 6.2 Agrupamento de Dados

Os dados são agrupados por:
1. Código da fonte de receita (cofontereceita)
2. Código da subfonte de receita (cosubfontereceita)

E então somados conforme as regras de conta contábil e período.

### 6.3 Tratamento de Ausência de Colunas

Se a coluna `cocontacorrente` não existir na tabela `receita_saldo`:
- A query de Recursos RPPS retornará valores zerados
- O sistema continuará funcionando normalmente
- Um aviso será registrado nos logs do servidor

## 7. Validações e Consistências

1. **Validação de Parâmetros**:
   - Ano e bimestre são obrigatórios
   - Bimestre deve estar entre 1 e 6

2. **Consistência de Dados**:
   - Saldo nunca pode ser negativo se a previsão for positiva
   - Percentuais não podem exceder limites razoáveis (ex: 999%)

3. **Tratamento de Nulos**:
   - Valores nulos são tratados como zero
   - Nomes ausentes nas dimensões mostram "Fonte/Subfonte + código"

## 8. Exportação e Impressão

### 8.1 Exportação para Excel (CSV)
- Separador: ponto e vírgula (;)
- Encoding: UTF-8 com BOM
- Mantém hierarquia através de indentação com espaços

### 8.2 Impressão
- Remove elementos de navegação e filtros
- Mantém apenas o demonstrativo
- Ajusta larguras para caber em página A4 paisagem