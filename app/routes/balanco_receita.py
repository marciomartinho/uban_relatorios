"""
Blueprint para Balanço Orçamentário da Receita
Adaptado do sistema original para trabalhar com DuckDB
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.database_duckdb import db_duckdb
from datetime import datetime
import traceback

# Criar blueprint
balanco_receita = Blueprint('balanco_receita', __name__)

# Mapeamento dos filtros de receita para códigos de categoria/fonte
FILTROS_RECEITA = {
    'todas': {'descricao': 'Todas as Receitas', 'categorias': None, 'fontes': None},
    'tributarias': {'descricao': 'Tributárias', 'categorias': ['1'], 'fontes': ['11']},
    'contribuicoes': {'descricao': 'Contribuições', 'categorias': ['1'], 'fontes': ['12']},
    'patrimonial': {'descricao': 'Patrimonial', 'categorias': ['1'], 'fontes': ['13']},
    'agropecuaria': {'descricao': 'Agropecuária', 'categorias': ['1'], 'fontes': ['14']},
    'industrial': {'descricao': 'Industrial', 'categorias': ['1'], 'fontes': ['15']},
    'servicos': {'descricao': 'Serviços', 'categorias': ['1'], 'fontes': ['16']},
    'transf_correntes': {'descricao': 'Transferências Correntes', 'categorias': ['1'], 'fontes': ['17']},
    'outras_correntes': {'descricao': 'Outras Receitas Correntes', 'categorias': ['1'], 'fontes': ['19']},
    'op_credito': {'descricao': 'Operações de Crédito', 'categorias': ['2'], 'fontes': ['21']},
    'alienacao_bens': {'descricao': 'Alienação de Bens', 'categorias': ['2'], 'fontes': ['22']},
    'amortizacao': {'descricao': 'Amortização de Empréstimos', 'categorias': ['2'], 'fontes': ['23']},
    'transf_capital': {'descricao': 'Transferências de Capital', 'categorias': ['2'], 'fontes': ['24']}
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
        conn = db_duckdb.get_connection()
        
        # Buscar anos disponíveis
        anos_query = """
        SELECT DISTINCT coexercicio 
        FROM receita_saldo 
        ORDER BY coexercicio DESC
        """
        anos = [row[0] for row in conn.execute(anos_query).fetchall()]
        
        # Buscar meses do ano mais recente
        if anos:
            ano_atual = anos[0]
            meses_query = f"""
            SELECT DISTINCT inmes 
            FROM receita_saldo 
            WHERE coexercicio = {ano_atual}
            ORDER BY inmes DESC
            """
            meses = [row[0] for row in conn.execute(meses_query).fetchall()]
        else:
            meses = []
        
        # Buscar UGs (Unidades Gestoras) com movimento
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
        for row in conn.execute(ugs_query).fetchall():
            ugs.append({
                'codigo': row[0],
                'descricao': f"{row[0]} - {row[1]}"
            })
        
        conn.close()
        
        # Filtros de tipo de receita
        filtros_receita = [
            {'valor': key, 'nome': value['descricao']} 
            for key, value in FILTROS_RECEITA.items()
        ]
        
        return jsonify({
            'anos': anos,
            'meses': meses,
            'ugs': ugs,
            'filtros_receita': filtros_receita
        })
        
    except Exception as e:
        print(f"Erro em get_filtros: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@balanco_receita.route('/api/gerar-relatorio')
def gerar_relatorio():
    """Gera o relatório de Balanço Orçamentário da Receita"""
    try:
        # Pegar parâmetros
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        coug = request.args.get('coug', '')
        filtro_receita = request.args.get('filtro', 'todas')
        
        if not ano or not mes:
            return jsonify({'erro': 'Ano e mês são obrigatórios'}), 400
        
        conn = db_duckdb.get_connection()
        
        # Construir filtro de UG
        filtro_ug = f"AND rs.coug = '{coug}'" if coug else ""
        
        # Construir filtro de tipo de receita
        filtro_tipo = ""
        if filtro_receita != 'todas' and filtro_receita in FILTROS_RECEITA:
            config_filtro = FILTROS_RECEITA[filtro_receita]
            if config_filtro['categorias']:
                cats = ','.join([f"'{c}'" for c in config_filtro['categorias']])
                filtro_tipo += f" AND rs.cocategoriareceita IN ({cats})"
            if config_filtro['fontes']:
                fontes = ','.join([f"'{f}'" for f in config_filtro['fontes']])
                filtro_tipo += f" AND rs.cofontereceita IN ({fontes})"
        
        # Query principal para buscar dados agregados
        query = f"""
        WITH dados_agregados AS (
            SELECT
                rs.cocategoriareceita,
                COALESCE(cat.nocategoriareceita, 'Categoria ' || rs.cocategoriareceita) as nome_categoria,
                rs.cofontereceita,
                COALESCE(ori.nofontereceita, 'Fonte ' || rs.cofontereceita) as nome_fonte,
                rs.cosubfontereceita,
                COALESCE(esp.nosubfontereceita, 'Subfonte ' || rs.cosubfontereceita) as nome_subfonte,
                rs.coalinea,
                COALESCE(ali.noalinea, 'Alínea ' || rs.coalinea) as nome_alinea,
                rs.coexercicio,
                rs.inmes,
                -- Previsão Inicial (contas 521100000 a 521199999)
                SUM(CASE 
                    WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521199999' 
                    THEN rs.saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_inicial,
                -- Previsão Atualizada (contas 521100000 a 521299999)
                SUM(CASE 
                    WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521299999' 
                    THEN rs.saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_atualizada,
                -- Receita Realizada (contas 621200000 a 621399999)
                SUM(CASE 
                    WHEN rs.cocontacontabil >= '621200000' AND rs.cocontacontabil <= '621399999' 
                    THEN rs.saldo_contabil_receita 
                    ELSE 0 
                END) as receita_realizada
            FROM receita_saldo rs
            LEFT JOIN dim_receita_categoria cat ON rs.cocategoriareceita = CAST(cat.cocategoriareceita AS VARCHAR)
            LEFT JOIN dim_receita_origem ori ON rs.cofontereceita = CAST(ori.cofontereceita AS VARCHAR)
            LEFT JOIN dim_receita_especie esp ON rs.cosubfontereceita = CAST(esp.cosubfontereceita AS VARCHAR)
            LEFT JOIN dim_receita_alinea ali ON rs.coalinea = CAST(ali.coalinea AS VARCHAR)
            WHERE 1=1 {filtro_ug} {filtro_tipo}
            GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
        ),
        dados_sumarizados AS (
            SELECT
                cocategoriareceita,
                nome_categoria,
                cofontereceita,
                nome_fonte,
                cosubfontereceita,
                nome_subfonte,
                coalinea,
                nome_alinea,
                -- Valores do ano atual
                SUM(CASE WHEN coexercicio = {ano} THEN previsao_inicial ELSE 0 END) as previsao_inicial,
                SUM(CASE WHEN coexercicio = {ano} THEN previsao_atualizada ELSE 0 END) as previsao_atualizada,
                SUM(CASE WHEN coexercicio = {ano} AND inmes <= {mes} THEN receita_realizada ELSE 0 END) as receita_atual,
                -- Valores do ano anterior
                SUM(CASE WHEN coexercicio = {ano-1} AND inmes <= {mes} THEN receita_realizada ELSE 0 END) as receita_anterior
            FROM dados_agregados
            WHERE coexercicio IN ({ano}, {ano-1})
            GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
        )
        SELECT * FROM dados_sumarizados
        WHERE ABS(previsao_inicial) + ABS(previsao_atualizada) + ABS(receita_atual) + ABS(receita_anterior) > 0.01
        ORDER BY cocategoriareceita, cofontereceita, cosubfontereceita, coalinea
        """
        
        print(f"Executando query para ano={ano}, mes={mes}, coug={coug}, filtro={filtro_receita}")
        
        # Executar query
        cursor = conn.execute(query)
        resultados = cursor.fetchall()
        
        print(f"Query retornou {len(resultados)} registros")
        
        # Processar resultados em estrutura hierárquica
        dados_hierarquicos = processar_dados_hierarquicos(resultados)
        
        # Calcular totais
        totais = calcular_totais(dados_hierarquicos)
        
        resultado = {
            'periodo': {
                'ano': ano,
                'mes': mes,
                'ano_anterior': ano - 1,
                'nome_mes': obter_nome_mes(mes),
                'periodo_completo': f"{obter_nome_mes(mes)}/{ano}"
            },
            'filtros': {
                'coug': coug,
                'nome_coug': obter_nome_ug(conn, coug) if coug else 'Consolidado',
                'filtro_receita': filtro_receita,
                'filtro_descricao': FILTROS_RECEITA[filtro_receita]['descricao']
            },
            'dados': dados_hierarquicos,
            'totais': totais,
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
        conn.close()
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Erro em gerar_relatorio: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def processar_dados_hierarquicos(resultados):
    """Processa os resultados em estrutura hierárquica"""
    dados = []
    
    # Agrupar por categoria primeiro
    categorias = {}
    
    for row in resultados:
        cat_id = row[0]  # cocategoriareceita
        cat_nome = row[1]  # nome_categoria
        fonte_id = row[2]  # cofontereceita
        fonte_nome = row[3]  # nome_fonte
        subfonte_id = row[4]  # cosubfontereceita
        subfonte_nome = row[5]  # nome_subfonte
        alinea_id = row[6]  # coalinea
        alinea_nome = row[7]  # nome_alinea
        
        # Valores
        previsao_inicial = float(row[8] or 0)
        previsao_atualizada = float(row[9] or 0)
        receita_atual = float(row[10] or 0)
        receita_anterior = float(row[11] or 0)
        
        # Criar estrutura se não existir
        if cat_id not in categorias:
            categorias[cat_id] = {
                'id': f'cat-{cat_id}',
                'codigo': cat_id,
                'descricao': cat_nome,
                'nivel': 0,
                'tipo': 'categoria',
                'previsao_inicial': 0,
                'previsao_atualizada': 0,
                'receita_atual': 0,
                'receita_anterior': 0,
                'variacao_absoluta': 0,
                'variacao_percentual': 0,
                'expandido': False,
                'tem_filhos': True,
                'filhos': {}
            }
        
        # Adicionar valores à categoria
        categorias[cat_id]['previsao_inicial'] += previsao_inicial
        categorias[cat_id]['previsao_atualizada'] += previsao_atualizada
        categorias[cat_id]['receita_atual'] += receita_atual
        categorias[cat_id]['receita_anterior'] += receita_anterior
        
        # Adicionar fonte se não existir
        if fonte_id and fonte_id not in categorias[cat_id]['filhos']:
            categorias[cat_id]['filhos'][fonte_id] = {
                'id': f'fonte-{cat_id}-{fonte_id}',
                'codigo': fonte_id,
                'descricao': fonte_nome,
                'nivel': 1,
                'tipo': 'fonte',
                'previsao_inicial': previsao_inicial,
                'previsao_atualizada': previsao_atualizada,
                'receita_atual': receita_atual,
                'receita_anterior': receita_anterior,
                'variacao_absoluta': 0,
                'variacao_percentual': 0,
                'expandido': False,
                'tem_filhos': False
            }
    
    # Converter para lista e calcular variações
    for cat_data in categorias.values():
        # Calcular variação da categoria
        cat_data['variacao_absoluta'] = cat_data['receita_atual'] - cat_data['receita_anterior']
        if cat_data['receita_anterior'] != 0:
            cat_data['variacao_percentual'] = (cat_data['variacao_absoluta'] / abs(cat_data['receita_anterior'])) * 100
        else:
            cat_data['variacao_percentual'] = 100 if cat_data['receita_atual'] != 0 else 0
        
        # Adicionar categoria à lista
        dados.append(cat_data)
        
        # Adicionar fontes
        for fonte_data in cat_data['filhos'].values():
            # Calcular variação da fonte
            fonte_data['variacao_absoluta'] = fonte_data['receita_atual'] - fonte_data['receita_anterior']
            if fonte_data['receita_anterior'] != 0:
                fonte_data['variacao_percentual'] = (fonte_data['variacao_absoluta'] / abs(fonte_data['receita_anterior'])) * 100
            else:
                fonte_data['variacao_percentual'] = 100 if fonte_data['receita_atual'] != 0 else 0
            
            dados.append(fonte_data)
    
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
    
    # Somar apenas categorias (nível 0)
    for item in dados:
        if item['nivel'] == 0:
            totais['previsao_inicial'] += item['previsao_inicial']
            totais['previsao_atualizada'] += item['previsao_atualizada']
            totais['receita_atual'] += item['receita_atual']
            totais['receita_anterior'] += item['receita_anterior']
    
    # Calcular variações
    totais['variacao_absoluta'] = totais['receita_atual'] - totais['receita_anterior']
    if totais['receita_anterior'] != 0:
        totais['variacao_percentual'] = (totais['variacao_absoluta'] / abs(totais['receita_anterior'])) * 100
    else:
        totais['variacao_percentual'] = 100 if totais['receita_atual'] != 0 else 0
    
    return totais

# Funções auxiliares
def obter_nome_mes(mes):
    """Retorna o nome do mês"""
    meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    return meses.get(mes, str(mes))

def obter_nome_ug(conn, coug):
    """Obtém o nome da UG"""
    try:
        query = """
        SELECT noug 
        FROM dim_unidade_gestora 
        WHERE coug = ?
        """
        result = conn.execute(query, [coug]).fetchone()
        return result[0] if result else f"UG {coug}"
    except:
        return f"UG {coug}"