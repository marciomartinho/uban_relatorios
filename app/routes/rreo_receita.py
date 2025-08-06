"""
Blueprint para relatórios RREO - Receita
Adaptado para trabalhar com db_manager (DuckDB/PostgreSQL)
"""
from flask import Blueprint, render_template, jsonify, request
from app.db_manager import db_manager
from datetime import datetime
import traceback

# Criar blueprint
rreo_receita = Blueprint('rreo_receita', __name__)

# Mapeamento de bimestres
BIMESTRES = {
    1: {'meses': [1, 2], 'nome': '1º Bimestre'},
    2: {'meses': [3, 4], 'nome': '2º Bimestre'},
    3: {'meses': [5, 6], 'nome': '3º Bimestre'},
    4: {'meses': [7, 8], 'nome': '4º Bimestre'},
    5: {'meses': [9, 10], 'nome': '5º Bimestre'},
    6: {'meses': [11, 12], 'nome': '6º Bimestre'}
}

@rreo_receita.route('/rreo-receita')
def rreo_receita_page():
    """Página do demonstrativo RREO de Receita"""
    return render_template('rreo_receita/rreo_receita.html',
                         title='RREO - Demonstrativo de Receitas')

@rreo_receita.route('/api/filtros')
def get_filtros():
    """Retorna os filtros disponíveis para o relatório"""
    try:
        # Query para buscar anos disponíveis
        anos_query = """
        SELECT DISTINCT coexercicio
        FROM receita_saldo
        ORDER BY coexercicio DESC
        """
        
        anos_result = db_manager.execute_query(anos_query)
        anos = [row['coexercicio'] for row in anos_result]
        
        return jsonify({
            'anos': anos,
            'bimestres': [
                {'valor': k, 'nome': v['nome']}
                for k, v in BIMESTRES.items()
            ]
        })
        
    except Exception as e:
        print(f"Erro em get_filtros: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@rreo_receita.route('/api/gerar-relatorio')
def gerar_relatorio():
    """Gera o relatório RREO de Receita"""
    try:
        # Pegar parâmetros
        ano = request.args.get('ano')
        bimestre = int(request.args.get('bimestre', 1))
        
        if not ano:
            return jsonify({'erro': 'Parâmetros obrigatórios: ano, bimestre'}), 400
        
        # Validar bimestre
        if bimestre not in BIMESTRES:
            return jsonify({'erro': 'Bimestre inválido'}), 400
        
        # Determinar meses do bimestre e até o bimestre
        meses_bimestre = BIMESTRES[bimestre]['meses']
        meses_ate_bimestre = list(range(1, max(meses_bimestre) + 1))
        
        # Buscar dados de receitas correntes (exceto intra)
        receitas_correntes = buscar_receitas_por_categoria(
            ano, meses_bimestre, meses_ate_bimestre,
            ['11', '12', '13', '14', '15', '16', '17', '18', '19']
        )
        
        # Buscar dados de receitas de capital (exceto intra)
        receitas_capital = buscar_receitas_por_categoria(
            ano, meses_bimestre, meses_ate_bimestre,
            ['21', '22', '23', '24', '25', '26', '27', '28', '29']
        )
        
        # Buscar dados de receitas intra-orçamentárias correntes
        receitas_intra_correntes = buscar_receitas_por_categoria(
            ano, meses_bimestre, meses_ate_bimestre,
            ['71', '72', '73', '74', '75', '76', '77', '78', '79']
        )
        
        # Buscar dados de receitas intra-orçamentárias de capital
        receitas_intra_capital = buscar_receitas_por_categoria(
            ano, meses_bimestre, meses_ate_bimestre,
            ['81', '82', '83', '84', '85', '86', '87', '88', '89']
        )
        
        # Buscar saldos de exercícios anteriores
        saldos_exercicios_anteriores = buscar_saldos_exercicios_anteriores(
            ano, meses_bimestre, meses_ate_bimestre
        )
        
        # Calcular totais
        total_correntes = calcular_total_categoria(receitas_correntes)
        total_capital = calcular_total_categoria(receitas_capital)
        total_intra_correntes = calcular_total_categoria(receitas_intra_correntes)
        total_intra_capital = calcular_total_categoria(receitas_intra_capital)
        
        # Total exceto intra
        total_exceto_intra = somar_totais(total_correntes, total_capital)
        
        # Total intra
        total_intra = somar_totais(total_intra_correntes, total_intra_capital)
        
        # Total geral de receitas
        total_receitas = somar_totais(total_exceto_intra, total_intra)
        
        # Linha déficit (zerada)
        deficit = {
            'previsao_inicial': 0,
            'previsao_atualizada': 0,
            'realizado_bimestre': 0,
            'realizado_ate_bimestre': 0
        }
        
        # Total final
        total_final = somar_totais(total_receitas, deficit)
        
        # Montar estrutura do relatório
        relatorio = {
            'ano': ano,
            'bimestre': bimestre,
            'nome_bimestre': BIMESTRES[bimestre]['nome'],
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'dados': {
                'receitas_exceto_intra': {
                    'total': total_exceto_intra,
                    'receitas_correntes': {
                        'total': total_correntes,
                        'detalhes': receitas_correntes
                    },
                    'receitas_capital': {
                        'total': total_capital,
                        'detalhes': receitas_capital
                    }
                },
                'receitas_intra': {
                    'total': total_intra,
                    'receitas_correntes': {
                        'total': total_intra_correntes,
                        'detalhes': receitas_intra_correntes
                    },
                    'receitas_capital': {
                        'total': total_intra_capital,
                        'detalhes': receitas_intra_capital
                    }
                },
                'total_receitas': total_receitas,
                'deficit': deficit,
                'total_final': total_final,
                'saldos_exercicios_anteriores': saldos_exercicios_anteriores
            }
        }
        
        return jsonify(relatorio)
        
    except Exception as e:
        print(f"Erro em gerar_relatorio: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def buscar_receitas_por_categoria(ano, meses_bimestre, meses_ate_bimestre, codigos_fonte):
    """Busca receitas por categoria (correntes, capital ou intra) - valores consolidados"""
    
    # Converter listas para formato adequado
    codigos_str = ','.join([f"'{c}'" for c in codigos_fonte])
    meses_bimestre_str = ','.join([str(m) for m in meses_bimestre])
    meses_ate_bimestre_str = ','.join([str(m) for m in meses_ate_bimestre])
    
    if db_manager.is_duckdb:
        query = f"""
        WITH dados_agrupados AS (
            SELECT 
                cofontereceita,
                cosubfontereceita,
                -- Previsão inicial (521100000 a 521199999)
                SUM(CASE 
                    WHEN cocontacontabil >= '521100000' AND cocontacontabil <= '521199999' 
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_inicial,
                
                -- Previsão atualizada (521100000 a 521299999)
                SUM(CASE 
                    WHEN cocontacontabil >= '521100000' AND cocontacontabil <= '521299999' 
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_atualizada,
                
                -- Realizado no bimestre (621200000 a 621399999)
                SUM(CASE 
                    WHEN cocontacontabil >= '621200000' AND cocontacontabil <= '621399999' 
                    AND inmes IN ({meses_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as realizado_bimestre,
                
                -- Realizado até o bimestre (621200000 a 621399999)
                SUM(CASE 
                    WHEN cocontacontabil >= '621200000' AND cocontacontabil <= '621399999' 
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as realizado_ate_bimestre
                
            FROM receita_saldo
            WHERE coexercicio = ?
            AND cofontereceita IN ({codigos_str})
            GROUP BY cofontereceita, cosubfontereceita
        ),
        dados_com_nomes AS (
            SELECT 
                d.*,
                COALESCE(f.nofontereceita, 'Fonte ' || d.cofontereceita) as nome_fonte,
                COALESCE(sf.nosubfontereceita, 'Subfonte ' || d.cosubfontereceita) as nome_subfonte
            FROM dados_agrupados d
            LEFT JOIN dim_receita_origem f ON d.cofontereceita = CAST(f.cofontereceita AS VARCHAR)
            LEFT JOIN dim_receita_especie sf ON d.cosubfontereceita = CAST(sf.cosubfontereceita AS VARCHAR)
        )
        SELECT * FROM dados_com_nomes
        WHERE previsao_inicial != 0 OR previsao_atualizada != 0 
              OR realizado_bimestre != 0 OR realizado_ate_bimestre != 0
        ORDER BY cofontereceita, cosubfontereceita
        """
        params = [ano]
    else:  # PostgreSQL
        query = f"""
        WITH dados_agrupados AS (
            SELECT 
                cofontereceita,
                cosubfontereceita,
                -- Previsão inicial (521100000 a 521199999)
                SUM(CASE 
                    WHEN cocontacontabil >= '521100000' AND cocontacontabil <= '521199999' 
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_inicial,
                
                -- Previsão atualizada (521100000 a 521299999)
                SUM(CASE 
                    WHEN cocontacontabil >= '521100000' AND cocontacontabil <= '521299999' 
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_atualizada,
                
                -- Realizado no bimestre (621200000 a 621399999)
                SUM(CASE 
                    WHEN cocontacontabil >= '621200000' AND cocontacontabil <= '621399999' 
                    AND inmes IN ({meses_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as realizado_bimestre,
                
                -- Realizado até o bimestre (621200000 a 621399999)
                SUM(CASE 
                    WHEN cocontacontabil >= '621200000' AND cocontacontabil <= '621399999' 
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as realizado_ate_bimestre
                
            FROM receita_saldo
            WHERE coexercicio = :ano
            AND cofontereceita IN ({codigos_str})
            GROUP BY cofontereceita, cosubfontereceita
        ),
        dados_com_nomes AS (
            SELECT 
                d.*,
                COALESCE(f.nofontereceita, 'Fonte ' || d.cofontereceita) as nome_fonte,
                COALESCE(sf.nosubfontereceita, 'Subfonte ' || d.cosubfontereceita) as nome_subfonte
            FROM dados_agrupados d
            LEFT JOIN dim_receita_origem f ON d.cofontereceita = f.cofontereceita
            LEFT JOIN dim_receita_especie sf ON d.cosubfontereceita = sf.cosubfontereceita
        )
        SELECT * FROM dados_com_nomes
        WHERE previsao_inicial != 0 OR previsao_atualizada != 0 
              OR realizado_bimestre != 0 OR realizado_ate_bimestre != 0
        ORDER BY cofontereceita, cosubfontereceita
        """
        params = {'ano': ano}
    
    result = db_manager.execute_query(query, params)
    
    # Organizar dados hierarquicamente
    dados_organizados = {}
    
    for row in result:
        cofonte = row['cofontereceita']
        cosubfonte = row['cosubfontereceita']
        nome_fonte = row['nome_fonte']
        nome_subfonte = row['nome_subfonte']
        
        if cofonte not in dados_organizados:
            dados_organizados[cofonte] = {
                'codigo': cofonte,
                'nome': nome_fonte,
                'total': {
                    'previsao_inicial': 0,
                    'previsao_atualizada': 0,
                    'realizado_bimestre': 0,
                    'realizado_ate_bimestre': 0
                },
                'subfontes': {}
            }
        
        # Adicionar subfonte
        dados_organizados[cofonte]['subfontes'][cosubfonte] = {
            'codigo': cosubfonte,
            'nome': nome_subfonte,
            'previsao_inicial': float(row['previsao_inicial']),
            'previsao_atualizada': float(row['previsao_atualizada']),
            'realizado_bimestre': float(row['realizado_bimestre']),
            'realizado_ate_bimestre': float(row['realizado_ate_bimestre'])
        }
        
        # Somar no total da fonte
        dados_organizados[cofonte]['total']['previsao_inicial'] += float(row['previsao_inicial'])
        dados_organizados[cofonte]['total']['previsao_atualizada'] += float(row['previsao_atualizada'])
        dados_organizados[cofonte]['total']['realizado_bimestre'] += float(row['realizado_bimestre'])
        dados_organizados[cofonte]['total']['realizado_ate_bimestre'] += float(row['realizado_ate_bimestre'])
    
    return dados_organizados

def calcular_total_categoria(categoria_dados):
    """Calcula o total de uma categoria (correntes, capital ou intra)"""
    total = {
        'previsao_inicial': 0,
        'previsao_atualizada': 0,
        'realizado_bimestre': 0,
        'realizado_ate_bimestre': 0
    }
    
    for fonte_data in categoria_dados.values():
        total['previsao_inicial'] += fonte_data['total']['previsao_inicial']
        total['previsao_atualizada'] += fonte_data['total']['previsao_atualizada']
        total['realizado_bimestre'] += fonte_data['total']['realizado_bimestre']
        total['realizado_ate_bimestre'] += fonte_data['total']['realizado_ate_bimestre']
    
    return total

def somar_totais(total1, total2):
    """Soma dois dicionários de totais"""
    return {
        'previsao_inicial': total1.get('previsao_inicial', 0) + total2.get('previsao_inicial', 0),
        'previsao_atualizada': total1.get('previsao_atualizada', 0) + total2.get('previsao_atualizada', 0),
        'realizado_bimestre': total1.get('realizado_bimestre', 0) + total2.get('realizado_bimestre', 0),
        'realizado_ate_bimestre': total1.get('realizado_ate_bimestre', 0) + total2.get('realizado_ate_bimestre', 0)
    }

def buscar_saldos_exercicios_anteriores(ano, meses_bimestre, meses_ate_bimestre):
    """Busca os saldos de exercícios anteriores"""
    
    meses_bimestre_str = ','.join([str(m) for m in meses_bimestre])
    meses_ate_bimestre_str = ','.join([str(m) for m in meses_ate_bimestre])
    
    # Primeiro verificar se existe a coluna cocontacorrente
    if db_manager.is_duckdb:
        check_column = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'receita_saldo' 
        AND column_name = 'cocontacorrente'
        """
    else:  # PostgreSQL
        check_column = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'receita_saldo' 
        AND column_name = 'cocontacorrente'
        AND table_schema = current_schema()
        """
    
    check_result = db_manager.execute_query(check_column)
    has_conta_corrente = len(check_result) > 0
    
    print(f"Coluna cocontacorrente existe: {has_conta_corrente}")
    
    # Se não tem a coluna, criar valores zerados
    if not has_conta_corrente:
        print("AVISO: Coluna cocontacorrente não encontrada. Retornando valores zerados.")
        recursos_rpps = {
            'previsao_inicial': 0,
            'previsao_atualizada': 0,
            'realizado_bimestre': 0,
            'realizado_ate_bimestre': 0
        }
    else:
        # 1. Recursos Arrecadados em Exercícios Anteriores - RPPS
        if db_manager.is_duckdb:
            query_rpps = f"""
            SELECT 
                -- Previsão inicial (521100000 a 521199999)
                SUM(CASE 
                    WHEN cocontacontabil >= '521100000' AND cocontacontabil <= '521199999' 
                    AND cocontacorrente LIKE '99%'
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_inicial,
                
                -- Previsão atualizada (521100000 a 521299999)
                SUM(CASE 
                    WHEN cocontacontabil >= '521100000' AND cocontacontabil <= '521299999' 
                    AND cocontacorrente LIKE '99%'
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_atualizada,
                
                -- Realizado no bimestre (621200000 a 621399999)
                SUM(CASE 
                    WHEN cocontacontabil >= '621200000' AND cocontacontabil <= '621399999' 
                    AND cocontacorrente LIKE '99%'
                    AND inmes IN ({meses_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as realizado_bimestre,
                
                -- Realizado até o bimestre (621200000 a 621399999)
                SUM(CASE 
                    WHEN cocontacontabil >= '621200000' AND cocontacontabil <= '621399999' 
                    AND cocontacorrente LIKE '99%'
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as realizado_ate_bimestre
                
            FROM receita_saldo
            WHERE coexercicio = ?
            """
            params_rpps = [ano]
        else:  # PostgreSQL
            query_rpps = f"""
            SELECT 
                -- Previsão inicial (521100000 a 521199999)
                SUM(CASE 
                    WHEN cocontacontabil >= '521100000' AND cocontacontabil <= '521199999' 
                    AND cocontacorrente LIKE '99%'
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_inicial,
                
                -- Previsão atualizada (521100000 a 521299999)
                SUM(CASE 
                    WHEN cocontacontabil >= '521100000' AND cocontacontabil <= '521299999' 
                    AND cocontacorrente LIKE '99%'
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_atualizada,
                
                -- Realizado no bimestre (621200000 a 621399999)
                SUM(CASE 
                    WHEN cocontacontabil >= '621200000' AND cocontacontabil <= '621399999' 
                    AND cocontacorrente LIKE '99%'
                    AND inmes IN ({meses_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as realizado_bimestre,
                
                -- Realizado até o bimestre (621200000 a 621399999)
                SUM(CASE 
                    WHEN cocontacontabil >= '621200000' AND cocontacontabil <= '621399999' 
                    AND cocontacorrente LIKE '99%'
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_receita 
                    ELSE 0 
                END) as realizado_ate_bimestre
                
            FROM receita_saldo
            WHERE coexercicio = :ano
            """
            params_rpps = {'ano': ano}
        
        print(f"Executando query RPPS...")
        result_rpps = db_manager.execute_query(query_rpps, params_rpps)
        print(f"Resultado RPPS: {result_rpps}")
        
        if result_rpps and len(result_rpps) > 0:
            row = result_rpps[0]
            recursos_rpps = {
                'previsao_inicial': float(row['previsao_inicial']) if row['previsao_inicial'] else 0,
                'previsao_atualizada': float(row['previsao_atualizada']) if row['previsao_atualizada'] else 0,
                'realizado_bimestre': float(row['realizado_bimestre']) if row['realizado_bimestre'] else 0,
                'realizado_ate_bimestre': float(row['realizado_ate_bimestre']) if row['realizado_ate_bimestre'] else 0
            }
        else:
            recursos_rpps = {
                'previsao_inicial': 0,
                'previsao_atualizada': 0,
                'realizado_bimestre': 0,
                'realizado_ate_bimestre': 0
            }
    
    # 2. Superávit Financeiro Utilizado para Créditos Adicionais
    if db_manager.is_duckdb:
        query_superavit = f"""
        SELECT 
            -- Superávit só tem previsão atualizada e realizado até o bimestre
            SUM(CASE 
                WHEN cocontacontabil >= '522130100' AND cocontacontabil <= '522130199' 
                AND inmes IN ({meses_ate_bimestre_str})
                THEN saldo_contabil_receita 
                ELSE 0 
            END) as valor_superavit
            
        FROM receita_saldo
        WHERE coexercicio = ?
        """
        params_superavit = [ano]
    else:  # PostgreSQL
        query_superavit = f"""
        SELECT 
            -- Superávit só tem previsão atualizada e realizado até o bimestre
            SUM(CASE 
                WHEN cocontacontabil >= '522130100' AND cocontacontabil <= '522130199' 
                AND inmes IN ({meses_ate_bimestre_str})
                THEN saldo_contabil_receita 
                ELSE 0 
            END) as valor_superavit
            
        FROM receita_saldo
        WHERE coexercicio = :ano
        """
        params_superavit = {'ano': ano}
    
    print(f"Executando query Superávit...")
    result_superavit = db_manager.execute_query(query_superavit, params_superavit)
    print(f"Resultado Superávit: {result_superavit}")
    
    valor_superavit = 0
    if result_superavit and len(result_superavit) > 0:
        valor_superavit = float(result_superavit[0]['valor_superavit']) if result_superavit[0]['valor_superavit'] else 0
    
    superavit_financeiro = {
        'previsao_inicial': 0,  # Superávit não tem previsão inicial
        'previsao_atualizada': valor_superavit,
        'realizado_bimestre': 0,  # Superávit não tem realizado no bimestre
        'realizado_ate_bimestre': valor_superavit
    }
    
    # Total dos saldos
    total_saldos = somar_totais(recursos_rpps, superavit_financeiro)
    
    print(f"Total saldos: {total_saldos}")
    
    return {
        'total': total_saldos,
        'recursos_rpps': recursos_rpps,
        'superavit_financeiro': superavit_financeiro
    }