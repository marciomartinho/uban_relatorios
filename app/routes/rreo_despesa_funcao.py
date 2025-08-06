"""
Blueprint para relatórios RREO - Despesa por Função
Adaptado para trabalhar com db_manager (DuckDB/PostgreSQL)
"""
from flask import Blueprint, render_template, jsonify, request
from app.db_manager import db_manager
from datetime import datetime
import traceback

# Criar blueprint
rreo_despesa_funcao = Blueprint('rreo_despesa_funcao', __name__)

# Mapeamento de bimestres
BIMESTRES = {
    1: {'meses': [1, 2], 'nome': '1º Bimestre'},
    2: {'meses': [3, 4], 'nome': '2º Bimestre'},
    3: {'meses': [5, 6], 'nome': '3º Bimestre'},
    4: {'meses': [7, 8], 'nome': '4º Bimestre'},
    5: {'meses': [9, 10], 'nome': '5º Bimestre'},
    6: {'meses': [11, 12], 'nome': '6º Bimestre'}
}

@rreo_despesa_funcao.route('/rreo-despesa-funcao')
def rreo_despesa_funcao_page():
    """Página do demonstrativo RREO de Despesa por Função"""
    return render_template('rreo_despesa/rreo_despesa_funcao.html',
                         title='RREO - Despesa por Função')

