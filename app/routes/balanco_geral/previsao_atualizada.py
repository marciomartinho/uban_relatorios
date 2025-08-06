"""
API para o quadro Previsão Atualizada
Parte do Balanço Geral GDF
Compara Previsão Inicial (521100000-521199999) com Previsão Atualizada (521100000-521299999)
"""
from flask import Blueprint, jsonify
from app.db_manager import db_manager
from datetime import datetime
import traceback

# Criar blueprint
previsao_atualizada_api = Blueprint('previsao_atualizada_api', __name__)

@previsao_atualizada_api.route('/api/dados-previsao-atualizada')
def get_dados_previsao_atualizada():
    """Retorna os dados da previsão atualizada de forma dinâmica"""
    try:
        # 1. Obter ano mais recente
        ano_query = """
        SELECT DISTINCT coexercicio 
        FROM receita_saldo 
        WHERE coexercicio >= 2024
        ORDER BY coexercicio DESC
        LIMIT 1
        """
        ano_result = db_manager.execute_query(ano_query)
        
        if not ano_result:
            return jsonify({'erro': 'Nenhum dado encontrado para o ano especificado.'}), 400
        
        ano_atual = ano_result[0]['coexercicio']
        
        # 2. Query SQL Dinâmica para buscar previsões inicial e atualizada
        query = """
        WITH dados_agregados AS (
            SELECT
                rs.cocategoriareceita,
                SUBSTRING(rs.cofontereceita, 1, 2) as fonte_principal,
                -- Previsão Inicial: contas entre 521100000 e 521199999
                SUM(CASE
                    WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521199999'
                    THEN rs.saldo_contabil_receita
                    ELSE 0
                END) as previsao_inicial,
                -- Previsão Atualizada: contas entre 521100000 e 521299999
                SUM(CASE
                    WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521299999'
                    THEN rs.saldo_contabil_receita
                    ELSE 0
                END) as previsao_atualizada
            FROM receita_saldo rs
            WHERE
                rs.coexercicio = ?
            GROUP BY
                rs.cocategoriareceita,
                SUBSTRING(rs.cofontereceita, 1, 2)
        )
        SELECT
            da.cocategoriareceita,
            COALESCE(drc.nocategoriareceita, CONCAT('Categoria ', da.cocategoriareceita)) as nocategoriareceita,
            da.fonte_principal,
            COALESCE(dro.nofontereceita, CONCAT('Fonte ', da.fonte_principal)) as nofontereceita,
            da.previsao_inicial,
            da.previsao_atualizada
        FROM
            dados_agregados da
        LEFT JOIN
            DIM_RECEITA_CATEGORIA drc ON CAST(da.cocategoriareceita AS BIGINT) = drc.cocategoriareceita
        LEFT JOIN
            DIM_RECEITA_ORIGEM dro ON CAST(da.fonte_principal AS BIGINT) = dro.cofontereceita
        WHERE
            (da.previsao_inicial != 0 OR da.previsao_atualizada != 0)
        ORDER BY
            da.cocategoriareceita, da.fonte_principal
        """
        
        params = [ano_atual]
        resultados = db_manager.execute_query(query, params)
        
        # 3. Processar resultados seguindo a mesma lógica do receita_estimada
        dados = processar_dados_previsao_dinamico(resultados)
        
        return jsonify({
            'ano': ano_atual,
            'dados': dados,
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        print(f"Erro em get_dados_previsao_atualizada: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def processar_dados_previsao_dinamico(resultados):
    """
    Processa os resultados da query em estrutura hierárquica de forma dinâmica,
    seguindo exatamente o mesmo padrão do receita_estimada.py
    """
    dados_por_categoria = {}

    # Etapa 1: Agrupar os dados lidos do banco em uma estrutura aninhada
    for row in resultados:
        cat_id = row['cocategoriareceita']
        cat_nome = row['nocategoriareceita']
        fonte_id = row['fonte_principal']
        fonte_nome = row['nofontereceita']
        previsao_inicial = float(row['previsao_inicial'] or 0)
        previsao_atualizada = float(row['previsao_atualizada'] or 0)

        # Cria a entrada da categoria se for a primeira vez que ela aparece
        if cat_id not in dados_por_categoria:
            dados_por_categoria[cat_id] = {
                'nome': cat_nome,
                'fontes': {},
                'total_inicial': 0,
                'total_atualizada': 0
            }

        # Cria a entrada da fonte dentro da categoria se for a primeira vez
        if fonte_id not in dados_por_categoria[cat_id]['fontes']:
            dados_por_categoria[cat_id]['fontes'][fonte_id] = {
                'nome': fonte_nome,
                'previsao_inicial': 0,
                'previsao_atualizada': 0
            }

        # Acumula os valores na estrutura
        dados_por_categoria[cat_id]['fontes'][fonte_id]['previsao_inicial'] += previsao_inicial
        dados_por_categoria[cat_id]['fontes'][fonte_id]['previsao_atualizada'] += previsao_atualizada
        dados_por_categoria[cat_id]['total_inicial'] += previsao_inicial
        dados_por_categoria[cat_id]['total_atualizada'] += previsao_atualizada

    # Etapa 2: Calcular totais gerais
    total_geral_inicial = sum(cat['total_inicial'] for cat in dados_por_categoria.values())
    total_geral_atualizada = sum(cat['total_atualizada'] for cat in dados_por_categoria.values())

    dados_finais = []
    
    # Itera sobre as categorias que foram encontradas dinamicamente
    for cat_id, cat_data in sorted(dados_por_categoria.items()):
        categoria = {
            'tipo': 'categoria',
            'nome': cat_data['nome'],
            'previsao_inicial': cat_data['total_inicial'],
            'previsao_atualizada': cat_data['total_atualizada'],
            'variacao': calcular_variacao_percentual(cat_data['total_atualizada'], cat_data['total_inicial']),
            'fontes': []
        }

        # Itera sobre as fontes encontradas para cada categoria
        for fonte_id, fonte_data in sorted(cat_data['fontes'].items()):
            fonte = {
                'tipo': 'fonte',
                'nome': fonte_data['nome'],
                'previsao_inicial': fonte_data['previsao_inicial'],
                'previsao_atualizada': fonte_data['previsao_atualizada'],
                'variacao': calcular_variacao_percentual(fonte_data['previsao_atualizada'], fonte_data['previsao_inicial'])
            }
            categoria['fontes'].append(fonte)
        
        dados_finais.append(categoria)

    # Adicionar a linha de total ao final
    dados_finais.append({
        'tipo': 'total',
        'nome': 'RECEITA LÍQUIDA',
        'previsao_inicial': total_geral_inicial,
        'previsao_atualizada': total_geral_atualizada,
        'variacao': calcular_variacao_percentual(total_geral_atualizada, total_geral_inicial)
    })

    return dados_finais

def calcular_variacao_percentual(valor_atual, valor_anterior):
    """Calcula a variação percentual entre dois valores"""
    if valor_anterior == 0:
        return 100.0 if valor_atual > 0 else 0.0
    return ((valor_atual - valor_anterior) / abs(valor_anterior)) * 100