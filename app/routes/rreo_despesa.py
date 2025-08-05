"""
Blueprint para relatórios RREO - Despesa
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.database_duckdb import db_duckdb
import pandas as pd
from datetime import datetime

# Criar blueprint
rreo_despesa = Blueprint('rreo_despesa', __name__)

# Mapeamento de bimestres
BIMESTRES = {
    1: {'meses': [1, 2], 'nome': '1º Bimestre'},
    2: {'meses': [3, 4], 'nome': '2º Bimestre'},
    3: {'meses': [5, 6], 'nome': '3º Bimestre'},
    4: {'meses': [7, 8], 'nome': '4º Bimestre'},
    5: {'meses': [9, 10], 'nome': '5º Bimestre'},
    6: {'meses': [11, 12], 'nome': '6º Bimestre'}
}

@rreo_despesa.route('/rreo-despesa')
def rreo_despesa_page():
    """Página do demonstrativo RREO de Despesa"""
    return render_template('rreo_despesa/rreo_despesa.html', 
                         title='RREO - Demonstrativo de Despesas')

@rreo_despesa.route('/api/filtros')
def get_filtros():
    """Retorna os filtros disponíveis para o relatório"""
    try:
        conn = db_duckdb.get_connection()
        
        # Buscar anos disponíveis
        anos_query = """
        SELECT DISTINCT coexercicio 
        FROM despesa_saldo 
        ORDER BY coexercicio DESC
        """
        anos = [row[0] for row in conn.execute(anos_query).fetchall()]
        
        conn.close()
        
        return jsonify({
            'anos': anos,
            'bimestres': [
                {'valor': k, 'nome': v['nome']} 
                for k, v in BIMESTRES.items()
            ]
        })
        
    except Exception as e:
        print(f"Erro em get_filtros: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@rreo_despesa.route('/api/gerar-relatorio')
def gerar_relatorio():
    """Gera o relatório RREO de Despesa"""
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
        
        conn = db_duckdb.get_connection()
        
        # Buscar despesas correntes (exceto intra)
        despesas_correntes_exceto = buscar_despesas_por_categoria(
            conn, ano, meses_bimestre, meses_ate_bimestre,
            ['1', '2', '3'],  # Categorias de despesas correntes
            excluir_intra=True
        )
        
        # Buscar despesas de capital (exceto intra)
        despesas_capital_exceto = buscar_despesas_por_categoria(
            conn, ano, meses_bimestre, meses_ate_bimestre,
            ['4', '5', '6'],  # Categorias de despesas de capital
            excluir_intra=True
        )
        
        # Buscar despesas correntes intra-orçamentárias
        despesas_correntes_intra = buscar_despesas_por_categoria(
            conn, ano, meses_bimestre, meses_ate_bimestre,
            ['1', '2', '3'],  # Categorias de despesas correntes
            apenas_intra=True
        )
        
        # Buscar despesas de capital intra-orçamentárias
        despesas_capital_intra = buscar_despesas_por_categoria(
            conn, ano, meses_bimestre, meses_ate_bimestre,
            ['4', '5', '6'],  # Categorias de despesas de capital
            apenas_intra=True
        )
        
        # Buscar reserva de contingência (incategoria = 9)
        reserva_contingencia = buscar_reserva_contingencia(
            conn, ano, meses_bimestre, meses_ate_bimestre
        )
        
        conn.close()
        
        # Calcular totais
        total_correntes_exceto = calcular_total_grupo(despesas_correntes_exceto)
        total_capital_exceto = calcular_total_grupo(despesas_capital_exceto)
        total_correntes_intra = calcular_total_grupo(despesas_correntes_intra)
        total_capital_intra = calcular_total_grupo(despesas_capital_intra)
        
        # Total exceto intra (VI)
        total_exceto_intra = somar_totais(total_correntes_exceto, total_capital_exceto)
        
        # Total intra (VII)
        total_intra = somar_totais(total_correntes_intra, total_capital_intra)
        
        # Total das despesas (VIII) = (VI) + (VII) + Reserva
        total_despesas_parcial = somar_totais(total_exceto_intra, total_intra)
        total_despesas = somar_totais(total_despesas_parcial, reserva_contingencia)
        
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
                    'despesas_correntes': {
                        'total': total_correntes_exceto,
                        'detalhes': despesas_correntes_exceto
                    },
                    'despesas_capital': {
                        'total': total_capital_exceto,
                        'detalhes': despesas_capital_exceto
                    }
                },
                'despesas_intra': {
                    'total': total_intra,
                    'despesas_correntes': {
                        'total': total_correntes_intra,
                        'detalhes': despesas_correntes_intra
                    },
                    'despesas_capital': {
                        'total': total_capital_intra,
                        'detalhes': despesas_capital_intra
                    }
                },
                'reserva_contingencia': reserva_contingencia,
                'total_despesas': total_despesas,
                'superavit': superavit,
                'total_final': total_final
            }
        }
        
        return jsonify(relatorio)
        
    except Exception as e:
        print(f"Erro em gerar_relatorio: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def buscar_despesas_por_categoria(conn, ano, meses_bimestre, meses_ate_bimestre, grupos, excluir_intra=False, apenas_intra=False):
    """Busca despesas por grupo com filtro de modalidade"""
    
    # Converter listas para string SQL
    grupos_str = ','.join([f"'{g}'" for g in grupos])
    meses_bimestre_str = ','.join([str(m) for m in meses_bimestre])
    meses_ate_bimestre_str = ','.join([str(m) for m in meses_ate_bimestre])
    
    # Filtro de modalidade
    filtro_modalidade = ""
    if excluir_intra:
        filtro_modalidade = "AND comodalidade != '91'"
    elif apenas_intra:
        filtro_modalidade = "AND comodalidade = '91'"
    
    query = f"""
    WITH dados_agrupados AS (
        SELECT 
            cogrupo,
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
        WHERE coexercicio = {ano}
        AND cogrupo IN ({grupos_str})
        {filtro_modalidade}
        GROUP BY cogrupo
    )
    SELECT 
        d.*,
        COALESCE(g.nogrupo, 'Grupo ' || d.cogrupo) as nome_grupo
    FROM dados_agrupados d
    LEFT JOIN dim_grupo_despesa g ON d.cogrupo = CAST(g.cogrupo AS VARCHAR)
    WHERE d.dotacao_inicial != 0 OR d.dotacao_autorizada != 0 
          OR d.empenhado_bimestre != 0 OR d.empenhado_ate_bimestre != 0
          OR d.liquidado_bimestre != 0 OR d.liquidado_ate_bimestre != 0
          OR d.pago_ate_bimestre != 0
    ORDER BY d.cogrupo
    """
    
    result = conn.execute(query).fetchall()
    
    # Organizar dados
    dados_organizados = {}
    
    for row in result:
        grupo = row[0]
        nome_grupo = row[8]
        
        # Usar o nome do grupo da dimensão
        dados_organizados[grupo] = {
            'codigo': grupo,
            'nome': nome_grupo,
            'dotacao_inicial': float(row[1]),
            'dotacao_autorizada': float(row[2]),
            'empenhado_bimestre': float(row[3]),
            'empenhado_ate_bimestre': float(row[4]),
            'liquidado_bimestre': float(row[5]),
            'liquidado_ate_bimestre': float(row[6]),
            'pago_ate_bimestre': float(row[7])
        }
    
    return dados_organizados

def calcular_total_grupo(grupo_dados):
    """Calcula o total de um grupo de categorias"""
    total = {
        'dotacao_inicial': 0,
        'dotacao_autorizada': 0,
        'empenhado_bimestre': 0,
        'empenhado_ate_bimestre': 0,
        'liquidado_bimestre': 0,
        'liquidado_ate_bimestre': 0,
        'pago_ate_bimestre': 0
    }
    
    for categoria_data in grupo_dados.values():
        total['dotacao_inicial'] += categoria_data.get('dotacao_inicial', 0)
        total['dotacao_autorizada'] += categoria_data.get('dotacao_autorizada', 0)
        total['empenhado_bimestre'] += categoria_data.get('empenhado_bimestre', 0)
        total['empenhado_ate_bimestre'] += categoria_data.get('empenhado_ate_bimestre', 0)
        total['liquidado_bimestre'] += categoria_data.get('liquidado_bimestre', 0)
        total['liquidado_ate_bimestre'] += categoria_data.get('liquidado_ate_bimestre', 0)
        total['pago_ate_bimestre'] += categoria_data.get('pago_ate_bimestre', 0)
    
    return total

def buscar_reserva_contingencia(conn, ano, meses_bimestre, meses_ate_bimestre):
    """Busca reserva de contingência (incategoria = 9)"""
    
    meses_bimestre_str = ','.join([str(m) for m in meses_bimestre])
    meses_ate_bimestre_str = ','.join([str(m) for m in meses_ate_bimestre])
    
    query = f"""
    SELECT 
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
    WHERE coexercicio = {ano}
    AND incategoria = '9'
    AND comodalidade != '91'
    """
    
    result = conn.execute(query).fetchone()
    
    return {
        'dotacao_inicial': float(result[0]) if result[0] else 0,
        'dotacao_autorizada': float(result[1]) if result[1] else 0,
        'empenhado_bimestre': float(result[2]) if result[2] else 0,
        'empenhado_ate_bimestre': float(result[3]) if result[3] else 0,
        'liquidado_bimestre': float(result[4]) if result[4] else 0,
        'liquidado_ate_bimestre': float(result[5]) if result[5] else 0,
        'pago_ate_bimestre': float(result[6]) if result[6] else 0
    }

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