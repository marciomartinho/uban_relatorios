"""
Blueprint para Relatório Detalhado por Fonte/Receita
Arquivo: app/routes/relatorio_receita_fonte.py
"""
from flask import Blueprint, render_template, jsonify, request
from app.db_manager import db_manager
from datetime import datetime
import traceback

# Criar blueprint
relatorio_receita_fonte = Blueprint('relatorio_receita_fonte', __name__)

@relatorio_receita_fonte.route('/')
def index():
    """Página principal do relatório"""
    return render_template('relatorio_receita_fonte/index.html',
                         title='Relatório Detalhado por Fonte/Receita')

@relatorio_receita_fonte.route('/api/dados-por-fonte')
def get_dados_por_fonte():
    """Retorna dados agrupados por fonte"""
    try:
        ano_atual = datetime.now().year
        ano_anterior = ano_atual - 1
        coug = request.args.get('coug', '')  # Vazio significa consolidado
        
        # Query para buscar dados agrupados por fonte
        if coug:
            # Query com filtro de UG
            query = """
            WITH fonte_data AS (
                -- Previsão Inicial (521100000 - 521199999)
                SELECT 
                    cofonte,
                    coalinea,
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 521100000 AND 521199999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as previsao_inicial,
                    
                    -- Previsão Atualizada (521100000 - 521299999)
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 521100000 AND 521299999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as previsao_atualizada,
                    
                    -- Realizada Ano Atual (621200000 - 621399999)
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as realizada_atual,
                    
                    -- Realizada Ano Anterior (621200000 - 621399999)
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as realizada_anterior
                    
                FROM receita_saldo
                WHERE coexercicio IN (?, ?)
                  AND cofonte IS NOT NULL
                  AND cofonte != ''
                  AND coug = ?
                GROUP BY cofonte, coalinea
            )
            SELECT 
                cofonte,
                coalinea,
                previsao_inicial,
                previsao_atualizada,
                realizada_atual,
                realizada_anterior,
                CASE 
                    WHEN realizada_anterior != 0 
                    THEN ((realizada_atual - realizada_anterior) / ABS(realizada_anterior)) * 100
                    ELSE 0 
                END as variacao_percentual,
                (realizada_atual - realizada_anterior) as variacao_absoluta
            FROM fonte_data
            WHERE (previsao_inicial != 0 OR previsao_atualizada != 0 OR 
                   realizada_atual != 0 OR realizada_anterior != 0)
            ORDER BY cofonte, coalinea
            """
            params = [ano_atual, ano_atual, ano_atual, ano_anterior, ano_atual, ano_anterior, coug]
        else:
            # Query sem filtro de UG (consolidado)
            query = """
            WITH fonte_data AS (
                -- Previsão Inicial (521100000 - 521199999)
                SELECT 
                    cofonte,
                    coalinea,
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 521100000 AND 521199999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as previsao_inicial,
                    
                    -- Previsão Atualizada (521100000 - 521299999)
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 521100000 AND 521299999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as previsao_atualizada,
                    
                    -- Realizada Ano Atual (621200000 - 621399999)
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as realizada_atual,
                    
                    -- Realizada Ano Anterior (621200000 - 621399999)
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as realizada_anterior
                    
                FROM receita_saldo
                WHERE coexercicio IN (?, ?)
                  AND cofonte IS NOT NULL
                  AND cofonte != ''
                GROUP BY cofonte, coalinea
            )
            SELECT 
                cofonte,
                coalinea,
                previsao_inicial,
                previsao_atualizada,
                realizada_atual,
                realizada_anterior,
                CASE 
                    WHEN realizada_anterior != 0 
                    THEN ((realizada_atual - realizada_anterior) / ABS(realizada_anterior)) * 100
                    ELSE 0 
                END as variacao_percentual,
                (realizada_atual - realizada_anterior) as variacao_absoluta
            FROM fonte_data
            WHERE (previsao_inicial != 0 OR previsao_atualizada != 0 OR 
                   realizada_atual != 0 OR realizada_anterior != 0)
            ORDER BY cofonte, coalinea
            """
            params = [ano_atual, ano_atual, ano_atual, ano_anterior, ano_atual, ano_anterior]
        
        dados = db_manager.execute_query(query, params)
        
        # Buscar descrições das fontes
        query_desc_fonte = """
        SELECT DISTINCT 
            CAST(cofonte AS VARCHAR) as cofonte, 
            nofonte 
        FROM dim_fonte
        """
        desc_fontes = db_manager.execute_query(query_desc_fonte)
        dict_fontes = {str(f['cofonte']): f['nofonte'] for f in desc_fontes}
        
        # Buscar descrições das alíneas
        query_desc_alinea = """
        SELECT DISTINCT 
            CAST(coalinea AS VARCHAR) as coalinea, 
            noalinea 
        FROM dim_receita_alinea
        """
        desc_alineas = db_manager.execute_query(query_desc_alinea)
        dict_alineas = {str(a['coalinea']): a['noalinea'] for a in desc_alineas}
        
        # Adicionar descrições aos dados
        for item in dados:
            item['nome_fonte'] = dict_fontes.get(str(item['cofonte']), '')
            item['nome_alinea'] = dict_alineas.get(str(item['coalinea']), '')
        
        # Agrupar dados por fonte para estrutura hierárquica
        dados_agrupados = {}
        totais_gerais = {
            'previsao_inicial': 0,
            'previsao_atualizada': 0,
            'realizada_atual': 0,
            'realizada_anterior': 0
        }
        
        for item in dados:
            cofonte = item['cofonte']
            
            if cofonte not in dados_agrupados:
                dados_agrupados[cofonte] = {
                    'cofonte': cofonte,
                    'nome_fonte': item['nome_fonte'],
                    'previsao_inicial': 0,
                    'previsao_atualizada': 0,
                    'realizada_atual': 0,
                    'realizada_anterior': 0,
                    'variacao_percentual': 0,
                    'variacao_absoluta': 0,
                    'alineas': []
                }
            
            # Adicionar alínea
            dados_agrupados[cofonte]['alineas'].append({
                'coalinea': item['coalinea'],
                'nome_alinea': item['nome_alinea'],
                'previsao_inicial': float(item['previsao_inicial'] or 0),
                'previsao_atualizada': float(item['previsao_atualizada'] or 0),
                'realizada_atual': float(item['realizada_atual'] or 0),
                'realizada_anterior': float(item['realizada_anterior'] or 0),
                'variacao_percentual': float(item['variacao_percentual'] or 0),
                'variacao_absoluta': float(item['variacao_absoluta'] or 0)
            })
            
            # Somar totais da fonte
            dados_agrupados[cofonte]['previsao_inicial'] += float(item['previsao_inicial'] or 0)
            dados_agrupados[cofonte]['previsao_atualizada'] += float(item['previsao_atualizada'] or 0)
            dados_agrupados[cofonte]['realizada_atual'] += float(item['realizada_atual'] or 0)
            dados_agrupados[cofonte]['realizada_anterior'] += float(item['realizada_anterior'] or 0)
            
            # Somar totais gerais
            totais_gerais['previsao_inicial'] += float(item['previsao_inicial'] or 0)
            totais_gerais['previsao_atualizada'] += float(item['previsao_atualizada'] or 0)
            totais_gerais['realizada_atual'] += float(item['realizada_atual'] or 0)
            totais_gerais['realizada_anterior'] += float(item['realizada_anterior'] or 0)
        
        # Calcular variação para cada fonte
        for fonte_data in dados_agrupados.values():
            if fonte_data['realizada_anterior'] != 0:
                fonte_data['variacao_percentual'] = ((fonte_data['realizada_atual'] - fonte_data['realizada_anterior']) / abs(fonte_data['realizada_anterior'])) * 100
                fonte_data['variacao_absoluta'] = fonte_data['realizada_atual'] - fonte_data['realizada_anterior']
        
        # Calcular variação dos totais gerais
        if totais_gerais['realizada_anterior'] != 0:
            totais_gerais['variacao_percentual'] = ((totais_gerais['realizada_atual'] - totais_gerais['realizada_anterior']) / abs(totais_gerais['realizada_anterior'])) * 100
            totais_gerais['variacao_absoluta'] = totais_gerais['realizada_atual'] - totais_gerais['realizada_anterior']
        else:
            totais_gerais['variacao_percentual'] = 0
            totais_gerais['variacao_absoluta'] = 0
        
        # Ordenar por valor realizado 2025 (maior para menor)
        dados_ordenados = sorted(dados_agrupados.values(), 
                                key=lambda x: x['realizada_atual'], 
                                reverse=True)
        
        return jsonify({
            'dados': dados_ordenados,
            'totais': totais_gerais,
            'ano_atual': ano_atual,
            'ano_anterior': ano_anterior
        })
        
    except Exception as e:
        print(f"Erro em get_dados_por_fonte: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@relatorio_receita_fonte.route('/api/dados-por-receita')
def get_dados_por_receita():
    """Retorna dados agrupados por receita (alínea)"""
    try:
        ano_atual = datetime.now().year
        ano_anterior = ano_atual - 1
        coug = request.args.get('coug', '')  # Vazio significa consolidado
        
        # Query similar à anterior, mas agrupando primeiro por alínea
        if coug:
            # Query com filtro de UG
            query = """
            WITH receita_data AS (
                SELECT 
                    coalinea,
                    cofonte,
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 521100000 AND 521199999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as previsao_inicial,
                    
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 521100000 AND 521299999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as previsao_atualizada,
                    
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as realizada_atual,
                    
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as realizada_anterior
                    
                FROM receita_saldo
                WHERE coexercicio IN (?, ?)
                  AND coalinea IS NOT NULL
                  AND coalinea != ''
                  AND coug = ?
                GROUP BY coalinea, cofonte
            )
            SELECT 
                coalinea,
                cofonte,
                previsao_inicial,
                previsao_atualizada,
                realizada_atual,
                realizada_anterior,
                CASE 
                    WHEN realizada_anterior != 0 
                    THEN ((realizada_atual - realizada_anterior) / ABS(realizada_anterior)) * 100
                    ELSE 0 
                END as variacao_percentual,
                (realizada_atual - realizada_anterior) as variacao_absoluta
            FROM receita_data
            WHERE (previsao_inicial != 0 OR previsao_atualizada != 0 OR 
                   realizada_atual != 0 OR realizada_anterior != 0)
            ORDER BY coalinea, cofonte
            """
            params = [ano_atual, ano_atual, ano_atual, ano_anterior, ano_atual, ano_anterior, coug]
        else:
            # Query sem filtro de UG (consolidado)
            query = """
            WITH receita_data AS (
                SELECT 
                    coalinea,
                    cofonte,
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 521100000 AND 521199999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as previsao_inicial,
                    
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 521100000 AND 521299999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as previsao_atualizada,
                    
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as realizada_atual,
                    
                    SUM(CASE 
                        WHEN coexercicio = ? AND CAST(cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999 
                        THEN saldo_contabil_receita 
                        ELSE 0 
                    END) as realizada_anterior
                    
                FROM receita_saldo
                WHERE coexercicio IN (?, ?)
                  AND coalinea IS NOT NULL
                  AND coalinea != ''
                GROUP BY coalinea, cofonte
            )
            SELECT 
                coalinea,
                cofonte,
                previsao_inicial,
                previsao_atualizada,
                realizada_atual,
                realizada_anterior,
                CASE 
                    WHEN realizada_anterior != 0 
                    THEN ((realizada_atual - realizada_anterior) / ABS(realizada_anterior)) * 100
                    ELSE 0 
                END as variacao_percentual,
                (realizada_atual - realizada_anterior) as variacao_absoluta
            FROM receita_data
            WHERE (previsao_inicial != 0 OR previsao_atualizada != 0 OR 
                   realizada_atual != 0 OR realizada_anterior != 0)
            ORDER BY coalinea, cofonte
            """
            params = [ano_atual, ano_atual, ano_atual, ano_anterior, ano_atual, ano_anterior]
        
        dados = db_manager.execute_query(query, params)
        
        # Buscar descrições
        query_desc_fonte = """
        SELECT DISTINCT 
            CAST(cofonte AS VARCHAR) as cofonte, 
            nofonte 
        FROM dim_fonte
        """
        desc_fontes = db_manager.execute_query(query_desc_fonte)
        dict_fontes = {str(f['cofonte']): f['nofonte'] for f in desc_fontes}
        
        query_desc_alinea = """
        SELECT DISTINCT 
            CAST(coalinea AS VARCHAR) as coalinea, 
            noalinea 
        FROM dim_receita_alinea
        """
        desc_alineas = db_manager.execute_query(query_desc_alinea)
        dict_alineas = {str(a['coalinea']): a['noalinea'] for a in desc_alineas}
        
        # Adicionar descrições aos dados
        for item in dados:
            item['nome_fonte'] = dict_fontes.get(str(item['cofonte']), '')
            item['nome_alinea'] = dict_alineas.get(str(item['coalinea']), '')
        
        # Agrupar dados por alínea para estrutura hierárquica
        dados_agrupados = {}
        totais_gerais = {
            'previsao_inicial': 0,
            'previsao_atualizada': 0,
            'realizada_atual': 0,
            'realizada_anterior': 0
        }
        
        for item in dados:
            coalinea = item['coalinea']
            
            if coalinea not in dados_agrupados:
                dados_agrupados[coalinea] = {
                    'coalinea': coalinea,
                    'nome_alinea': item['nome_alinea'],
                    'previsao_inicial': 0,
                    'previsao_atualizada': 0,
                    'realizada_atual': 0,
                    'realizada_anterior': 0,
                    'variacao_percentual': 0,
                    'variacao_absoluta': 0,
                    'fontes': []
                }
            
            # Adicionar fonte
            dados_agrupados[coalinea]['fontes'].append({
                'cofonte': item['cofonte'],
                'nome_fonte': item['nome_fonte'],
                'previsao_inicial': float(item['previsao_inicial'] or 0),
                'previsao_atualizada': float(item['previsao_atualizada'] or 0),
                'realizada_atual': float(item['realizada_atual'] or 0),
                'realizada_anterior': float(item['realizada_anterior'] or 0),
                'variacao_percentual': float(item['variacao_percentual'] or 0),
                'variacao_absoluta': float(item['variacao_absoluta'] or 0)
            })
            
            # Somar totais da alínea
            dados_agrupados[coalinea]['previsao_inicial'] += float(item['previsao_inicial'] or 0)
            dados_agrupados[coalinea]['previsao_atualizada'] += float(item['previsao_atualizada'] or 0)
            dados_agrupados[coalinea]['realizada_atual'] += float(item['realizada_atual'] or 0)
            dados_agrupados[coalinea]['realizada_anterior'] += float(item['realizada_anterior'] or 0)
            
            # Somar totais gerais
            totais_gerais['previsao_inicial'] += float(item['previsao_inicial'] or 0)
            totais_gerais['previsao_atualizada'] += float(item['previsao_atualizada'] or 0)
            totais_gerais['realizada_atual'] += float(item['realizada_atual'] or 0)
            totais_gerais['realizada_anterior'] += float(item['realizada_anterior'] or 0)
        
        # Calcular variação para cada alínea
        for alinea_data in dados_agrupados.values():
            if alinea_data['realizada_anterior'] != 0:
                alinea_data['variacao_percentual'] = ((alinea_data['realizada_atual'] - alinea_data['realizada_anterior']) / abs(alinea_data['realizada_anterior'])) * 100
                alinea_data['variacao_absoluta'] = alinea_data['realizada_atual'] - alinea_data['realizada_anterior']
        
        # Calcular variação dos totais gerais
        if totais_gerais['realizada_anterior'] != 0:
            totais_gerais['variacao_percentual'] = ((totais_gerais['realizada_atual'] - totais_gerais['realizada_anterior']) / abs(totais_gerais['realizada_anterior'])) * 100
            totais_gerais['variacao_absoluta'] = totais_gerais['realizada_atual'] - totais_gerais['realizada_anterior']
        else:
            totais_gerais['variacao_percentual'] = 0
            totais_gerais['variacao_absoluta'] = 0
        
        # Ordenar por valor realizado 2025 (maior para menor)
        dados_ordenados = sorted(dados_agrupados.values(), 
                                key=lambda x: x['realizada_atual'], 
                                reverse=True)
        
        return jsonify({
            'dados': dados_ordenados,
            'totais': totais_gerais,
            'ano_atual': ano_atual,
            'ano_anterior': ano_anterior
        })
        
    except Exception as e:
        print(f"Erro em get_dados_por_receita: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@relatorio_receita_fonte.route('/api/lista-ugs')
def get_lista_ugs():
    """Retorna lista de UGs que possuem saldo nas contas de receita realizada"""
    try:
        ano_atual = datetime.now().year
        
        # Query para buscar UGs com saldo realizado
        query = """
        SELECT DISTINCT 
            rs.coug,
            ug.noug
        FROM receita_saldo rs
        LEFT JOIN dim_unidade_gestora ug ON rs.coug = ug.coug
        WHERE rs.coexercicio = ?
          AND CAST(rs.cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999
          AND rs.saldo_contabil_receita != 0
          AND rs.coug IS NOT NULL
          AND rs.coug != ''
        ORDER BY rs.coug
        """
        
        params = [ano_atual]
        
        ugs = db_manager.execute_query(query, params)
        
        # Formatar lista de UGs
        lista_ugs = []
        for ug in ugs:
            lista_ugs.append({
                'coug': str(ug['coug']),
                'noug': ug['noug'] or f"UG {ug['coug']}"
            })
        
        return jsonify({
            'ugs': lista_ugs,
            'total': len(lista_ugs)
        })
        
    except Exception as e:
        print(f"Erro em get_lista_ugs: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@relatorio_receita_fonte.route('/api/detalhes-lancamentos')
def get_detalhes_lancamentos():
    """Retorna detalhes dos lançamentos para uma combinação fonte/alínea"""
    try:
        cofonte = request.args.get('cofonte')
        coalinea = request.args.get('coalinea')
        coug = request.args.get('coug', '')  # Recebe coug do filtro principal
        ano = request.args.get('ano', datetime.now().year)
        exportar = request.args.get('exportar', 'false') == 'true'
        
        if not cofonte or not coalinea:
            return jsonify({'erro': 'Parâmetros cofonte e coalinea são obrigatórios'}), 400
        
        # Query para buscar lançamentos da tabela RECEITA_LANCAMENTO
        # Se tiver filtro de coug, usa esse valor como cougcontab na query
        if coug:
            query = """
            SELECT 
                rl.cocontacontabil,
                CAST(rl.coug AS VARCHAR) as coug,
                rl.nudocumento,
                rl.coevento,
                rl.indebitocredito,
                rl.valancamento,
                rl.dalancamento,
                rl.cogrupo,
                cc.nocontacontabil,
                ug.noug,
                ev.noevento
            FROM receita_lancamento rl
            LEFT JOIN dim_conta_contabil cc ON rl.cocontacontabil = cc.cocontacontabil
            LEFT JOIN dim_unidade_gestora ug ON rl.coug = ug.coug
            LEFT JOIN dim_evento ev ON rl.coevento = ev.coevento
            WHERE rl.cofonte = ?
              AND rl.coalinea = ?
              AND rl.coexercicio = ?
              AND rl.cougcontab = ?
              AND CAST(rl.cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999
            ORDER BY rl.dalancamento DESC, rl.nudocumento
            """
            params = [cofonte, coalinea, ano, coug]  # coug será usado como cougcontab na query
        else:
            # Modo consolidado - busca todos os lançamentos sem filtro de UG
            query = """
            SELECT 
                rl.cocontacontabil,
                CAST(rl.coug AS VARCHAR) as coug,
                rl.nudocumento,
                rl.coevento,
                rl.indebitocredito,
                rl.valancamento,
                rl.dalancamento,
                rl.cogrupo,
                cc.nocontacontabil,
                ug.noug,
                ev.noevento
            FROM receita_lancamento rl
            LEFT JOIN dim_conta_contabil cc ON rl.cocontacontabil = cc.cocontacontabil
            LEFT JOIN dim_unidade_gestora ug ON rl.coug = ug.coug
            LEFT JOIN dim_evento ev ON rl.coevento = ev.coevento
            WHERE rl.cofonte = ?
              AND rl.coalinea = ?
              AND rl.coexercicio = ?
              AND CAST(rl.cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999
            ORDER BY rl.dalancamento DESC, rl.nudocumento
            """
            params = [cofonte, coalinea, ano]
        
        # Se não for exportação, limitar a 1000 registros
        if not exportar:
            query += " LIMIT 1000"
        
        dados = db_manager.execute_query(query, params)
        
        # Contar total de registros
        if coug:
            query_count = """
            SELECT COUNT(*) as total
            FROM receita_lancamento
            WHERE cofonte = ?
              AND coalinea = ?
              AND coexercicio = ?
              AND cougcontab = ?
              AND CAST(cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999
            """
            count_params = [cofonte, coalinea, ano, coug]  # coug será usado como cougcontab
        else:
            query_count = """
            SELECT COUNT(*) as total
            FROM receita_lancamento
            WHERE cofonte = ?
              AND coalinea = ?
              AND coexercicio = ?
              AND CAST(cocontacontabil AS BIGINT) BETWEEN 621200000 AND 621399999
            """
            count_params = [cofonte, coalinea, ano]
        
        count_result = db_manager.execute_query(query_count, count_params)
        total_registros = count_result[0]['total'] if count_result else 0
        
        # Formatar dados para retorno
        dados_formatados = []
        total_debito = 0
        total_credito = 0
        
        for item in dados:
            valor = float(item['valancamento'] or 0)
            tipo_dc = item['indebitocredito']
            
            if tipo_dc == 'D':
                total_debito += valor
            else:
                total_credito += valor
            
            dados_formatados.append({
                'cocontacontabil': item['cocontacontabil'],
                'nocontacontabil': item['nocontacontabil'] or '',
                'coug': str(item['coug']) if item['coug'] else '',
                'noug': item['noug'] or '',
                'nudocumento': item['nudocumento'],
                'coevento': item['coevento'],
                'noevento': item['noevento'] or '',
                'indebitocredito': tipo_dc,
                'valancamento': valor,
                'dalancamento': item['dalancamento'].strftime('%d/%m/%Y') if item['dalancamento'] else '',
                'cogrupo': item['cogrupo'] or ''
            })
        
        # Buscar descrições da fonte e alínea
        query_desc = """
        SELECT 
            (SELECT nofonte FROM dim_fonte WHERE cofonte = ? LIMIT 1) as nome_fonte,
            (SELECT noalinea FROM dim_receita_alinea WHERE coalinea = ? LIMIT 1) as nome_alinea
        """
        
        desc_result = db_manager.execute_query(query_desc, [cofonte, coalinea])
        nome_fonte = desc_result[0]['nome_fonte'] if desc_result else ''
        nome_alinea = desc_result[0]['nome_alinea'] if desc_result else ''
        
        return jsonify({
            'dados': dados_formatados,
            'total_registros': total_registros,
            'registros_exibidos': len(dados_formatados),
            'total_debito': total_debito,
            'total_credito': total_credito,
            'saldo': total_credito - total_debito,
            'cofonte': cofonte,
            'nome_fonte': nome_fonte,
            'coalinea': coalinea,
            'nome_alinea': nome_alinea,
            'ano': ano,
            'limitado': not exportar and total_registros > 1000
        })
        
    except Exception as e:
        print(f"Erro em get_detalhes_lancamentos: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500
    
@relatorio_receita_fonte.route('/api/verificar-inconsistencias')
def verificar_inconsistencias():
    """Verifica inconsistências entre lançamentos e dimensão de fonte/conta - mostra documentos"""
    try:
        ano_atual = datetime.now().year
        exportar = request.args.get('exportar', 'false') == 'true'
        limite = 500 if not exportar else 10000  # Limite maior para visualização
        
        # Query ATUALIZADA para usar coalinea diretamente e incluir coevento
        query = """
        WITH combinacoes_validas AS (
            -- Combinações válidas da dimensão (agora usando coalinea diretamente)
            SELECT DISTINCT
                CAST(cofonte AS VARCHAR) as cofonte,
                CAST(coalinea AS VARCHAR) as coalinea
            FROM dim_receita_fonte_conta_contabil
            WHERE cofonte IS NOT NULL
              AND coalinea IS NOT NULL
              AND instatus = 0
        )
        -- Buscar documentos com combinações inválidas
        SELECT 
            rl.nudocumento,
            rl.cougcontab,
            rl.coevento,
            CAST(rl.cofonte AS VARCHAR) as cofonte,
            CAST(rl.coalinea AS VARCHAR) as coalinea,
            rl.dalancamento,
            rl.valancamento,
            rl.indebitocredito,
            f.nofonte,
            a.noalinea,
            ug.noug,
            ev.noevento
        FROM receita_lancamento rl
        LEFT JOIN combinacoes_validas cv 
            ON CAST(rl.cofonte AS VARCHAR) = cv.cofonte 
            AND CAST(rl.coalinea AS VARCHAR) = cv.coalinea
        LEFT JOIN dim_fonte f 
            ON CAST(rl.cofonte AS BIGINT) = f.cofonte
        LEFT JOIN dim_receita_alinea a 
            ON CAST(rl.coalinea AS BIGINT) = a.coalinea
        LEFT JOIN dim_unidade_gestora ug
            ON rl.cougcontab = ug.coug
        LEFT JOIN dim_evento ev
            ON rl.coevento = ev.coevento
        WHERE cv.cofonte IS NULL  -- Não existe na dimensão
          AND rl.cofonte IS NOT NULL
          AND rl.cofonte != ''
          AND rl.coalinea IS NOT NULL
          AND rl.coalinea != ''
          AND rl.coexercicio = ?
        ORDER BY ABS(rl.valancamento) DESC
        """
        
        if not exportar:
            query += f" LIMIT {limite}"
        
        # Executar query
        documentos = db_manager.execute_query(query, [ano_atual])
        
        # Calcular totais e estatísticas
        total_documentos = len(documentos)
        valor_total = sum(abs(doc['valancamento']) for doc in documentos)
        
        # Agrupar por combinação única para contar
        combinacoes_unicas = set()
        for doc in documentos:
            combinacoes_unicas.add((doc['cofonte'], doc['coalinea']))
        
        # Query para contar total real (sem limite) - ATUALIZADA
        query_count = """
        WITH combinacoes_validas AS (
            SELECT DISTINCT
                CAST(cofonte AS VARCHAR) as cofonte,
                CAST(coalinea AS VARCHAR) as coalinea
            FROM dim_receita_fonte_conta_contabil
            WHERE cofonte IS NOT NULL
              AND coalinea IS NOT NULL
              AND instatus = 0
        )
        SELECT COUNT(*) as total
        FROM receita_lancamento rl
        LEFT JOIN combinacoes_validas cv 
            ON CAST(rl.cofonte AS VARCHAR) = cv.cofonte 
            AND CAST(rl.coalinea AS VARCHAR) = cv.coalinea
        WHERE cv.cofonte IS NULL
          AND rl.cofonte IS NOT NULL
          AND rl.cofonte != ''
          AND rl.coalinea IS NOT NULL
          AND rl.coalinea != ''
          AND rl.coexercicio = ?
        """
        
        count_result = db_manager.execute_query(query_count, [ano_atual])
        total_sem_limite = count_result[0]['total'] if count_result else total_documentos
        
        # Formatar resposta
        response = {
            'documentos': documentos,
            'totais': {
                'total_documentos': total_sem_limite,
                'total_exibido': len(documentos),
                'total_combinacoes': len(combinacoes_unicas),
                'valor_total': float(valor_total)
            },
            'filtros': {
                'ano': ano_atual,
                'limitado': not exportar and total_sem_limite > limite
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Erro em verificar_inconsistencias: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@relatorio_receita_fonte.route('/api/estatisticas-inconsistencias')
def get_estatisticas_inconsistencias():
    """Retorna estatísticas rápidas sobre inconsistências (para o badge)"""
    try:
        # Query simplificada para contar - ATUALIZADA
        query = """
        WITH combinacoes_problema AS (
            SELECT DISTINCT 
                CAST(rl.cofonte AS VARCHAR) as cofonte,
                CAST(rl.coalinea AS VARCHAR) as coalinea
            FROM receita_lancamento rl
            WHERE NOT EXISTS (
                SELECT 1 
                FROM dim_receita_fonte_conta_contabil d
                WHERE CAST(d.cofonte AS VARCHAR) = CAST(rl.cofonte AS VARCHAR)
                  AND CAST(d.coalinea AS VARCHAR) = CAST(rl.coalinea AS VARCHAR)
                  AND d.instatus = 0
            )
            AND rl.cofonte IS NOT NULL
            AND rl.cofonte != ''
            AND rl.coalinea IS NOT NULL
            AND rl.coalinea != ''
            AND rl.coexercicio = ?
        )
        SELECT COUNT(*) as total
        FROM combinacoes_problema
        """
        
        ano_atual = datetime.now().year
        result = db_manager.execute_query(query, [ano_atual])
        
        total = result[0]['total'] if result else 0
        
        return jsonify({
            'total': total,
            'ano': ano_atual,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Erro em get_estatisticas_inconsistencias: {str(e)}")
        return jsonify({'total': 0, 'erro': str(e)}), 200