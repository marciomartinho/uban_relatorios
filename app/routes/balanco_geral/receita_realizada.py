"""
API para o quadro Receita Líquida Realizada
Parte do Balanço Geral GDF
Compara Previsão Atualizada com Receita Realizada do ano atual e ano anterior
"""
from flask import Blueprint, jsonify
from app.db_manager import db_manager
from datetime import datetime
import traceback

# Criar blueprint
receita_realizada_api = Blueprint('receita_realizada_api', __name__)

@receita_realizada_api.route('/api/dados-receita-realizada')
def get_dados_receita_realizada():
    """Retorna os dados da receita realizada de forma dinâmica"""
    try:
        # 1. Obter anos disponíveis
        anos_query = """
        SELECT DISTINCT coexercicio 
        FROM receita_saldo 
        WHERE coexercicio >= 2023
        ORDER BY coexercicio DESC
        """
        anos_result = db_manager.execute_query(anos_query)
        
        if len(anos_result) < 2:
            return jsonify({'erro': 'Dados insuficientes. São necessários pelo menos 2 anos de dados.'}), 400
        
        ano_atual = anos_result[0]['coexercicio']
        ano_anterior = anos_result[1]['coexercicio']
        
        # 2. Query SQL para buscar previsão atualizada e receita realizada
        query = """
        WITH dados_agregados AS (
            SELECT
                rs.coexercicio,
                rs.cocategoriareceita,
                SUBSTRING(rs.cofontereceita, 1, 2) as fonte_principal,
                -- Previsão Atualizada: contas entre 521100000 e 521299999
                SUM(CASE
                    WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521299999'
                    THEN rs.saldo_contabil_receita
                    ELSE 0
                END) as previsao_atualizada,
                -- Receita Realizada: contas entre 621200000 e 621399999
                SUM(CASE
                    WHEN rs.cocontacontabil >= '621200000' AND rs.cocontacontabil <= '621399999'
                    THEN rs.saldo_contabil_receita
                    ELSE 0
                END) as receita_realizada
            FROM receita_saldo rs
            WHERE
                rs.coexercicio IN (?, ?)
            GROUP BY
                rs.coexercicio,
                rs.cocategoriareceita,
                SUBSTRING(rs.cofontereceita, 1, 2)
        )
        SELECT
            da.coexercicio,
            da.cocategoriareceita,
            COALESCE(drc.nocategoriareceita, CONCAT('Categoria ', da.cocategoriareceita)) as nocategoriareceita,
            da.fonte_principal,
            COALESCE(dro.nofontereceita, CONCAT('Fonte ', da.fonte_principal)) as nofontereceita,
            da.previsao_atualizada,
            da.receita_realizada
        FROM
            dados_agregados da
        LEFT JOIN
            DIM_RECEITA_CATEGORIA drc ON CAST(da.cocategoriareceita AS BIGINT) = drc.cocategoriareceita
        LEFT JOIN
            DIM_RECEITA_ORIGEM dro ON CAST(da.fonte_principal AS BIGINT) = dro.cofontereceita
        WHERE
            (da.previsao_atualizada != 0 OR da.receita_realizada != 0)
        ORDER BY
            da.cocategoriareceita, da.fonte_principal
        """
        
        params = [ano_atual, ano_anterior]
        resultados = db_manager.execute_query(query, params)
        
        # 3. Processar resultados
        dados = processar_dados_receita_realizada(resultados, ano_atual, ano_anterior)
        
        return jsonify({
            'ano_atual': ano_atual,
            'ano_anterior': ano_anterior,
            'dados': dados,
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        print(f"Erro em get_dados_receita_realizada: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def processar_dados_receita_realizada(resultados, ano_atual, ano_anterior):
    """
    Processa os resultados da query em estrutura hierárquica
    """
    dados_por_categoria = {}

    # Etapa 1: Agrupar os dados lidos do banco
    for row in resultados:
        cat_id = row['cocategoriareceita']
        cat_nome = row['nocategoriareceita']
        fonte_id = row['fonte_principal']
        fonte_nome = row['nofontereceita']
        exercicio = row['coexercicio']
        previsao_atualizada = float(row['previsao_atualizada'] or 0)
        receita_realizada = float(row['receita_realizada'] or 0)

        # Cria a entrada da categoria se for a primeira vez
        if cat_id not in dados_por_categoria:
            dados_por_categoria[cat_id] = {
                'nome': cat_nome,
                'fontes': {},
                'previsao_atual': 0,
                'realizada_atual': 0,
                'realizada_anterior': 0
            }

        # Cria a entrada da fonte se for a primeira vez
        if fonte_id not in dados_por_categoria[cat_id]['fontes']:
            dados_por_categoria[cat_id]['fontes'][fonte_id] = {
                'nome': fonte_nome,
                'previsao_atual': 0,
                'realizada_atual': 0,
                'realizada_anterior': 0
            }

        # Acumula os valores
        if exercicio == ano_atual:
            dados_por_categoria[cat_id]['fontes'][fonte_id]['previsao_atual'] += previsao_atualizada
            dados_por_categoria[cat_id]['fontes'][fonte_id]['realizada_atual'] += receita_realizada
            dados_por_categoria[cat_id]['previsao_atual'] += previsao_atualizada
            dados_por_categoria[cat_id]['realizada_atual'] += receita_realizada
        else:  # ano_anterior
            dados_por_categoria[cat_id]['fontes'][fonte_id]['realizada_anterior'] += receita_realizada
            dados_por_categoria[cat_id]['realizada_anterior'] += receita_realizada

    # Etapa 2: Calcular totais e transformar na estrutura final
    total_previsao_atual = sum(cat['previsao_atual'] for cat in dados_por_categoria.values())
    total_realizada_atual = sum(cat['realizada_atual'] for cat in dados_por_categoria.values())
    total_realizada_anterior = sum(cat['realizada_anterior'] for cat in dados_por_categoria.values())

    dados_finais = []
    
    # Itera sobre as categorias
    for cat_id, cat_data in sorted(dados_por_categoria.items()):
        categoria = {
            'tipo': 'categoria',
            'nome': cat_data['nome'],
            'previsao_atual': cat_data['previsao_atual'],
            'realizada_atual': cat_data['realizada_atual'],
            'variacao_previsto': calcular_variacao_percentual(cat_data['realizada_atual'], cat_data['previsao_atual']),
            'realizada_anterior': cat_data['realizada_anterior'],
            'variacao_anual': calcular_variacao_percentual(cat_data['realizada_atual'], cat_data['realizada_anterior']),
            'fontes': []
        }

        # Itera sobre as fontes
        for fonte_id, fonte_data in sorted(cat_data['fontes'].items()):
            fonte = {
                'tipo': 'fonte',
                'nome': fonte_data['nome'],
                'previsao_atual': fonte_data['previsao_atual'],
                'realizada_atual': fonte_data['realizada_atual'],
                'variacao_previsto': calcular_variacao_percentual(fonte_data['realizada_atual'], fonte_data['previsao_atual']),
                'realizada_anterior': fonte_data['realizada_anterior'],
                'variacao_anual': calcular_variacao_percentual(fonte_data['realizada_atual'], fonte_data['realizada_anterior'])
            }
            categoria['fontes'].append(fonte)
        
        dados_finais.append(categoria)

    # Adicionar linha de total
    dados_finais.append({
        'tipo': 'total',
        'nome': 'RECEITA LÍQUIDA',
        'previsao_atual': total_previsao_atual,
        'realizada_atual': total_realizada_atual,
        'variacao_previsto': calcular_variacao_percentual(total_realizada_atual, total_previsao_atual),
        'realizada_anterior': total_realizada_anterior,
        'variacao_anual': calcular_variacao_percentual(total_realizada_atual, total_realizada_anterior)
    })

    return dados_finais

def calcular_variacao_percentual(valor_atual, valor_anterior):
    """Calcula a variação percentual entre dois valores"""
    if valor_anterior == 0:
        return 100.0 if valor_atual > 0 else 0.0
    return ((valor_atual - valor_anterior) / abs(valor_anterior)) * 100