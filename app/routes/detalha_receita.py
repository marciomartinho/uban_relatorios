"""
Blueprint para detalhamento de conta contábil de receita - Versão DuckDB
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.database_duckdb import db_duckdb
import pandas as pd

# Criar blueprint com o NOME ORIGINAL
detalha_receita = Blueprint('detalha_receita', __name__)

@detalha_receita.route('/consulta')
def consulta():
    """Página de consulta de detalhamento de conta contábil receita"""
    return render_template('detalha_receita/consulta_detalha_receita.html', 
                         title='Detalha Conta Contábil Receita')

@detalha_receita.route('/api/filtros')
def get_filtros():
    """Retorna os valores únicos para os filtros"""
    try:
        conn = db_duckdb.get_connection()
        
        # Buscar anos únicos
        anos_query = """
        SELECT DISTINCT YEAR(dalancamento) as ano
        FROM receita_lancamento 
        WHERE dalancamento IS NOT NULL
        ORDER BY ano DESC
        """
        anos = [row[0] for row in conn.execute(anos_query).fetchall()]
        
        # Buscar contas contábeis únicas (top 100 mais usadas)
        contas_query = """
        SELECT cocontacontabil, COUNT(*) as qtd
        FROM receita_lancamento 
        WHERE cocontacontabil IS NOT NULL
        GROUP BY cocontacontabil
        ORDER BY cocontacontabil ASC  -- Mudança aqui: ordenar por conta, não por quantidade
        LIMIT 100
        """
        contas_result = conn.execute(contas_query).fetchall()
        contas = [row[0] for row in contas_result]
        
        # Buscar UGs Contábeis únicas
        ugs_query = """
        SELECT DISTINCT cougcontab 
        FROM receita_lancamento 
        WHERE cougcontab IS NOT NULL
        ORDER BY cougcontab
        """
        ugs = [row[0] for row in conn.execute(ugs_query).fetchall()]
        
        conn.close()
        
        return jsonify({
            'anos': anos,
            'contas': contas,
            'ugs': ugs,
            'fonte': 'DuckDB Local'
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@detalha_receita.route('/api/dados')
def get_dados():
    """Retorna os dados filtrados"""
    try:
        # Pegar parâmetros da query
        ano = request.args.get('ano')
        conta = request.args.get('conta')
        ug = request.args.get('ug')
        limite = request.args.get('limite', 5000)  # Limite padrão maior no DuckDB
        
        # Validar parâmetros obrigatórios
        if not all([ano, conta, ug]):
            return jsonify({'erro': 'Parâmetros obrigatórios: ano, conta, ug'}), 400
        
        conn = db_duckdb.get_connection()
        
        # Montar query base
        if ug == 'CONSOLIDADO':
            # Se for consolidado, busca todos os lançamentos do ano/conta
            query = """
            SELECT 
                MONTH(dalancamento) as mes,
                nudocumento,
                coevento,
                cocontacorrente,
                valancamento,
                indebitocredito,
                coug,
                strftime('%d/%m/%Y', dalancamento) as dalancamento,
                tipo_lancamento,
                cofonte,
                coclasseorc
            FROM receita_lancamento
            WHERE YEAR(dalancamento) = ? 
                AND cocontacontabil = ?
            ORDER BY MONTH(dalancamento), dalancamento, nudocumento
            LIMIT ?
            """
            params = [int(ano), int(conta), int(limite)]
        else:
            # Query normal com UG Contábil específica
            query = """
            SELECT 
                MONTH(dalancamento) as mes,
                nudocumento,
                coevento,
                cocontacorrente,
                valancamento,
                indebitocredito,
                coug,
                strftime('%d/%m/%Y', dalancamento) as dalancamento,
                tipo_lancamento,
                cofonte,
                coclasseorc
            FROM receita_lancamento
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
                'cocontacorrente': row[3],
                'valancamento': row[4],
                'indebitocredito': row[5],
                'coug': row[6],
                'dalancamento': row[7],
                'tipo_lancamento': row[8],
                'cofonte': row[9],
                'coclasseorc': row[10]
            })
        
        # Verificar se tem mais registros
        if ug == 'CONSOLIDADO':
            count_query = """
            SELECT COUNT(*) FROM receita_lancamento
            WHERE YEAR(dalancamento) = ? AND cocontacontabil = ?
            """
            count_params = [int(ano), int(conta)]
        else:
            count_query = """
            SELECT COUNT(*) FROM receita_lancamento
            WHERE YEAR(dalancamento) = ? AND cocontacontabil = ? AND cougcontab = ?
            """
            count_params = [int(ano), int(conta), int(ug)]
        
        total_registros = conn.execute(count_query, count_params).fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'dados': dados,
            'total': len(dados),
            'total_real': total_registros,
            'tem_mais': total_registros > len(dados),
            'fonte': 'DuckDB Local'
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@detalha_receita.route('/api/totais')
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
            FROM receita_lancamento
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
            FROM receita_lancamento
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
        
        conn.close()
        
        return jsonify(totais)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500