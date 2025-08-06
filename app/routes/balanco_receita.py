"""
Blueprint para Balanço Orçamentário da Receita
Adaptado do sistema original para trabalhar com DuckDB
"""
from flask import Blueprint, render_template, jsonify, request, current_app
from app.db_manager import db_manager # Usando o db_manager central
from datetime import datetime
import traceback

# Criar blueprint
balanco_receita = Blueprint('balanco_receita', __name__)

# Mapeamento das categorias e suas fontes
CATEGORIA_FONTE_MAP = {
    '1': {  # Receitas Correntes
        'nome': 'Receitas Correntes',
        'fontes_inicio': 11,
        'fontes_fim': 19
    },
    '2': {  # Receitas de Capital
        'nome': 'Receitas de Capital',
        'fontes_inicio': 21,
        'fontes_fim': 29
    },
    '7': {  # Receitas Correntes Intra-Orçamentárias
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
            
            # Adaptação para ambos os bancos
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

        # Define o estilo do placeholder para a query ('?' para DuckDB, ':nome' para Psql)
        param_style = "?" if db_manager.is_duckdb else ":{}"

        filtro_ug_sql = ""
        if coug:
            filtro_ug_sql = f"AND rs.coug = {param_style.format('coug') if not db_manager.is_duckdb else '?'}"

        query = f"""
        WITH dados_agregados AS (
            SELECT
                rs.cocategoriareceita, rs.cofontereceita, rs.cosubfontereceita, rs.coalinea,
                rs.coexercicio, rs.inmes,
                SUM(CASE WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521199999' THEN rs.saldo_contabil_receita ELSE 0 END) as previsao_inicial,
                SUM(CASE WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521299999' THEN rs.saldo_contabil_receita ELSE 0 END) as previsao_atualizada,
                SUM(CASE WHEN rs.cocontacontabil >= '621200000' AND rs.cocontacontabil <= '621399999' THEN rs.saldo_contabil_receita ELSE 0 END) as receita_realizada
            FROM receita_saldo rs
            WHERE rs.cocategoriareceita IN ('1', '2', '7') {filtro_ug_sql}
            GROUP BY 1, 2, 3, 4, 5, 6
        ),
        dados_sumarizados AS (
            SELECT
                cocategoriareceita, cofontereceita, cosubfontereceita, coalinea,
                SUM(CASE WHEN coexercicio = {param_style.format('ano') if not db_manager.is_duckdb else '?'} THEN previsao_inicial ELSE 0 END) as previsao_inicial,
                SUM(CASE WHEN coexercicio = {param_style.format('ano') if not db_manager.is_duckdb else '?'} THEN previsao_atualizada ELSE 0 END) as previsao_atualizada,
                SUM(CASE WHEN coexercicio = {param_style.format('ano') if not db_manager.is_duckdb else '?'} AND inmes <= {param_style.format('mes') if not db_manager.is_duckdb else '?'} THEN receita_realizada ELSE 0 END) as receita_atual,
                SUM(CASE WHEN coexercicio = {param_style.format('ano_anterior') if not db_manager.is_duckdb else '?'} AND inmes <= {param_style.format('mes') if not db_manager.is_duckdb else '?'} THEN receita_realizada ELSE 0 END) as receita_anterior
            FROM dados_agregados
            WHERE coexercicio IN ({param_style.format('ano') if not db_manager.is_duckdb else '?'}, {param_style.format('ano_anterior') if not db_manager.is_duckdb else '?'})
            GROUP BY 1, 2, 3, 4
        )
        SELECT
            ds.cocategoriareceita, ds.cofontereceita,
            COALESCE(ori.nofontereceita, 'Fonte ' || ds.cofontereceita) as nome_fonte,
            ds.cosubfontereceita,
            COALESCE(esp.nosubfontereceita, 'Subfonte ' || ds.cosubfontereceita) as nome_subfonte,
            ds.coalinea,
            COALESCE(ali.noalinea, 'Alínea ' || ds.coalinea) as nome_alinea,
            ds.previsao_inicial, ds.previsao_atualizada, ds.receita_atual, ds.receita_anterior
        FROM dados_sumarizados ds
        LEFT JOIN dim_receita_origem ori ON ds.cofontereceita = CAST(ori.cofontereceita AS VARCHAR)
        LEFT JOIN dim_receita_especie esp ON ds.cosubfontereceita = CAST(esp.cosubfontereceita AS VARCHAR)
        LEFT JOIN dim_receita_alinea ali ON ds.coalinea = CAST(ali.coalinea AS VARCHAR)
        WHERE ABS(ds.previsao_inicial) + ABS(ds.previsao_atualizada) + ABS(ds.receita_atual) + ABS(ds.receita_anterior) > 0.01
        ORDER BY ds.cocategoriareceita, ds.cofontereceita, ds.cosubfontereceita, ds.coalinea
        """
        
        # Monta os parâmetros na ordem correta que a query espera
        if db_manager.is_duckdb:
            params = [ano, ano, ano, mes, ano - 1, mes, ano, ano - 1]
            if coug:
                params.insert(0, coug) # Adiciona no início da lista se existir
        else: # PostgreSQL
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

# ... (o resto das funções, como processar_dados_hierarquicos, calcular_totais, etc., continua IGUAL) ...
def processar_dados_hierarquicos(resultados):
    """Processa os resultados em estrutura hierárquica correta com 4 níveis"""
    dados = []
    
    # Primeiro, criar a estrutura de categorias
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
            'expandido': False,  # Sem botão de expansão
            'tem_filhos': False,
            'fontes_inicio': cat_info['fontes_inicio'],
            'fontes_fim': cat_info['fontes_fim']
        }
    
    # Processar resultados por fonte, subfonte e alínea
    fontes_por_categoria = {'1': {}, '2': {}, '7': {}}
    
    for row in resultados:
        cat_id, fonte_id, nome_fonte, subfonte_id, nome_subfonte, alinea_id, nome_alinea, \
        previsao_inicial, previsao_atualizada, receita_atual, receita_anterior = row
        
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
            categorias[categoria_id]['previsao_inicial'] += previsao_inicial
            categorias[categoria_id]['previsao_atualizada'] += previsao_atualizada
            categorias[categoria_id]['receita_atual'] += receita_atual
            categorias[categoria_id]['receita_anterior'] += receita_anterior
            categorias[categoria_id]['tem_filhos'] = True
            
            if fonte_id not in fontes_por_categoria[categoria_id]:
                fontes_por_categoria[categoria_id][fonte_id] = {
                    'id': f'fonte-{categoria_id}-{fonte_id}', 'codigo': fonte_id, 'descricao': nome_fonte,
                    'nivel': 1, 'tipo': 'fonte', 'categoria_pai': categoria_id,
                    'previsao_inicial': 0, 'previsao_atualizada': 0, 'receita_atual': 0, 'receita_anterior': 0,
                    'variacao_absoluta': 0, 'variacao_percentual': 0, 'expandido': False, 'tem_filhos': False, 'subfontes': {}
                }
            
            fonte_data = fontes_por_categoria[categoria_id][fonte_id]
            fonte_data['previsao_inicial'] += previsao_inicial
            fonte_data['previsao_atualizada'] += previsao_atualizada
            fonte_data['receita_atual'] += receita_atual
            fonte_data['receita_anterior'] += receita_anterior
            
            if subfonte_id and subfonte_id != fonte_id:
                fonte_data['tem_filhos'] = True
                
                if subfonte_id not in fonte_data['subfontes']:
                    fonte_data['subfontes'][subfonte_id] = {
                        'id': f'subfonte-{categoria_id}-{fonte_id}-{subfonte_id}', 'codigo': subfonte_id, 'descricao': nome_subfonte,
                        'nivel': 2, 'tipo': 'subfonte', 'categoria_pai': categoria_id, 'fonte_pai': fonte_id,
                        'previsao_inicial': 0, 'previsao_atualizada': 0, 'receita_atual': 0, 'receita_anterior': 0,
                        'variacao_absoluta': 0, 'variacao_percentual': 0, 'expandido': False, 'tem_filhos': False, 'alineas': {}
                    }
                
                subfonte_data = fonte_data['subfontes'][subfonte_id]
                subfonte_data['previsao_inicial'] += previsao_inicial
                subfonte_data['previsao_atualizada'] += previsao_atualizada
                subfonte_data['receita_atual'] += receita_atual
                subfonte_data['receita_anterior'] += receita_anterior
                
                if alinea_id and alinea_id != subfonte_id:
                    subfonte_data['tem_filhos'] = True
                    
                    variacao_absoluta = receita_atual - receita_anterior
                    variacao_percentual = (variacao_absoluta / abs(receita_anterior) * 100) if receita_anterior != 0 else (100 if receita_atual != 0 else 0)
                    
                    subfonte_data['alineas'][alinea_id] = {
                        'id': f'alinea-{categoria_id}-{fonte_id}-{subfonte_id}-{alinea_id}', 'codigo': alinea_id, 'descricao': nome_alinea,
                        'nivel': 3, 'tipo': 'alinea', 'categoria_pai': categoria_id, 'fonte_pai': fonte_id, 'subfonte_pai': subfonte_id,
                        'previsao_inicial': previsao_inicial, 'previsao_atualizada': previsao_atualizada, 'receita_atual': receita_atual, 'receita_anterior': receita_anterior,
                        'variacao_absoluta': variacao_absoluta, 'variacao_percentual': variacao_percentual, 'expandido': False, 'tem_filhos': False
                    }
    
    for cat_id in ['1', '2', '7']:
        if cat_id in categorias:
            cat_data = categorias[cat_id]
            
            cat_data['variacao_absoluta'] = cat_data['receita_atual'] - cat_data['receita_anterior']
            cat_data['variacao_percentual'] = (cat_data['variacao_absoluta'] / abs(cat_data['receita_anterior']) * 100) if cat_data['receita_anterior'] != 0 else (100 if cat_data['receita_atual'] != 0 else 0)
            
            if (abs(cat_data['previsao_inicial']) + abs(cat_data['previsao_atualizada']) + abs(cat_data['receita_atual']) + abs(cat_data['receita_anterior'])) > 0.01:
                dados.append(cat_data)
                
                for fonte_id in sorted(fontes_por_categoria[cat_id].keys()):
                    fonte_data = fontes_por_categoria[cat_id][fonte_id]
                    
                    fonte_data['variacao_absoluta'] = fonte_data['receita_atual'] - fonte_data['receita_anterior']
                    fonte_data['variacao_percentual'] = (fonte_data['variacao_absoluta'] / abs(fonte_data['receita_anterior']) * 100) if fonte_data['receita_anterior'] != 0 else (100 if fonte_data['receita_atual'] != 0 else 0)
                    dados.append(fonte_data)
                    
                    for subfonte_id in sorted(fonte_data['subfontes'].keys()):
                        subfonte_data = fonte_data['subfontes'][subfonte_id]
                        
                        subfonte_data['variacao_absoluta'] = subfonte_data['receita_atual'] - subfonte_data['receita_anterior']
                        subfonte_data['variacao_percentual'] = (subfonte_data['variacao_absoluta'] / abs(subfonte_data['receita_anterior']) * 100) if subfonte_data['receita_anterior'] != 0 else (100 if subfonte_data['receita_atual'] != 0 else 0)
                        dados.append(subfonte_data)
                        
                        for alinea_id in sorted(subfonte_data['alineas'].keys()):
                            dados.append(subfonte_data['alineas'][alinea_id])
    return dados

def calcular_totais(dados):
    """Calcula os totais gerais do relatório"""
    totais = {
        'previsao_inicial': 0, 'previsao_atualizada': 0, 'receita_atual': 0,
        'receita_anterior': 0, 'variacao_absoluta': 0, 'variacao_percentual': 0
    }
    for item in dados:
        if item['nivel'] == 0:
            totais['previsao_inicial'] += item['previsao_inicial']
            totais['previsao_atualizada'] += item['previsao_atualizada']
            totais['receita_atual'] += item['receita_atual']
            totais['receita_anterior'] += item['receita_anterior']
    
    totais['variacao_absoluta'] = totais['receita_atual'] - totais['receita_anterior']
    totais['variacao_percentual'] = (totais['variacao_absoluta'] / abs(totais['receita_anterior']) * 100) if totais['receita_anterior'] != 0 else (100 if totais['receita_atual'] != 0 else 0)
    return totais

def obter_nome_mes(mes):
    """Retorna o nome do mês"""
    meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
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