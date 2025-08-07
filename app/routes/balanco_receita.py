"""
Blueprint para Balanço Orçamentário da Receita
Adaptado do sistema original para trabalhar com DuckDB
Agora com suporte para exibir UGs por alínea e lançamentos
"""
from flask import Blueprint, render_template, jsonify, request, current_app
from app.db_manager import db_manager
from datetime import datetime
import traceback

# Criar blueprint
balanco_receita = Blueprint('balanco_receita', __name__)

# Mapeamento das categorias e suas fontes
CATEGORIA_FONTE_MAP = {
    '1': {
        'nome': 'Receitas Correntes',
        'fontes_inicio': 11,
        'fontes_fim': 19
    },
    '2': {
        'nome': 'Receitas de Capital',
        'fontes_inicio': 21,
        'fontes_fim': 29
    },
    '7': {
        'nome': 'Receitas Correntes Intra-Orçamentárias',
        'fontes_inicio': 71,
        'fontes_fim': 79
    }
}

@balanco_receita.route('/')
def index():
    """Página principal do Balanço Orçamentário da Receita"""
    return render_template('balanco_receita/index.html',
                         title='Balanço Orçamentário da Receita')

@balanco_receita.route('/api/filtros')
def get_filtros():
    """Retorna os filtros disponíveis para o relatório"""
    try:
        anos_query = "SELECT DISTINCT coexercicio FROM receita_saldo ORDER BY coexercicio DESC"
        anos_result = db_manager.execute_query(anos_query)
        anos = [row['coexercicio'] for row in anos_result]

        ultimo_mes = None
        if anos:
            ano_atual = anos[0]
            
            param_style = "?" if db_manager.is_duckdb else ":ano_atual"
            meses_query = f"SELECT DISTINCT inmes FROM receita_saldo WHERE coexercicio = {param_style} AND ABS(saldo_contabil_receita) > 0.01 ORDER BY inmes DESC LIMIT 1"
            params = [ano_atual] if db_manager.is_duckdb else {'ano_atual': ano_atual}

            result = db_manager.execute_query(meses_query, params)
            ultimo_mes = result[0]['inmes'] if result else 12

        ugs_query = """
        SELECT DISTINCT
            rs.coug,
            COALESCE(ug.noug, 'UG ' || rs.coug) as nome_ug
        FROM receita_saldo rs
        LEFT JOIN dim_unidade_gestora ug ON rs.coug = CAST(ug.coug AS VARCHAR)
        WHERE ABS(rs.saldo_contabil_receita) > 0.01
        ORDER BY rs.coug
        """
        ugs = []
        for row in db_manager.execute_query(ugs_query):
            ugs.append({
                'codigo': row['coug'],
                'descricao': f"{row['coug']} - {row['nome_ug']}"
            })

        return jsonify({
            'anos': anos,
            'ano_atual': anos[0] if anos else None,
            'ultimo_mes': ultimo_mes,
            'ugs': ugs
        })

    except Exception as e:
        print(f"Erro em get_filtros: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@balanco_receita.route('/api/gerar-relatorio')
def gerar_relatorio():
    """Gera o relatório de Balanço Orçamentário da Receita"""
    try:
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        coug = request.args.get('coug', '')

        if not ano or not mes:
            return jsonify({'erro': 'Ano e mês são obrigatórios'}), 400

        param_style = "?" if db_manager.is_duckdb else ":{}"

        filtro_ug_sql = ""
        if coug:
            filtro_ug_sql = f"AND rs.coug = {param_style.format('coug') if not db_manager.is_duckdb else '?'}"

        # Query principal agora inclui dados por UG
        query = f"""
        WITH dados_agregados AS (
            SELECT
                rs.cocategoriareceita, rs.cofontereceita, rs.cosubfontereceita, rs.coalinea,
                rs.coexercicio, rs.inmes, rs.coug,
                SUM(CASE WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521199999' THEN rs.saldo_contabil_receita ELSE 0 END) as previsao_inicial,
                SUM(CASE WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521299999' THEN rs.saldo_contabil_receita ELSE 0 END) as previsao_atualizada,
                SUM(CASE WHEN rs.cocontacontabil >= '621200000' AND rs.cocontacontabil <= '621399999' THEN rs.saldo_contabil_receita ELSE 0 END) as receita_realizada
            FROM receita_saldo rs
            WHERE rs.cocategoriareceita IN ('1', '2', '7') {filtro_ug_sql}
            GROUP BY 1, 2, 3, 4, 5, 6, 7
        ),
        dados_sumarizados AS (
            SELECT
                cocategoriareceita, cofontereceita, cosubfontereceita, coalinea, coug,
                SUM(CASE WHEN coexercicio = {param_style.format('ano') if not db_manager.is_duckdb else '?'} THEN previsao_inicial ELSE 0 END) as previsao_inicial,
                SUM(CASE WHEN coexercicio = {param_style.format('ano') if not db_manager.is_duckdb else '?'} THEN previsao_atualizada ELSE 0 END) as previsao_atualizada,
                SUM(CASE WHEN coexercicio = {param_style.format('ano') if not db_manager.is_duckdb else '?'} AND inmes <= {param_style.format('mes') if not db_manager.is_duckdb else '?'} THEN receita_realizada ELSE 0 END) as receita_atual,
                SUM(CASE WHEN coexercicio = {param_style.format('ano_anterior') if not db_manager.is_duckdb else '?'} AND inmes <= {param_style.format('mes') if not db_manager.is_duckdb else '?'} THEN receita_realizada ELSE 0 END) as receita_anterior
            FROM dados_agregados
            WHERE coexercicio IN ({param_style.format('ano') if not db_manager.is_duckdb else '?'}, {param_style.format('ano_anterior') if not db_manager.is_duckdb else '?'})
            GROUP BY 1, 2, 3, 4, 5
        )
        SELECT
            ds.cocategoriareceita, ds.cofontereceita,
            COALESCE(ori.nofontereceita, 'Fonte ' || ds.cofontereceita) as nome_fonte,
            ds.cosubfontereceita,
            COALESCE(esp.nosubfontereceita, 'Subfonte ' || ds.cosubfontereceita) as nome_subfonte,
            ds.coalinea,
            COALESCE(ali.noalinea, 'Alínea ' || ds.coalinea) as nome_alinea,
            ds.coug,
            COALESCE(ug.noug, 'UG ' || ds.coug) as nome_ug,
            ds.previsao_inicial, ds.previsao_atualizada, ds.receita_atual, ds.receita_anterior
        FROM dados_sumarizados ds
        LEFT JOIN dim_receita_origem ori ON ds.cofontereceita = CAST(ori.cofontereceita AS VARCHAR)
        LEFT JOIN dim_receita_especie esp ON ds.cosubfontereceita = CAST(esp.cosubfontereceita AS VARCHAR)
        LEFT JOIN dim_receita_alinea ali ON ds.coalinea = CAST(ali.coalinea AS VARCHAR)
        LEFT JOIN dim_unidade_gestora ug ON ds.coug = CAST(ug.coug AS VARCHAR)
        WHERE ABS(ds.previsao_inicial) + ABS(ds.previsao_atualizada) + ABS(ds.receita_atual) + ABS(ds.receita_anterior) > 0.01
        ORDER BY ds.cocategoriareceita, ds.cofontereceita, ds.cosubfontereceita, ds.coalinea, ds.coug
        """
        
        if db_manager.is_duckdb:
            params = [ano, ano, ano, mes, ano - 1, mes, ano, ano - 1]
            if coug:
                params.insert(0, coug)
        else:
            params = {'ano': ano, 'mes': mes, 'ano_anterior': ano - 1}
            if coug:
                params['coug'] = coug

        print(f"Executando query para ano={ano}, mes={mes}, coug={coug}")
        resultados = db_manager.execute_query(query, params=params)
        print(f"Query retornou {len(resultados)} registros")

        resultados_como_tuplas = [tuple(row.values()) for row in resultados]
        dados_hierarquicos = processar_dados_hierarquicos(resultados_como_tuplas)
        
        totais = calcular_totais(dados_hierarquicos)
        
        resultado = {
            'periodo': {
                'ano': ano, 'mes': mes, 'ano_anterior': ano - 1,
                'nome_mes': obter_nome_mes(mes),
                'periodo_completo': f"{obter_nome_mes(mes)}/{ano}"
            },
            'filtros': {
                'coug': coug,
                'nome_coug': obter_nome_ug(coug) if coug else 'Consolidado'
            },
            'dados': dados_hierarquicos,
            'totais': totais,
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Erro em gerar_relatorio: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@balanco_receita.route('/api/lancamentos')
def get_lancamentos():
    """Retorna os lançamentos de uma UG específica"""
    try:
        # Obter parâmetros
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        coug = request.args.get('coug')
        cofontereceita = request.args.get('cofontereceita')
        cosubfontereceita = request.args.get('cosubfontereceita')
        coalinea = request.args.get('coalinea')
        
        if not all([ano, mes, coug, cofontereceita, cosubfontereceita, coalinea]):
            return jsonify({'erro': 'Todos os parâmetros são obrigatórios'}), 400
        
        # Query para buscar lançamentos
        # IMPORTANTE: coug da linha = cougcontab na tabela de lançamentos
        # Filtrar apenas contas contábeis entre 621200000 e 621399999
        param_style = "?" if db_manager.is_duckdb else ":param{}"
        
        query = f"""
        SELECT
            rl.cocontacontabil,
            rl.coug as ug_emitente,
            rl.nudocumento,
            rl.coevento,
            COALESCE(ev.noevento, 'Evento ' || rl.coevento) as nome_evento,
            rl.indebitocredito,
            rl.valancamento,
            rl.dalancamento,
            rl.inmes
        FROM receita_lancamento rl
        LEFT JOIN dim_evento ev ON rl.coevento = CAST(ev.coevento AS VARCHAR)
        WHERE rl.coexercicio = {param_style.format(1) if not db_manager.is_duckdb else '?'}
            AND rl.inmes <= {param_style.format(2) if not db_manager.is_duckdb else '?'}
            AND rl.cougcontab = {param_style.format(3) if not db_manager.is_duckdb else '?'}
            AND rl.cofontereceita = {param_style.format(4) if not db_manager.is_duckdb else '?'}
            AND rl.cosubfontereceita = {param_style.format(5) if not db_manager.is_duckdb else '?'}
            AND rl.coalinea = {param_style.format(6) if not db_manager.is_duckdb else '?'}
            AND rl.cocontacontabil >= '621200000'
            AND rl.cocontacontabil <= '621399999'
        ORDER BY rl.dalancamento DESC, rl.nulancamento DESC
        LIMIT 1001
        """
        
        if db_manager.is_duckdb:
            params = [ano, mes, int(coug), cofontereceita, cosubfontereceita, coalinea]
        else:
            params = {
                'param1': ano,
                'param2': mes,
                'param3': int(coug),
                'param4': cofontereceita,
                'param5': cosubfontereceita,
                'param6': coalinea
            }
        
        print(f"Buscando lançamentos: ano={ano}, mes={mes}, coug={coug}, fonte={cofontereceita}, subfonte={cosubfontereceita}, alinea={coalinea}")
        
        resultados = db_manager.execute_query(query, params=params)
        
        # Verificar se há mais de 1000 registros
        tem_mais_registros = len(resultados) > 1000
        if tem_mais_registros:
            resultados = resultados[:1000]  # Limitar a 1000 registros para exibição
        
        # Formatar resultados
        lancamentos = []
        for row in resultados:
            lancamentos.append({
                'conta_contabil': row['cocontacontabil'],
                'ug_emitente': row['ug_emitente'],
                'documento': row['nudocumento'],
                'evento': f"{row['coevento']} - {row['nome_evento']}",
                'dc': row['indebitocredito'],  # Usar o valor direto do banco
                'valor': float(row['valancamento']),
                'data': row['dalancamento'].strftime('%d/%m/%Y') if row['dalancamento'] else '',
                'mes': row['inmes']
            })
        
        # Calcular totais (C - D)
        total_debito = sum(l['valor'] for l in lancamentos if l['dc'] == 'D')
        total_credito = sum(l['valor'] for l in lancamentos if l['dc'] == 'C')
        
        return jsonify({
            'lancamentos': lancamentos,
            'total_registros': len(lancamentos),
            'tem_mais_registros': tem_mais_registros,
            'totais': {
                'debito': total_debito,
                'credito': total_credito,
                'saldo': total_credito - total_debito
            }
        })
        
    except Exception as e:
        print(f"Erro em get_lancamentos: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def processar_dados_hierarquicos(resultados):
    """Processa os resultados em estrutura hierárquica com 5 níveis (incluindo UGs)"""
    dados = []
    
    # Criar estrutura de categorias
    categorias = {}
    for cat_id, cat_info in CATEGORIA_FONTE_MAP.items():
        categorias[cat_id] = {
            'id': f'cat-{cat_id}',
            'codigo': cat_id,
            'descricao': cat_info['nome'],
            'nivel': 0,
            'tipo': 'categoria',
            'previsao_inicial': 0,
            'previsao_atualizada': 0,
            'receita_atual': 0,
            'receita_anterior': 0,
            'variacao_absoluta': 0,
            'variacao_percentual': 0,
            'expandido': False,
            'tem_filhos': False,
            'fontes_inicio': cat_info['fontes_inicio'],
            'fontes_fim': cat_info['fontes_fim']
        }
    
    # Estrutura hierárquica completa
    fontes_por_categoria = {'1': {}, '2': {}, '7': {}}
    
    for row in resultados:
        # Agora temos 12 campos incluindo UG
        cat_id, fonte_id, nome_fonte, subfonte_id, nome_subfonte, alinea_id, nome_alinea, \
        coug, nome_ug, previsao_inicial, previsao_atualizada, receita_atual, receita_anterior = row
        
        previsao_inicial = float(previsao_inicial or 0)
        previsao_atualizada = float(previsao_atualizada or 0)
        receita_atual = float(receita_atual or 0)
        receita_anterior = float(receita_anterior or 0)
        
        fonte_num = int(fonte_id) if fonte_id and fonte_id.isdigit() else 0
        categoria_id = None
        
        for cid, cinfo in CATEGORIA_FONTE_MAP.items():
            if cinfo['fontes_inicio'] <= fonte_num <= cinfo['fontes_fim']:
                categoria_id = cid
                break
        
        if categoria_id and categoria_id == cat_id:
            # Atualizar totais da categoria
            categorias[categoria_id]['previsao_inicial'] += previsao_inicial
            categorias[categoria_id]['previsao_atualizada'] += previsao_atualizada
            categorias[categoria_id]['receita_atual'] += receita_atual
            categorias[categoria_id]['receita_anterior'] += receita_anterior
            categorias[categoria_id]['tem_filhos'] = True
            
            # Nível 1: Fontes
            if fonte_id not in fontes_por_categoria[categoria_id]:
                fontes_por_categoria[categoria_id][fonte_id] = {
                    'id': f'fonte-{categoria_id}-{fonte_id}',
                    'codigo': fonte_id,
                    'descricao': nome_fonte,
                    'nivel': 1,
                    'tipo': 'fonte',
                    'categoria_pai': categoria_id,
                    'previsao_inicial': 0,
                    'previsao_atualizada': 0,
                    'receita_atual': 0,
                    'receita_anterior': 0,
                    'variacao_absoluta': 0,
                    'variacao_percentual': 0,
                    'expandido': False,
                    'tem_filhos': False,
                    'subfontes': {}
                }
            
            fonte_data = fontes_por_categoria[categoria_id][fonte_id]
            fonte_data['previsao_inicial'] += previsao_inicial
            fonte_data['previsao_atualizada'] += previsao_atualizada
            fonte_data['receita_atual'] += receita_atual
            fonte_data['receita_anterior'] += receita_anterior
            
            # Nível 2: Subfontes
            if subfonte_id and subfonte_id != fonte_id:
                fonte_data['tem_filhos'] = True
                
                if subfonte_id not in fonte_data['subfontes']:
                    fonte_data['subfontes'][subfonte_id] = {
                        'id': f'subfonte-{categoria_id}-{fonte_id}-{subfonte_id}',
                        'codigo': subfonte_id,
                        'descricao': nome_subfonte,
                        'nivel': 2,
                        'tipo': 'subfonte',
                        'categoria_pai': categoria_id,
                        'fonte_pai': fonte_id,
                        'previsao_inicial': 0,
                        'previsao_atualizada': 0,
                        'receita_atual': 0,
                        'receita_anterior': 0,
                        'variacao_absoluta': 0,
                        'variacao_percentual': 0,
                        'expandido': False,
                        'tem_filhos': False,
                        'alineas': {}
                    }
                
                subfonte_data = fonte_data['subfontes'][subfonte_id]
                subfonte_data['previsao_inicial'] += previsao_inicial
                subfonte_data['previsao_atualizada'] += previsao_atualizada
                subfonte_data['receita_atual'] += receita_atual
                subfonte_data['receita_anterior'] += receita_anterior
                
                # Nível 3: Alíneas
                if alinea_id and alinea_id != subfonte_id:
                    subfonte_data['tem_filhos'] = True
                    
                    if alinea_id not in subfonte_data['alineas']:
                        subfonte_data['alineas'][alinea_id] = {
                            'id': f'alinea-{categoria_id}-{fonte_id}-{subfonte_id}-{alinea_id}',
                            'codigo': alinea_id,
                            'descricao': nome_alinea,
                            'nivel': 3,
                            'tipo': 'alinea',
                            'categoria_pai': categoria_id,
                            'fonte_pai': fonte_id,
                            'subfonte_pai': subfonte_id,
                            'previsao_inicial': 0,
                            'previsao_atualizada': 0,
                            'receita_atual': 0,
                            'receita_anterior': 0,
                            'variacao_absoluta': 0,
                            'variacao_percentual': 0,
                            'expandido': False,
                            'tem_filhos': False,
                            'ugs': {}
                        }
                    
                    alinea_data = subfonte_data['alineas'][alinea_id]
                    alinea_data['previsao_inicial'] += previsao_inicial
                    alinea_data['previsao_atualizada'] += previsao_atualizada
                    alinea_data['receita_atual'] += receita_atual
                    alinea_data['receita_anterior'] += receita_anterior
                    
                    # Nível 4: UGs
                    if coug:
                        alinea_data['tem_filhos'] = True
                        
                        variacao_absoluta = receita_atual - receita_anterior
                        variacao_percentual = (variacao_absoluta / abs(receita_anterior) * 100) if receita_anterior != 0 else (100 if receita_atual != 0 else 0)
                        
                        alinea_data['ugs'][coug] = {
                            'id': f'ug-{categoria_id}-{fonte_id}-{subfonte_id}-{alinea_id}-{coug}',
                            'codigo': coug,
                            'descricao': f"{coug} - {nome_ug}",
                            'nivel': 4,
                            'tipo': 'ug',
                            'categoria_pai': categoria_id,
                            'fonte_pai': fonte_id,
                            'subfonte_pai': subfonte_id,
                            'alinea_pai': alinea_id,
                            'previsao_inicial': previsao_inicial,
                            'previsao_atualizada': previsao_atualizada,
                            'receita_atual': receita_atual,
                            'receita_anterior': receita_anterior,
                            'variacao_absoluta': variacao_absoluta,
                            'variacao_percentual': variacao_percentual,
                            'expandido': False,
                            'tem_filhos': False
                        }
    
    # Montar a estrutura final
    for cat_id in ['1', '2', '7']:
        if cat_id in categorias:
            cat_data = categorias[cat_id]
            
            # Calcular variações da categoria
            cat_data['variacao_absoluta'] = cat_data['receita_atual'] - cat_data['receita_anterior']
            cat_data['variacao_percentual'] = (cat_data['variacao_absoluta'] / abs(cat_data['receita_anterior']) * 100) if cat_data['receita_anterior'] != 0 else (100 if cat_data['receita_atual'] != 0 else 0)
            
            if (abs(cat_data['previsao_inicial']) + abs(cat_data['previsao_atualizada']) + abs(cat_data['receita_atual']) + abs(cat_data['receita_anterior'])) > 0.01:
                dados.append(cat_data)
                
                # Adicionar fontes
                for fonte_id in sorted(fontes_por_categoria[cat_id].keys()):
                    fonte_data = fontes_por_categoria[cat_id][fonte_id]
                    
                    fonte_data['variacao_absoluta'] = fonte_data['receita_atual'] - fonte_data['receita_anterior']
                    fonte_data['variacao_percentual'] = (fonte_data['variacao_absoluta'] / abs(fonte_data['receita_anterior']) * 100) if fonte_data['receita_anterior'] != 0 else (100 if fonte_data['receita_atual'] != 0 else 0)
                    dados.append(fonte_data)
                    
                    # Adicionar subfontes
                    for subfonte_id in sorted(fonte_data['subfontes'].keys()):
                        subfonte_data = fonte_data['subfontes'][subfonte_id]
                        
                        subfonte_data['variacao_absoluta'] = subfonte_data['receita_atual'] - subfonte_data['receita_anterior']
                        subfonte_data['variacao_percentual'] = (subfonte_data['variacao_absoluta'] / abs(subfonte_data['receita_anterior']) * 100) if subfonte_data['receita_anterior'] != 0 else (100 if subfonte_data['receita_atual'] != 0 else 0)
                        dados.append(subfonte_data)
                        
                        # Adicionar alíneas
                        for alinea_id in sorted(subfonte_data['alineas'].keys()):
                            alinea_data = subfonte_data['alineas'][alinea_id]
                            
                            alinea_data['variacao_absoluta'] = alinea_data['receita_atual'] - alinea_data['receita_anterior']
                            alinea_data['variacao_percentual'] = (alinea_data['variacao_absoluta'] / abs(alinea_data['receita_anterior']) * 100) if alinea_data['receita_anterior'] != 0 else (100 if alinea_data['receita_atual'] != 0 else 0)
                            dados.append(alinea_data)
                            
                            # Adicionar UGs
                            for coug in sorted(alinea_data['ugs'].keys()):
                                dados.append(alinea_data['ugs'][coug])
    
    return dados

def calcular_totais(dados):
    """Calcula os totais gerais do relatório"""
    totais = {
        'previsao_inicial': 0,
        'previsao_atualizada': 0,
        'receita_atual': 0,
        'receita_anterior': 0,
        'variacao_absoluta': 0,
        'variacao_percentual': 0
    }
    
    for item in dados:
        if item['nivel'] == 0:  # Apenas categorias
            totais['previsao_inicial'] += item['previsao_inicial']
            totais['previsao_atualizada'] += item['previsao_atualizada']
            totais['receita_atual'] += item['receita_atual']
            totais['receita_anterior'] += item['receita_anterior']
    
    totais['variacao_absoluta'] = totais['receita_atual'] - totais['receita_anterior']
    totais['variacao_percentual'] = (totais['variacao_absoluta'] / abs(totais['receita_anterior']) * 100) if totais['receita_anterior'] != 0 else (100 if totais['receita_atual'] != 0 else 0)
    
    return totais

def obter_nome_mes(mes):
    """Retorna o nome do mês"""
    meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    return meses.get(mes, str(mes))

def obter_nome_ug(coug):
    """Obtém o nome da UG"""
    try:
        param_style = "?" if db_manager.is_duckdb else ":coug"
        query = f"SELECT noug FROM dim_unidade_gestora WHERE coug = {param_style}"
        params = [int(coug)] if db_manager.is_duckdb else {'coug': int(coug)}
        
        result = db_manager.execute_query(query, params=params)
        return result[0]['noug'] if result else f"UG {coug}"
    except:
        return f"UG {coug}"

@balanco_receita.route('/api/relatorio-receita-fonte')
def gerar_relatorio_receita_fonte():
    """Gera o relatório de receitas por fonte ou alínea"""
    try:
        from app.modules.relatorio_receita_fonte import RelatorioReceitaFonte
        
        # Obter parâmetros
        tipo = request.args.get('tipo', 'fonte')
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        coug = request.args.get('coug', '')
        tipo_receita = request.args.get('tipo_receita', 'todas') # MODIFICADO: Recebe o novo parâmetro
        
        # Validar parâmetros
        if not ano or not mes:
            return jsonify({'erro': 'Ano e mês são obrigatórios'}), 400
        
        if tipo not in ['fonte', 'receita']:
            return jsonify({'erro': 'Tipo deve ser "fonte" ou "receita"'}), 400
        
        print(f"DEBUG - Gerando relatório receita/fonte: tipo={tipo}, ano={ano}, mes={mes}, coug={coug}, tipo_receita={tipo_receita}")
        
        # Gerar relatório
        relatorio = RelatorioReceitaFonte()
        resultado = relatorio.gerar_relatorio(
            tipo=tipo,
            ano=ano,
            mes=mes,
            coug=coug if coug else None,
            tipo_receita=tipo_receita if tipo_receita != 'todas' else None # MODIFICADO: Passa o filtro
        )
        
        # Adicionar informações extras
        resultado['periodo_formatado'] = f"{mes:02d}/{ano}"
        resultado['data_geracao'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Obter nome da UG se especificada
        if coug:
            try:
                query = "SELECT noug FROM dim_unidade_gestora WHERE coug = ?"
                result = db_manager.execute_query(query, [int(coug)])
                resultado['nome_ug'] = result[0]['noug'] if result else f"UG {coug}"
            except:
                resultado['nome_ug'] = f"UG {coug}"
        else:
            resultado['nome_ug'] = 'Consolidado'
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Erro em gerar_relatorio_receita_fonte: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@balanco_receita.route('/api/lancamentos-excel')
def get_lancamentos_excel():
    """Retorna TODOS os lançamentos para exportação Excel"""
    try:
        # Obter parâmetros
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        coug = request.args.get('coug')
        cofontereceita = request.args.get('cofontereceita')
        cosubfontereceita = request.args.get('cosubfontereceita')
        coalinea = request.args.get('coalinea')
        
        if not all([ano, mes, coug, cofontereceita, cosubfontereceita, coalinea]):
            return jsonify({'erro': 'Todos os parâmetros são obrigatórios'}), 400
        
        # Query SEM LIMIT para pegar TODOS os registros
        param_style = "?" if db_manager.is_duckdb else ":param{}"
        
        query = f"""
        SELECT
            rl.cocontacontabil,
            rl.coug as ug_emitente,
            rl.nudocumento,
            rl.coevento,
            COALESCE(ev.noevento, 'Evento ' || rl.coevento) as nome_evento,
            rl.indebitocredito,
            rl.valancamento,
            rl.dalancamento,
            rl.inmes
        FROM receita_lancamento rl
        LEFT JOIN dim_evento ev ON rl.coevento = CAST(ev.coevento AS VARCHAR)
        WHERE rl.coexercicio = {param_style.format(1) if not db_manager.is_duckdb else '?'}
            AND rl.inmes <= {param_style.format(2) if not db_manager.is_duckdb else '?'}
            AND rl.cougcontab = {param_style.format(3) if not db_manager.is_duckdb else '?'}
            AND rl.cofontereceita = {param_style.format(4) if not db_manager.is_duckdb else '?'}
            AND rl.cosubfontereceita = {param_style.format(5) if not db_manager.is_duckdb else '?'}
            AND rl.coalinea = {param_style.format(6) if not db_manager.is_duckdb else '?'}
            AND rl.cocontacontabil >= '621200000'
            AND rl.cocontacontabil <= '621399999'
        ORDER BY rl.dalancamento DESC, rl.nulancamento DESC
        """
        
        if db_manager.is_duckdb:
            params = [ano, mes, int(coug), cofontereceita, cosubfontereceita, coalinea]
        else:
            params = {
                'param1': ano,
                'param2': mes,
                'param3': int(coug),
                'param4': cofontereceita,
                'param5': cosubfontereceita,
                'param6': coalinea
            }
        
        print(f"Buscando TODOS os lançamentos para Excel: ano={ano}, mes={mes}, coug={coug}")
        
        resultados = db_manager.execute_query(query, params=params)
        
        # Formatar resultados
        lancamentos = []
        for row in resultados:
            lancamentos.append({
                'conta_contabil': row['cocontacontabil'],
                'ug_emitente': row['ug_emitente'],
                'documento': row['nudocumento'],
                'evento': f"{row['coevento']} - {row['nome_evento']}",
                'dc': row['indebitocredito'],
                'valor': float(row['valancamento']),
                'data': row['dalancamento'].strftime('%d/%m/%Y') if row['dalancamento'] else '',
                'mes': row['inmes']
            })
        
        # Calcular totais
        total_debito = sum(l['valor'] for l in lancamentos if l['dc'] == 'D')
        total_credito = sum(l['valor'] for l in lancamentos if l['dc'] == 'C')
        
        return jsonify({
            'lancamentos': lancamentos,
            'total_registros': len(lancamentos),
            'totais': {
                'debito': total_debito,
                'credito': total_credito,
                'saldo': total_credito - total_debito
            }
        })
        
    except Exception as e:
        print(f"Erro em get_lancamentos_excel: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500
def gerar_relatorio_receita_fonte():
    """Gera o relatório de receitas por fonte ou alínea"""
    try:
        from app.modules.relatorio_receita_fonte import RelatorioReceitaFonte
        
        # Obter parâmetros
        tipo = request.args.get('tipo', 'fonte')
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        coug = request.args.get('coug', '')
        tipo_receita = request.args.get('tipo_receita', 'todas') # MODIFICADO: Recebe o novo parâmetro
        
        # Validar parâmetros
        if not ano or not mes:
            return jsonify({'erro': 'Ano e mês são obrigatórios'}), 400
        
        if tipo not in ['fonte', 'receita']:
            return jsonify({'erro': 'Tipo deve ser "fonte" ou "receita"'}), 400
        
        print(f"DEBUG - Gerando relatório receita/fonte: tipo={tipo}, ano={ano}, mes={mes}, coug={coug}, tipo_receita={tipo_receita}")
        
        # Gerar relatório
        relatorio = RelatorioReceitaFonte()
        resultado = relatorio.gerar_relatorio(
            tipo=tipo,
            ano=ano,
            mes=mes,
            coug=coug if coug else None,
            tipo_receita=tipo_receita if tipo_receita != 'todas' else None # MODIFICADO: Passa o filtro
        )
        
        # Adicionar informações extras
        resultado['periodo_formatado'] = f"{mes:02d}/{ano}"
        resultado['data_geracao'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Obter nome da UG se especificada
        if coug:
            try:
                query = "SELECT noug FROM dim_unidade_gestora WHERE coug = ?"
                result = db_manager.execute_query(query, [int(coug)])
                resultado['nome_ug'] = result[0]['noug'] if result else f"UG {coug}"
            except:
                resultado['nome_ug'] = f"UG {coug}"
        else:
            resultado['nome_ug'] = 'Consolidado'
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Erro em gerar_relatorio_receita_fonte: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500
    
@balanco_receita.route('/api/lancamentos-fonte-alinea')
def get_lancamentos_fonte_alinea():
    """Retorna os lançamentos por fonte e alínea (sem UG específica)"""
    try:
        # Obter parâmetros
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        cofontereceita = request.args.get('cofontereceita')
        coalinea = request.args.get('coalinea')
        
        if not all([ano, mes, cofontereceita, coalinea]):
            return jsonify({'erro': 'Todos os parâmetros são obrigatórios'}), 400
        
        # Query para buscar lançamentos agrupados por UG
        param_style = "?" if db_manager.is_duckdb else ":param{}"
        
        query = f"""
        SELECT
            rl.cocontacontabil,
            rl.coug as ug_emitente,
            rl.cougcontab,
            COALESCE(ug.noug, 'UG ' || rl.cougcontab) as nome_ug,
            rl.nudocumento,
            rl.coevento,
            COALESCE(ev.noevento, 'Evento ' || rl.coevento) as nome_evento,
            rl.indebitocredito,
            rl.valancamento,
            rl.dalancamento,
            rl.inmes
        FROM receita_lancamento rl
        LEFT JOIN dim_evento ev ON rl.coevento = CAST(ev.coevento AS VARCHAR)
        LEFT JOIN dim_unidade_gestora ug ON rl.cougcontab = CAST(ug.coug AS VARCHAR)
        WHERE rl.coexercicio = {param_style.format(1) if not db_manager.is_duckdb else '?'}
            AND rl.inmes <= {param_style.format(2) if not db_manager.is_duckdb else '?'}
            AND rl.cofontereceita = {param_style.format(3) if not db_manager.is_duckdb else '?'}
            AND rl.coalinea = {param_style.format(4) if not db_manager.is_duckdb else '?'}
            AND rl.cocontacontabil >= '621200000'
            AND rl.cocontacontabil <= '621399999'
        ORDER BY rl.cougcontab, rl.dalancamento DESC, rl.nulancamento DESC
        LIMIT 1001
        """
        
        if db_manager.is_duckdb:
            params = [ano, mes, cofontereceita, coalinea]
        else:
            params = {
                'param1': ano,
                'param2': mes,
                'param3': cofontereceita,
                'param4': coalinea
            }
        
        print(f"Buscando lançamentos: ano={ano}, mes={mes}, fonte={cofontereceita}, alinea={coalinea}")
        
        resultados = db_manager.execute_query(query, params=params)
        
        # Verificar se há mais de 1000 registros
        tem_mais_registros = len(resultados) > 1000
        if tem_mais_registros:
            resultados = resultados[:1000]
        
        # Formatar resultados
        lancamentos = []
        for row in resultados:
            lancamentos.append({
                'conta_contabil': row['cocontacontabil'],
                'ug_emitente': row['ug_emitente'],
                'ug_contabil': f"{row['cougcontab']} - {row['nome_ug']}",
                'documento': row['nudocumento'],
                'evento': f"{row['coevento']} - {row['nome_evento']}",
                'dc': row['indebitocredito'],
                'valor': float(row['valancamento']),
                'data': row['dalancamento'].strftime('%d/%m/%Y') if row['dalancamento'] else '',
                'mes': row['inmes']
            })
        
        # Calcular totais
        total_debito = sum(l['valor'] for l in lancamentos if l['dc'] == 'D')
        total_credito = sum(l['valor'] for l in lancamentos if l['dc'] == 'C')
        
        return jsonify({
            'lancamentos': lancamentos,
            'total_registros': len(lancamentos),
            'tem_mais_registros': tem_mais_registros,
            'totais': {
                'debito': total_debito,
                'credito': total_credito,
                'saldo': total_credito - total_debito
            }
        })
        
    except Exception as e:
        print(f"Erro em get_lancamentos_fonte_alinea: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500