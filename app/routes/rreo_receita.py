"""
Blueprint para relatórios RREO - Receita
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.database_duckdb import db_duckdb
import pandas as pd
from datetime import datetime

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

@rreo_receita.route('/demonstrativo')
def demonstrativo():
    """Página do demonstrativo RREO de Receita"""
    return render_template('rreo_receita/demonstrativo.html', 
                         title='RREO - Demonstrativo de Receitas')

@rreo_receita.route('/api/filtros')
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
        
        conn = db_duckdb.get_connection()
        
        # Buscar dados de receitas correntes (exceto intra)
        receitas_correntes = buscar_receitas_por_categoria(
            conn, ano, meses_bimestre, meses_ate_bimestre, 
            ['11', '12', '13', '14', '15', '16', '17', '18', '19']
        )
        
        # Buscar dados de receitas de capital (exceto intra)
        receitas_capital = buscar_receitas_por_categoria(
            conn, ano, meses_bimestre, meses_ate_bimestre,
            ['21', '22', '23', '24', '25', '26', '27', '28', '29']
        )
        
        # Buscar dados de receitas intra-orçamentárias correntes
        receitas_intra_correntes = buscar_receitas_por_categoria(
            conn, ano, meses_bimestre, meses_ate_bimestre,
            ['71', '72', '73', '74', '75', '76', '77', '78', '79']
        )
        
        # Buscar dados de receitas intra-orçamentárias de capital
        receitas_intra_capital = buscar_receitas_por_categoria(
            conn, ano, meses_bimestre, meses_ate_bimestre,
            ['81', '82', '83', '84', '85', '86', '87', '88', '89']
        )
        
        conn.close()
        
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
                'total_final': total_final
            }
        }
        
        return jsonify(relatorio)
        
    except Exception as e:
        print(f"Erro em gerar_relatorio: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def buscar_receitas_por_categoria(conn, ano, meses_bimestre, meses_ate_bimestre, codigos_fonte):
    """Busca receitas por categoria (correntes, capital ou intra) - valores consolidados"""
    
    # Converter listas para string SQL
    codigos_str = ','.join([f"'{c}'" for c in codigos_fonte])
    meses_bimestre_str = ','.join([str(m) for m in meses_bimestre])
    meses_ate_bimestre_str = ','.join([str(m) for m in meses_ate_bimestre])
    
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
        WHERE coexercicio = {ano}
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
    
    result = conn.execute(query).fetchall()
    
    # Organizar dados hierarquicamente
    dados_organizados = {}
    
    for row in result:
        cofonte = row[0]
        cosubfonte = row[1]
        nome_fonte = row[6]
        nome_subfonte = row[7]
        
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
            'previsao_inicial': float(row[2]),
            'previsao_atualizada': float(row[3]),
            'realizado_bimestre': float(row[4]),
            'realizado_ate_bimestre': float(row[5])
        }
        
        # Somar no total da fonte
        dados_organizados[cofonte]['total']['previsao_inicial'] += float(row[2])
        dados_organizados[cofonte]['total']['previsao_atualizada'] += float(row[3])
        dados_organizados[cofonte]['total']['realizado_bimestre'] += float(row[4])
        dados_organizados[cofonte]['total']['realizado_ate_bimestre'] += float(row[5])
    
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