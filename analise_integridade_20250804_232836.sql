-- Script de análise dos problemas de integridade
-- Gerado em: 04/08/2025 23:28:36


-- Análise: despesa_saldo.incategoria -> dim_categoria_despesa
------------------------------------------------------------
-- Valores órfãos (total: 4)
SELECT DISTINCT f.incategoria, COUNT(*) as qtd
FROM despesa_saldo f
LEFT JOIN dim_categoria_despesa d ON f.incategoria = d.incategoria
WHERE f.incategoria IS NOT NULL
AND d.incategoria IS NULL
GROUP BY f.incategoria
ORDER BY COUNT(*) DESC;

-- Exemplos de registros afetados
SELECT *
FROM despesa_saldo f
WHERE f.incategoria IN (
    SELECT DISTINCT f2.incategoria
    FROM despesa_saldo f2
    LEFT JOIN dim_categoria_despesa d ON f2.incategoria = d.incategoria
    WHERE f2.incategoria IS NOT NULL
    AND d.incategoria IS NULL
)
LIMIT 10;


-- Análise: receita_lancamento.coevento -> dim_evento
------------------------------------------------------------
-- Valores órfãos (total: 2)
SELECT DISTINCT f.coevento, COUNT(*) as qtd
FROM receita_lancamento f
LEFT JOIN dim_evento d ON f.coevento = d.coevento
WHERE f.coevento IS NOT NULL
AND d.coevento IS NULL
GROUP BY f.coevento
ORDER BY COUNT(*) DESC;

-- Exemplos de registros afetados
SELECT *
FROM receita_lancamento f
WHERE f.coevento IN (
    SELECT DISTINCT f2.coevento
    FROM receita_lancamento f2
    LEFT JOIN dim_evento d ON f2.coevento = d.coevento
    WHERE f2.coevento IS NOT NULL
    AND d.coevento IS NULL
)
LIMIT 10;


-- Análise: receita_lancamento.cocontacontabil -> dim_conta_contabil
------------------------------------------------------------
-- Valores órfãos (total: 2)
SELECT DISTINCT f.cocontacontabil, COUNT(*) as qtd
FROM receita_lancamento f
LEFT JOIN dim_conta_contabil d ON f.cocontacontabil = d.cocontacontabil
WHERE f.cocontacontabil IS NOT NULL
AND d.cocontacontabil IS NULL
GROUP BY f.cocontacontabil
ORDER BY COUNT(*) DESC;

-- Exemplos de registros afetados
SELECT *
FROM receita_lancamento f
WHERE f.cocontacontabil IN (
    SELECT DISTINCT f2.cocontacontabil
    FROM receita_lancamento f2
    LEFT JOIN dim_conta_contabil d ON f2.cocontacontabil = d.cocontacontabil
    WHERE f2.cocontacontabil IS NOT NULL
    AND d.cocontacontabil IS NULL
)
LIMIT 10;


-- Análise: receita_saldo.cocontacontabil -> dim_conta_contabil
------------------------------------------------------------
-- Valores órfãos (total: 2)
SELECT DISTINCT f.cocontacontabil, COUNT(*) as qtd
FROM receita_saldo f
LEFT JOIN dim_conta_contabil d ON f.cocontacontabil = d.cocontacontabil
WHERE f.cocontacontabil IS NOT NULL
AND d.cocontacontabil IS NULL
GROUP BY f.cocontacontabil
ORDER BY COUNT(*) DESC;

-- Exemplos de registros afetados
SELECT *
FROM receita_saldo f
WHERE f.cocontacontabil IN (
    SELECT DISTINCT f2.cocontacontabil
    FROM receita_saldo f2
    LEFT JOIN dim_conta_contabil d ON f2.cocontacontabil = d.cocontacontabil
    WHERE f2.cocontacontabil IS NOT NULL
    AND d.cocontacontabil IS NULL
)
LIMIT 10;

