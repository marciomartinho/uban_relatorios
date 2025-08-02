"""
Blueprint para detalhamento de conta contábil de receita
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.database import db
import pandas as pd

# Criar blueprint
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
        # Buscar anos únicos
        anos_query = """
        SELECT DISTINCT CAST(EXTRACT(YEAR FROM dalancamento) AS INTEGER) as ano
        FROM receitas.fato_receita_lancamento 
        WHERE dalancamento IS NOT NULL
        ORDER BY ano DESC
        """
        anos = [row[0] for row in db.execute_query(anos_query)]
        
        # Buscar contas contábeis únicas
        contas_query = """
        SELECT DISTINCT cocontacontabil 
        FROM receitas.fato_receita_lancamento 
        WHERE cocontacontabil IS NOT NULL
        ORDER BY cocontacontabil
        """
        contas = [row[0] for row in db.execute_query(contas_query)]
        
        # Buscar UGs Contábeis únicas
        ugs_query = """
        SELECT DISTINCT cougcontab 
        FROM receitas.fato_receita_lancamento 
        WHERE cougcontab IS NOT NULL
        ORDER BY cougcontab
        """
        ugs = [row[0] for row in db.execute_query(ugs_query)]
        
        return jsonify({
            'anos': anos,
            'contas': contas,
            'ugs': ugs
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
        
        # Validar parâmetros obrigatórios
        if not all([ano, conta, ug]):
            return jsonify({'erro': 'Parâmetros obrigatórios: ano, conta, ug'}), 400
        
        # Montar query base
        if ug == 'CONSOLIDADO':
            # Se for consolidado, busca todos os lançamentos do ano/conta
            query = """
            SELECT 
                CAST(EXTRACT(MONTH FROM dalancamento) AS INTEGER) as mes,
                nudocumento,
                coevento,
                cocontacorrente,
                valancamento,
                indebitocredito,
                coug,
                dalancamento,
                tipo_lancamento
            FROM receitas.fato_receita_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s
            ORDER BY EXTRACT(MONTH FROM dalancamento), dalancamento, nudocumento
            """
            params = (ano, conta)
        else:
            # Query normal com UG Contábil específica
            query = """
            SELECT 
                CAST(EXTRACT(MONTH FROM dalancamento) AS INTEGER) as mes,
                nudocumento,
                coevento,
                cocontacorrente,
                valancamento,
                indebitocredito,
                coug,
                dalancamento,
                tipo_lancamento
            FROM receitas.fato_receita_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s 
                AND cougcontab = %s
            ORDER BY EXTRACT(MONTH FROM dalancamento), dalancamento, nudocumento
            """
            params = (ano, conta, ug)
        
        # Executar query
        df = db.read_sql(query, params)
        
        # Converter data para string no formato brasileiro
        if not df.empty:
            df['dalancamento'] = pd.to_datetime(df['dalancamento']).dt.strftime('%d/%m/%Y')
        
        # Converter para lista de dicionários
        dados = df.to_dict('records')
        
        return jsonify({
            'dados': dados,
            'total': len(dados)
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
        
        # Montar query para totais
        if ug == 'CONSOLIDADO':
            query = """
            SELECT 
                tipo_lancamento,
                COUNT(*) as quantidade,
                SUM(valancamento) as total
            FROM receitas.fato_receita_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s
            GROUP BY tipo_lancamento
            """
            params = (ano, conta)
        else:
            query = """
            SELECT 
                tipo_lancamento,
                COUNT(*) as quantidade,
                SUM(valancamento) as total
            FROM receitas.fato_receita_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s 
                AND cougcontab = %s
            GROUP BY tipo_lancamento
            """
            params = (ano, conta, ug)
        
        # Executar query
        df = db.read_sql(query, params)
        
        # Formatar resultado
        totais = {
            'debito': {'quantidade': 0, 'total': 0},
            'credito': {'quantidade': 0, 'total': 0},
            'saldo': 0
        }
        
        for _, row in df.iterrows():
            if row['tipo_lancamento'] == 'DEBITO':
                totais['debito']['quantidade'] = int(row['quantidade'])
                totais['debito']['total'] = float(row['total'] or 0)
            elif row['tipo_lancamento'] == 'CREDITO':
                totais['credito']['quantidade'] = int(row['quantidade'])
                totais['credito']['total'] = float(row['total'] or 0)
        
        # Calcular saldo baseado no primeiro dígito da conta contábil
        # Se conta começa com 5: débito - crédito
        # Se conta começa com 6: crédito - débito
        if conta and str(conta).startswith('5'):
            totais['saldo'] = totais['debito']['total'] - totais['credito']['total']
        else:
            totais['saldo'] = totais['credito']['total'] - totais['debito']['total']
        
        return jsonify(totais)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500