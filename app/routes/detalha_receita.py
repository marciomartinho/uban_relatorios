"""
Blueprint para detalhamento de conta contábil de receita - Versão DuckDB com Filtros em Cascata
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.database_duckdb import db_duckdb
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
    """Retorna apenas os anos únicos - filtros iniciais"""
    try:
        conn = db_duckdb.get_connection()
        
        # Buscar apenas anos únicos inicialmente
        anos_query = """
        SELECT DISTINCT YEAR(dalancamento) as ano
        FROM receita_lancamento 
        WHERE dalancamento IS NOT NULL
        ORDER BY ano DESC
        """
        anos = [row[0] for row in conn.execute(anos_query).fetchall()]
        
        conn.close()
        
        return jsonify({
            'anos': anos,
            'fonte': 'DuckDB Local'
        })
        
    except Exception as e:
        print(f"Erro em get_filtros: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@detalha_receita.route('/api/contas-por-ano')
def get_contas_por_ano():
    """Retorna as contas contábeis disponíveis para um ano específico"""
    try:
        ano = request.args.get('ano')
        
        if not ano:
            return jsonify({'erro': 'Ano é obrigatório'}), 400
            
        # Validar que ano é numérico
        try:
            int(ano)
        except ValueError:
            return jsonify({'erro': 'Ano deve ser numérico'}), 400
        
        conn = db_duckdb.get_connection()
        
        # Buscar contas contábeis que possuem dados no ano selecionado
        contas_query = """
        SELECT DISTINCT cocontacontabil 
        FROM receita_lancamento 
        WHERE YEAR(dalancamento) = ?
            AND cocontacontabil IS NOT NULL
        ORDER BY cocontacontabil
        """
        
        contas = [row[0] for row in conn.execute(contas_query, [int(ano)]).fetchall()]
        
        conn.close()
        
        return jsonify({
            'contas': contas
        })
        
    except Exception as e:
        print(f"Erro em get_contas_por_ano: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@detalha_receita.route('/api/ugs-por-ano-conta')
def get_ugs_por_ano_conta():
    """Retorna as UGs contábeis disponíveis para um ano e conta específicos"""
    try:
        ano = request.args.get('ano')
        conta = request.args.get('conta')
        
        if not all([ano, conta]):
            return jsonify({'erro': 'Ano e conta são obrigatórios'}), 400
            
        # Validar que ano é numérico
        try:
            int(ano)
        except ValueError:
            return jsonify({'erro': 'Ano deve ser numérico'}), 400
        
        conn = db_duckdb.get_connection()
        
        # Buscar UGs contábeis que possuem dados no ano e conta selecionados
        ugs_query = """
        SELECT DISTINCT cougcontab 
        FROM receita_lancamento 
        WHERE YEAR(dalancamento) = ? 
            AND cocontacontabil = ?
            AND cougcontab IS NOT NULL
        ORDER BY cougcontab
        """
        
        ugs = [row[0] for row in conn.execute(ugs_query, [int(ano), conta]).fetchall()]
        
        conn.close()
        
        return jsonify({
            'ugs': ugs
        })
        
    except Exception as e:
        print(f"Erro em get_ugs_por_ano_conta: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@detalha_receita.route('/api/dados')
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
            params = [int(ano), conta, int(limite)]
        else:
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
            params = [int(ano), conta, ug, int(limite)]
        
        # Executar query
        result = conn.execute(query, params).fetchall()
        
        # Converter para lista de dicionários
        dados = []
        colunas = ['mes', 'nudocumento', 'coevento', 'cocontacorrente',
                   'valancamento', 'indebitocredito', 'coug', 'dalancamento',
                   'tipo_lancamento', 'cofonte', 'coclasseorc']
        
        for row in result:
            # Criar dicionário garantindo conversão de tipos
            dado = {}
            for i, col in enumerate(colunas):
                valor = row[i]
                
                # Converter valores numéricos
                if col == 'valancamento' and valor is not None:
                    dado[col] = float(valor)
                elif col == 'mes' and valor is not None:
                    dado[col] = int(valor)
                else:
                    dado[col] = valor
                    
            dados.append(dado)
        
        # Verificar se tem mais registros
        if ug == 'CONSOLIDADO':
            count_query = """
            SELECT COUNT(*) FROM receita_lancamento
            WHERE YEAR(dalancamento) = ? AND cocontacontabil = ?
            """
            count_params = [int(ano), conta]
        else:
            count_query = """
            SELECT COUNT(*) FROM receita_lancamento
            WHERE YEAR(dalancamento) = ? AND cocontacontabil = ? AND cougcontab = ?
            """
            count_params = [int(ano), conta, ug]
        
        total_registros = conn.execute(count_query, count_params).fetchone()[0]
        
        conn.close()
        
        # Log temporário para debug
        print(f"🔍 Consulta retornou {len(dados)} registros")
        print(f"   Filtros: ano={ano}, conta={conta}, ug={ug}")
        
        return jsonify({
            'dados': dados,
            'total': len(dados),
            'total_registros': total_registros,
            'tem_mais': total_registros > len(dados),
            'limite_aplicado': int(limite),
            'fonte': 'DuckDB Local'
        })
        
    except Exception as e:
        print(f"Erro em get_dados: {str(e)}")
        import traceback
        traceback.print_exc()
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
            params = [int(ano), conta]
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
            params = [int(ano), conta, ug]
        
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