@rreo_despesa_funcao.route('/api/filtros')
def get_filtros():
    """Retorna os filtros disponíveis para o relatório"""
    try:
        # Query para buscar anos disponíveis
        anos_query = """
        SELECT DISTINCT coexercicio
        FROM despesa_saldo
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

@rreo_despesa_funcao.route('/api/gerar-relatorio')
def gerar_relatorio():
    """Gera o relatório RREO de Despesa por Função"""
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
        
        # Buscar despesas por função (exceto intra)
        despesas_funcao_exceto = buscar_despesas_por_funcao(
            ano, meses_bimestre, meses_ate_bimestre,
            excluir_intra=True
        )
        
        # Buscar despesas por função (intra-orçamentárias)
        despesas_funcao_intra = buscar_despesas_por_funcao(
            ano, meses_bimestre, meses_ate_bimestre,
            apenas_intra=True
        )
        
        # Calcular totais
        total_exceto_intra = calcular_total_geral(despesas_funcao_exceto)
        total_intra = calcular_total_geral(despesas_funcao_intra)
        
        # Total das despesas (VIII) = (VI) + (VII)
        total_despesas = somar_totais(total_exceto_intra, total_intra)
        
        # Linha superávit (IX) - zerada
        superavit = {
            'dotacao_inicial': 0,
            'dotacao_autorizada': 0,
            'empenhado_bimestre': 0,
            'empenhado_ate_bimestre': 0,
            'liquidado_bimestre': 0,
            'liquidado_ate_bimestre': 0,
            'pago_ate_bimestre': 0
        }
        
        # Total final (X) = (VIII) + (IX)
        total_final = somar_totais(total_despesas, superavit)
        
        # Montar estrutura do relatório
        relatorio = {
            'ano': ano,
            'bimestre': bimestre,
            'nome_bimestre': BIMESTRES[bimestre]['nome'],
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'dados': {
                'despesas_exceto_intra': {
                    'total': total_exceto_intra,
                    'funcoes': despesas_funcao_exceto
                },
                'despesas_intra': {
                    'total': total_intra,
                    'funcoes': despesas_funcao_intra
                },
                'total_despesas': total_despesas,
                'superavit': superavit,
                'total_final': total_final
            }
        }
        
        return jsonify(relatorio)
        
    except Exception as e:
        print(f"Erro em gerar_relatorio: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def buscar_despesas_por_funcao(ano, meses_bimestre, meses_ate_bimestre, excluir_intra=False, apenas_intra=False):
    """Busca despesas agrupadas por função e subfunção"""
    
    # Converter listas para formato adequado
    meses_bimestre_str = ','.join([str(m) for m in meses_bimestre])
    meses_ate_bimestre_str = ','.join([str(m) for m in meses_ate_bimestre])
    
    # Filtro de modalidade
    filtro_modalidade = ""
    if excluir_intra:
        filtro_modalidade = "AND comodalidade != '91'"
    elif apenas_intra:
        filtro_modalidade = "AND comodalidade = '91'"
    
    # Query adaptada para ambos os bancos
    if db_manager.is_duckdb:
        query = f"""
        WITH dados_agrupados AS (
            SELECT 
                cofuncao,
                cosubfuncao,
                -- Dotação inicial (522110000 a 522119999)
                SUM(CASE 
                    WHEN cocontacontabil >= '522110000' AND cocontacontabil <= '522119999' 
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as dotacao_inicial,
                
                -- Dotação autorizada (inclui créditos suplementares)
                SUM(CASE 
                    WHEN (
                        (cocontacontabil >= '522110000' AND cocontacontabil <= '522119999') OR
                        (cocontacontabil >= '522120000' AND cocontacontabil <= '522129999') OR
                        (cocontacontabil >= '522150000' AND cocontacontabil <= '522159999') OR
                        (cocontacontabil >= '522190000' AND cocontacontabil <= '522199999')
                    )
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as dotacao_autorizada,
                
                -- Empenhado no bimestre (622130000 a 622139999)
                SUM(CASE 
                    WHEN cocontacontabil >= '622130000' AND cocontacontabil <= '622139999' 
                    AND inmes IN ({meses_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as empenhado_bimestre,
                
                -- Empenhado até o bimestre (622130000 a 622139999)
                SUM(CASE 
                    WHEN cocontacontabil >= '622130000' AND cocontacontabil <= '622139999' 
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as empenhado_ate_bimestre,
                
                -- Liquidado no bimestre
                SUM(CASE 
                    WHEN cocontacontabil IN ('622130300', '622130400', '622130700')
                    AND inmes IN ({meses_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as liquidado_bimestre,
                
                -- Liquidado até o bimestre
                SUM(CASE 
                    WHEN cocontacontabil IN ('622130300', '622130400', '622130700')
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as liquidado_ate_bimestre,
                
                -- Pago até o bimestre
                SUM(CASE 
                    WHEN cocontacontabil = '622920104'
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as pago_ate_bimestre
                
            FROM despesa_saldo
            WHERE coexercicio = ?
            {filtro_modalidade}
            GROUP BY cofuncao, cosubfuncao
        )
        SELECT 
            d.*,
            COALESCE(f.nofuncao, 'Função ' || d.cofuncao) as nome_funcao,
            COALESCE(s.nosubfuncao, 'Subfunção ' || d.cosubfuncao) as nome_subfuncao
        FROM dados_agrupados d
        LEFT JOIN dim_funcao f ON CAST(d.cofuncao AS INTEGER) = f.cofuncao
        LEFT JOIN dim_subfuncao s ON CAST(d.cosubfuncao AS INTEGER) = s.cosubfuncao
        WHERE d.dotacao_inicial != 0 OR d.dotacao_autorizada != 0 
              OR d.empenhado_bimestre != 0 OR d.empenhado_ate_bimestre != 0
              OR d.liquidado_bimestre != 0 OR d.liquidado_ate_bimestre != 0
              OR d.pago_ate_bimestre != 0
        ORDER BY d.cofuncao, d.cosubfuncao
        """
        params = [ano]
    else:  # PostgreSQL
        query = f"""
        WITH dados_agrupados AS (
            SELECT 
                cofuncao,
                cosubfuncao,
                -- Dotação inicial (522110000 a 522119999)
                SUM(CASE 
                    WHEN cocontacontabil >= '522110000' AND cocontacontabil <= '522119999' 
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as dotacao_inicial,
                
                -- Dotação autorizada (inclui créditos suplementares)
                SUM(CASE 
                    WHEN (
                        (cocontacontabil >= '522110000' AND cocontacontabil <= '522119999') OR
                        (cocontacontabil >= '522120000' AND cocontacontabil <= '522129999') OR
                        (cocontacontabil >= '522150000' AND cocontacontabil <= '522159999') OR
                        (cocontacontabil >= '522190000' AND cocontacontabil <= '522199999')
                    )
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as dotacao_autorizada,
                
                -- Empenhado no bimestre (622130000 a 622139999)
                SUM(CASE 
                    WHEN cocontacontabil >= '622130000' AND cocontacontabil <= '622139999' 
                    AND inmes IN ({meses_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as empenhado_bimestre,
                
                -- Empenhado até o bimestre (622130000 a 622139999)
                SUM(CASE 
                    WHEN cocontacontabil >= '622130000' AND cocontacontabil <= '622139999' 
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as empenhado_ate_bimestre,
                
                -- Liquidado no bimestre
                SUM(CASE 
                    WHEN cocontacontabil IN ('622130300', '622130400', '622130700')
                    AND inmes IN ({meses_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as liquidado_bimestre,
                
                -- Liquidado até o bimestre
                SUM(CASE 
                    WHEN cocontacontabil IN ('622130300', '622130400', '622130700')
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as liquidado_ate_bimestre,
                
                -- Pago até o bimestre
                SUM(CASE 
                    WHEN cocontacontabil = '622920104'
                    AND inmes IN ({meses_ate_bimestre_str})
                    THEN saldo_contabil_despesa 
                    ELSE 0 
                END) as pago_ate_bimestre
                
            FROM despesa_saldo
            WHERE coexercicio = :ano
            {filtro_modalidade}
            GROUP BY cofuncao, cosubfuncao
        )
        SELECT 
            d.*,
            COALESCE(f.nofuncao, 'Função ' || d.cofuncao) as nome_funcao,
            COALESCE(s.nosubfuncao, 'Subfunção ' || d.cosubfuncao) as nome_subfuncao
        FROM dados_agrupados d
        LEFT JOIN dim_funcao f ON CAST(d.cofuncao AS INTEGER) = f.cofuncao
        LEFT JOIN dim_subfuncao s ON CAST(d.cosubfuncao AS INTEGER) = s.cosubfuncao
        WHERE d.dotacao_inicial != 0 OR d.dotacao_autorizada != 0 
              OR d.empenhado_bimestre != 0 OR d.empenhado_ate_bimestre != 0
              OR d.liquidado_bimestre != 0 OR d.liquidado_ate_bimestre != 0
              OR d.pago_ate_bimestre != 0
        ORDER BY d.cofuncao, d.cosubfuncao
        """
        params = {'ano': ano}
    
    result = db_manager.execute_query(query, params)
    
    # Organizar dados hierarquicamente por função e subfunção
    dados_organizados = {}
    
    for row in result:
        funcao = row['cofuncao']
        subfuncao = row['cosubfuncao']
        nome_funcao = row['nome_funcao']
        nome_subfuncao = row['nome_subfuncao']
        
        if funcao not in dados_organizados:
            dados_organizados[funcao] = {
                'codigo': funcao,
                'nome': nome_funcao,
                'total': {
                    'dotacao_inicial': 0,
                    'dotacao_autorizada': 0,
                    'empenhado_bimestre': 0,
                    'empenhado_ate_bimestre': 0,
                    'liquidado_bimestre': 0,
                    'liquidado_ate_bimestre': 0,
                    'pago_ate_bimestre': 0
                },
                'subfuncoes': {}
            }
        
        # Adicionar subfunção
        dados_organizados[funcao]['subfuncoes'][subfuncao] = {
            'codigo': subfuncao,
            'nome': nome_subfuncao,
            'dotacao_inicial': float(row['dotacao_inicial']),
            'dotacao_autorizada': float(row['dotacao_autorizada']),
            'empenhado_bimestre': float(row['empenhado_bimestre']),
            'empenhado_ate_bimestre': float(row['empenhado_ate_bimestre']),
            'liquidado_bimestre': float(row['liquidado_bimestre']),
            'liquidado_ate_bimestre': float(row['liquidado_ate_bimestre']),
            'pago_ate_bimestre': float(row['pago_ate_bimestre'])
        }
        
        # Somar ao total da função
        dados_organizados[funcao]['total']['dotacao_inicial'] += float(row['dotacao_inicial'])
        dados_organizados[funcao]['total']['dotacao_autorizada'] += float(row['dotacao_autorizada'])
        dados_organizados[funcao]['total']['empenhado_bimestre'] += float(row['empenhado_bimestre'])
        dados_organizados[funcao]['total']['empenhado_ate_bimestre'] += float(row['empenhado_ate_bimestre'])
        dados_organizados[funcao]['total']['liquidado_bimestre'] += float(row['liquidado_bimestre'])
        dados_organizados[funcao]['total']['liquidado_ate_bimestre'] += float(row['liquidado_ate_bimestre'])
        dados_organizados[funcao]['total']['pago_ate_bimestre'] += float(row['pago_ate_bimestre'])
    
    return dados_organizados

def calcular_total_geral(funcoes_dados):
    """Calcula o total geral de todas as funções"""
    total = {
        'dotacao_inicial': 0,
        'dotacao_autorizada': 0,
        'empenhado_bimestre': 0,
        'empenhado_ate_bimestre': 0,
        'liquidado_bimestre': 0,
        'liquidado_ate_bimestre': 0,
        'pago_ate_bimestre': 0
    }
    
    for funcao_data in funcoes_dados.values():
        total['dotacao_inicial'] += funcao_data['total']['dotacao_inicial']
        total['dotacao_autorizada'] += funcao_data['total']['dotacao_autorizada']
        total['empenhado_bimestre'] += funcao_data['total']['empenhado_bimestre']
        total['empenhado_ate_bimestre'] += funcao_data['total']['empenhado_ate_bimestre']
        total['liquidado_bimestre'] += funcao_data['total']['liquidado_bimestre']
        total['liquidado_ate_bimestre'] += funcao_data['total']['liquidado_ate_bimestre']
        total['pago_ate_bimestre'] += funcao_data['total']['pago_ate_bimestre']
    
    return total

def somar_totais(total1, total2):
    """Soma dois dicionários de totais"""
    return {
        'dotacao_inicial': total1.get('dotacao_inicial', 0) + total2.get('dotacao_inicial', 0),
        'dotacao_autorizada': total1.get('dotacao_autorizada', 0) + total2.get('dotacao_autorizada', 0),
        'empenhado_bimestre': total1.get('empenhado_bimestre', 0) + total2.get('empenhado_bimestre', 0),
        'empenhado_ate_bimestre': total1.get('empenhado_ate_bimestre', 0) + total2.get('empenhado_ate_bimestre', 0),
        'liquidado_bimestre': total1.get('liquidado_bimestre', 0) + total2.get('liquidado_bimestre', 0),
        'liquidado_ate_bimestre': total1.get('liquidado_ate_bimestre', 0) + total2.get('liquidado_ate_bimestre', 0),
        'pago_ate_bimestre': total1.get('pago_ate_bimestre', 0) + total2.get('pago_ate_bimestre', 0)
    }