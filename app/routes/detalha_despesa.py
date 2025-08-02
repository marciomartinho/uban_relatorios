"""
Blueprint para detalhamento de conta contábil de despesa - Versão DuckDB
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.database_duckdb import db_duckdb
import pandas as pd

# Criar blueprint
detalha_despesa = Blueprint('detalha_despesa', __name__)

@detalha_despesa.route('/consulta')
def consulta():
    """Página de consulta de detalhamento de conta contábil despesa"""
    return render_template('detalha_despesa/consulta_detalha_despesa.html', 
                         title='Detalha Conta Contábil Despesa')

@detalha_despesa.route('/api/filtros')
def get_filtros():
    """Retorna os valores únicos para os filtros"""
    try:
        conn = db_duckdb.get_connection()
        
        # Buscar anos únicos
        anos_query = """
        SELECT DISTINCT YEAR(dalancamento) as ano
        FROM despesa_lancamento 
        WHERE dalancamento IS NOT NULL
        ORDER BY ano DESC
        """
        anos = [row[0] for row in conn.execute(anos_query).fetchall()]
        
        # Buscar contas contábeis únicas - ordenadas numericamente
        contas_query = """
        SELECT DISTINCT cocontacontabil
        FROM despesa_lancamento 
        WHERE cocontacontabil IS NOT NULL
        ORDER BY cocontacontabil ASC
        """
        contas = [row[0] for row in conn.execute(contas_query).fetchall()]
        
        # Buscar UGs Contábeis únicas
        ugs_query = """
        SELECT DISTINCT cougcontab 
        FROM despesa_lancamento 
        WHERE cougcontab IS NOT NULL
        ORDER BY cougcontab
        """
        ugs = [row[0] for row in conn.execute(ugs_query).fetchall()]
        
        conn.close()
        
        return jsonify({
            'anos': anos,
            'contas': contas,
            'ugs': ugs,
            'fonte': 'DuckDB Local',
            'cache_disponivel': True  # DuckDB é sempre rápido
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@detalha_despesa.route('/api/dados')
def get_dados():
    """Retorna os dados filtrados"""
    try:
        # Pegar parâmetros da query
        ano = request.args.get('ano')
        conta = request.args.get('conta')
        ug = request.args.get('ug')
        limite = request.args.get('limite', 10000)  # Limite maior no DuckDB
        
        # Validar parâmetros obrigatórios
        if not all([ano, conta, ug]):
            return jsonify({'erro': 'Parâmetros obrigatórios: ano, conta, ug'}), 400
        
        conn = db_duckdb.get_connection()
        
        # Montar query base
        if ug == 'CONSOLIDADO':
            query = """
            SELECT 
                MONTH(dalancamento) as mes,
                nudocumento,
                coevento,
                conatureza,
                cocontacorrente,
                valancamento,
                indebitocredito,
                coug,
                strftime('%d/%m/%Y', dalancamento) as dalancamento,
                tipo_lancamento,
                cofonte,
                couo,
                coprograma
            FROM despesa_lancamento
            WHERE YEAR(dalancamento) = ? 
                AND cocontacontabil = ?
            ORDER BY MONTH(dalancamento), dalancamento, nudocumento
            LIMIT ?
            """
            params = [int(ano), int(conta), int(limite)]
        else:
            query = """
            SELECT 
                MONTH(dalancamento) as mes,
                nudocumento,
                coevento,
                conatureza,
                cocontacorrente,
                valancamento,
                indebitocredito,
                coug,
                strftime('%d/%m/%Y', dalancamento) as dalancamento,
                tipo_lancamento,
                cofonte,
                couo,
                coprograma
            FROM despesa_lancamento
            WHERE YEAR(dalancamento) = ? 
                AND cocontacontabil = ? 
                AND cougcontab = ?
            ORDER BY MONTH(dalancamento), dalancamento, nudocumento
            LIMIT ?
            """
            params = [int(ano), int(conta), int(ug), int(limite)]
        
        # Executar query
        result = conn.execute(query, params).fetchall()
        
        # Converter para lista de dicionários
        dados = []
        for row in result:
            dados.append({
                'mes': row[0],
                'nudocumento': row[1],
                'coevento': row[2],
                'conatureza': row[3],
                'cocontacorrente': row[4],
                'valancamento': row[5],
                'indebitocredito': row[6],
                'coug': row[7],
                'dalancamento': row[8],
                'tipo_lancamento': row[9],
                'cofonte': row[10],
                'couo': row[11],
                'coprograma': row[12]
            })
        
        # Verificar se tem mais registros
        if ug == 'CONSOLIDADO':
            count_query = """
            SELECT COUNT(*) FROM despesa_lancamento
            WHERE YEAR(dalancamento) = ? AND cocontacontabil = ?
            """
            count_params = [int(ano), int(conta)]
        else:
            count_query = """
            SELECT COUNT(*) FROM despesa_lancamento
            WHERE YEAR(dalancamento) = ? AND cocontacontabil = ? AND cougcontab = ?
            """
            count_params = [int(ano), int(conta), int(ug)]
        
        total_registros = conn.execute(count_query, count_params).fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'dados': dados,
            'total': len(dados),
            'total_registros': total_registros,
            'tem_mais': total_registros > len(dados),
            'limite_aplicado': int(limite),
            'fonte': 'DuckDB Local'
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@detalha_despesa.route('/api/totais')
def get_totais():
    """Retorna os totais por tipo de lançamento"""
    try:
        # Pegar parâmetros da query
        ano = request.args.get('ano')
        conta = request.args.get('conta')
        ug = request.args.get('ug')
        
        # Validar parâmetros obrigatórios
        if not all([ano, conta, ug]):
            return jsonify({'erro': 'Parâmetros obrigatórios: ano, conta, ug'}), 400
        
        conn = db_duckdb.get_connection()
        
        # Montar query para totais
        if ug == 'CONSOLIDADO':
            query = """
            SELECT 
                tipo_lancamento,
                COUNT(*) as quantidade,
                SUM(valancamento) as total
            FROM despesa_lancamento
            WHERE YEAR(dalancamento) = ? 
                AND cocontacontabil = ?
            GROUP BY tipo_lancamento
            """
            params = [int(ano), int(conta)]
        else:
            query = """
            SELECT 
                tipo_lancamento,
                COUNT(*) as quantidade,
                SUM(valancamento) as total
            FROM despesa_lancamento
            WHERE YEAR(dalancamento) = ? 
                AND cocontacontabil = ? 
                AND cougcontab = ?
            GROUP BY tipo_lancamento
            """
            params = [int(ano), int(conta), int(ug)]
        
        # Executar query
        result = conn.execute(query, params).fetchall()
        
        # Formatar resultado
        totais = {
            'debito': {'quantidade': 0, 'total': 0},
            'credito': {'quantidade': 0, 'total': 0},
            'saldo': 0
        }
        
        for row in result:
            if row[0] == 'DEBITO':
                totais['debito']['quantidade'] = row[1]
                totais['debito']['total'] = float(row[2] or 0)
            elif row[0] == 'CREDITO':
                totais['credito']['quantidade'] = row[1]
                totais['credito']['total'] = float(row[2] or 0)
        
        # Calcular saldo baseado no primeiro dígito da conta contábil
        if str(conta).startswith('5'):
            totais['saldo'] = totais['debito']['total'] - totais['credito']['total']
        else:
            totais['saldo'] = totais['credito']['total'] - totais['debito']['total']
        
        # Buscar top 5 naturezas de despesa
        if ug == 'CONSOLIDADO':
            natureza_query = """
            SELECT 
                conatureza,
                COUNT(*) as quantidade,
                SUM(valancamento) as total
            FROM despesa_lancamento
            WHERE YEAR(dalancamento) = ? 
                AND cocontacontabil = ?
                AND conatureza IS NOT NULL
            GROUP BY conatureza
            ORDER BY total DESC
            LIMIT 5
            """
            natureza_params = [int(ano), int(conta)]
        else:
            natureza_query = """
            SELECT 
                conatureza,
                COUNT(*) as quantidade,
                SUM(valancamento) as total
            FROM despesa_lancamento
            WHERE YEAR(dalancamento) = ? 
                AND cocontacontabil = ?
                AND cougcontab = ?
                AND conatureza IS NOT NULL
            GROUP BY conatureza
            ORDER BY total DESC
            LIMIT 5
            """
            natureza_params = [int(ano), int(conta), int(ug)]
        
        natureza_result = conn.execute(natureza_query, natureza_params).fetchall()
        
        # Adicionar top naturezas aos totais
        totais['top_naturezas'] = []
        for row in natureza_result:
            totais['top_naturezas'].append({
                'natureza': row[0],
                'quantidade': row[1],
                'total': float(row[2] or 0)
            })
        
        conn.close()
        
        return jsonify(totais)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500