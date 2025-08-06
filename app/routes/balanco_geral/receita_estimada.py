"""
API para o quadro Receita Estimada Líquida
Parte do Balanço Geral GDF
Versão 100% dinâmica, que lê a estrutura do banco de dados.
"""
from flask import Blueprint, jsonify
from app.db_manager import db_manager
from datetime import datetime
import traceback

# Criar blueprint
receita_estimada_api = Blueprint('receita_estimada_api', __name__)

# O dicionário estático ESTRUTURA_RECEITAS foi completamente removido.
# A estrutura agora é lida diretamente do banco de dados.

@receita_estimada_api.route('/api/dados-receita-estimada')
def get_dados_receita_estimada():
    """Retorna os dados da receita estimada líquida de forma dinâmica"""
    try:
        # 1. Obter anos disponíveis (lógica mantida)
        anos_query = """
        SELECT DISTINCT coexercicio 
        FROM receita_saldo 
        WHERE coexercicio >= 2024
        ORDER BY coexercicio DESC
        """
        anos_result = db_manager.execute_query(anos_query)
        
        if len(anos_result) < 2:
            return jsonify({'erro': 'Dados insuficientes. São necessários pelo menos 2 anos de dados.'}), 400
        
        ano_atual = anos_result[0]['coexercicio']
        ano_anterior = anos_result[1]['coexercicio']
        
        # 2. Nova Query SQL 100% Dinâmica
        # Esta query busca os valores e já os associa com os nomes das categorias
        # e fontes diretamente das tabelas de dimensão, sem filtros estáticos.
        query = """
        WITH dados_agregados AS (
            SELECT
                rs.coexercicio,
                rs.cocategoriareceita,
                SUBSTRING(rs.cofontereceita, 1, 2) as fonte_principal,
                SUM(CASE
                    WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521199999'
                    THEN rs.saldo_contabil_receita
                    ELSE 0
                END) as receita_prevista
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
            COALESCE(drc.nocategoriareceita, 'Categoria ' || da.cocategoriareceita) as nocategoriareceita,
            da.fonte_principal,
            COALESCE(dro.nofontereceita, 'Fonte ' || da.fonte_principal) as nofontereceita,
            da.receita_prevista
        FROM
            dados_agregados da
        LEFT JOIN
            DIM_RECEITA_CATEGORIA drc ON da.cocategoriareceita = drc.cocategoriareceita
        LEFT JOIN
            DIM_RECEITA_ORIGEM dro ON da.fonte_principal = CAST(dro.cofontereceita AS VARCHAR)
        WHERE
            da.receita_prevista != 0
        ORDER BY
            da.cocategoriareceita, da.fonte_principal
        """
        
        params = [ano_atual, ano_anterior]
        resultados = db_manager.execute_query(query, params)
        
        # 3. Processar resultados com a nova função dinâmica
        dados = processar_dados_receita_dinamico(resultados, ano_atual, ano_anterior)
        
        return jsonify({
            'ano_atual': ano_atual,
            'ano_anterior': ano_anterior,
            'dados': dados,
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        print(f"Erro em get_dados_receita_estimada: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def processar_dados_receita_dinamico(resultados, ano_atual, ano_anterior):
    """
    Processa os resultados da query em estrutura hierárquica de forma dinâmica,
    sem depender de nenhuma estrutura pré-definida.
    """
    dados_por_categoria = {}

    # Etapa 1: Agrupar os dados lidos do banco em uma estrutura aninhada
    for row in resultados:
        cat_id = row['cocategoriareceita']
        cat_nome = row['nocategoriareceita']
        fonte_id = row['fonte_principal']
        fonte_nome = row['nofontereceita']
        exercicio = row['coexercicio']
        valor = float(row['receita_prevista'] or 0)

        # Cria a entrada da categoria se for a primeira vez que ela aparece
        if cat_id not in dados_por_categoria:
            dados_por_categoria[cat_id] = {
                'nome': cat_nome,
                'fontes': {},
                'total_atual': 0,
                'total_anterior': 0
            }

        # Cria a entrada da fonte dentro da categoria se for a primeira vez
        if fonte_id not in dados_por_categoria[cat_id]['fontes']:
            dados_por_categoria[cat_id]['fontes'][fonte_id] = {
                'nome': fonte_nome,
                'valor_atual': 0,
                'valor_anterior': 0
            }

        # Acumula os valores na estrutura
        if exercicio == ano_atual:
            dados_por_categoria[cat_id]['fontes'][fonte_id]['valor_atual'] += valor
            dados_por_categoria[cat_id]['total_atual'] += valor
        else:
            dados_por_categoria[cat_id]['fontes'][fonte_id]['valor_anterior'] += valor
            dados_por_categoria[cat_id]['total_anterior'] += valor

    # Etapa 2: Calcular totais e transformar o dicionário na lista final para a API
    total_geral_atual = sum(cat['total_atual'] for cat in dados_por_categoria.values())
    total_geral_anterior = sum(cat['total_anterior'] for cat in dados_por_categoria.values())

    dados_finais = []
    # Itera sobre as categorias que foram encontradas dinamicamente
    for cat_id, cat_data in sorted(dados_por_categoria.items()):
        categoria = {
            'tipo': 'categoria',
            'nome': cat_data['nome'],
            'valor_atual': cat_data['total_atual'],
            'valor_anterior': cat_data['total_anterior'],
            'percentual_atual': (cat_data['total_atual'] / total_geral_atual * 100) if total_geral_atual > 0 else 0,
            'percentual_anterior': (cat_data['total_anterior'] / total_geral_anterior * 100) if total_geral_anterior > 0 else 0,
            'variacao': calcular_variacao(cat_data['total_atual'], cat_data['total_anterior']),
            'fontes': []
        }

        # Itera sobre as fontes encontradas para cada categoria
        for fonte_id, fonte_data in sorted(cat_data['fontes'].items()):
            fonte = {
                'tipo': 'fonte',
                'nome': fonte_data['nome'],
                'valor_atual': fonte_data['valor_atual'],
                'valor_anterior': fonte_data['valor_anterior'],
                'percentual_atual': (fonte_data['valor_atual'] / total_geral_atual * 100) if total_geral_atual > 0 else 0,
                'percentual_anterior': (fonte_data['valor_anterior'] / total_geral_anterior * 100) if total_geral_anterior > 0 else 0,
                'variacao': calcular_variacao(fonte_data['valor_atual'], fonte_data['valor_anterior'])
            }
            categoria['fontes'].append(fonte)
        
        dados_finais.append(categoria)

    # Adicionar a linha de total ao final
    dados_finais.append({
        'tipo': 'total',
        'nome': 'RECEITA LÍQUIDA',
        'valor_atual': total_geral_atual,
        'valor_anterior': total_geral_anterior,
        'percentual_atual': 100.0,
        'percentual_anterior': 100.0,
        'variacao': calcular_variacao(total_geral_atual, total_geral_anterior)
    })

    return dados_finais

def calcular_variacao(valor_atual, valor_anterior):
    """Calcula a variação percentual entre dois valores (lógica mantida)"""
    if valor_anterior == 0:
        return 100.0 if valor_atual > 0 else 0.0
    return ((valor_atual - valor_anterior) / abs(valor_anterior)) * 100