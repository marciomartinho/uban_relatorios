"""
Blueprint para detalhamento de conta contábil de receita
Adaptado para trabalhar com db_manager (DuckDB/PostgreSQL)
"""
from flask import Blueprint, render_template, jsonify, request
from app.db_manager import db_manager
from datetime import datetime
import traceback

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
        # Query para buscar anos distintos
        if db_manager.is_duckdb:
            anos_query = """
            SELECT DISTINCT YEAR(dalancamento) as ano
            FROM receita_lancamento
            WHERE dalancamento IS NOT NULL
            ORDER BY ano DESC
            """
        else:  # PostgreSQL
            anos_query = """
            SELECT DISTINCT EXTRACT(YEAR FROM dalancamento)::integer as ano
            FROM receita_lancamento
            WHERE dalancamento IS NOT NULL
            ORDER BY ano DESC
            """
        
        anos_result = db_manager.execute_query(anos_query)
        anos = [row['ano'] for row in anos_result]
        
        return jsonify({
            'anos': anos,
            'fonte': 'DuckDB Local' if db_manager.is_duckdb else 'PostgreSQL'
        })
        
    except Exception as e:
        print(f"Erro em get_filtros: {str(e)}")
        traceback.print_exc()
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
        
        # Adaptar query para ambos os bancos
        if db_manager.is_duckdb:
            contas_query = """
            SELECT DISTINCT cocontacontabil
            FROM receita_lancamento
            WHERE YEAR(dalancamento) = ?
                AND cocontacontabil IS NOT NULL
            ORDER BY cocontacontabil
            """
            params = [int(ano)]
        else:
            contas_query = """
            SELECT DISTINCT cocontacontabil
            FROM receita_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = :ano
                AND cocontacontabil IS NOT NULL
            ORDER BY cocontacontabil
            """
            params = {'ano': int(ano)}
        
        contas_result = db_manager.execute_query(contas_query, params)
        contas = [row['cocontacontabil'] for row in contas_result]
        
        return jsonify({
            'contas': contas
        })
        
    except Exception as e:
        print(f"Erro em get_contas_por_ano: {str(e)}")
        traceback.print_exc()
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
        
        # Adaptar query para ambos os bancos
        if db_manager.is_duckdb:
            ugs_query = """
            SELECT DISTINCT cougcontab
            FROM receita_lancamento
            WHERE YEAR(dalancamento) = ?
                AND cocontacontabil = ?
                AND cougcontab IS NOT NULL
            ORDER BY cougcontab
            """
            params = [int(ano), conta]
        else:
            ugs_query = """
            SELECT DISTINCT cougcontab
            FROM receita_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = :ano
                AND cocontacontabil = :conta
                AND cougcontab IS NOT NULL
            ORDER BY cougcontab
            """
            params = {'ano': int(ano), 'conta': conta}
        
        ugs_result = db_manager.execute_query(ugs_query, params)
        ugs = [row['cougcontab'] for row in ugs_result]
        
        return jsonify({
            'ugs': ugs
        })
        
    except Exception as e:
        print(f"Erro em get_ugs_por_ano_conta: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@detalha_receita.route('/api/dados')
def get_dados():
    """Retorna os dados filtrados"""
    try:
        # Pegar parâmetros da query
        ano = request.args.get('ano')
        conta = request.args.get('conta')
        ug = request.args.get('ug')
        limite = request.args.get('limite', 10000)  # Limite maior
        
        # Validar parâmetros obrigatórios
        if not all([ano, conta, ug]):
            return jsonify({'erro': 'Parâmetros obrigatórios: ano, conta, ug'}), 400
        
        # Montar query base adaptada para ambos os bancos
        if db_manager.is_duckdb:
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
        else:  # PostgreSQL
            if ug == 'CONSOLIDADO':
                query = """
                SELECT 
                    EXTRACT(MONTH FROM dalancamento)::integer as mes,
                    nudocumento,
                    coevento,
                    cocontacorrente,
                    valancamento,
                    indebitocredito,
                    coug,
                    TO_CHAR(dalancamento, 'DD/MM/YYYY') as dalancamento,
                    tipo_lancamento,
                    cofonte,
                    coclasseorc
                FROM receita_lancamento
                WHERE EXTRACT(YEAR FROM dalancamento) = :ano 
                    AND cocontacontabil = :conta
                ORDER BY EXTRACT(MONTH FROM dalancamento), dalancamento, nudocumento
                LIMIT :limite
                """
                params = {'ano': int(ano), 'conta': conta, 'limite': int(limite)}
            else:
                query = """
                SELECT 
                    EXTRACT(MONTH FROM dalancamento)::integer as mes,
                    nudocumento,
                    coevento,
                    cocontacorrente,
                    valancamento,
                    indebitocredito,
                    coug,
                    TO_CHAR(dalancamento, 'DD/MM/YYYY') as dalancamento,
                    tipo_lancamento,
                    cofonte,
                    coclasseorc
                FROM receita_lancamento
                WHERE EXTRACT(YEAR FROM dalancamento) = :ano 
                    AND cocontacontabil = :conta 
                    AND cougcontab = :ug
                ORDER BY EXTRACT(MONTH FROM dalancamento), dalancamento, nudocumento
                LIMIT :limite
                """
                params = {'ano': int(ano), 'conta': conta, 'ug': ug, 'limite': int(limite)}
        
        # Executar query
        dados = db_manager.execute_query(query, params)
        
        # Processar dados para garantir tipos corretos
        for dado in dados:
            if 'valancamento' in dado and dado['valancamento'] is not None:
                dado['valancamento'] = float(dado['valancamento'])
            if 'mes' in dado and dado['mes'] is not None:
                dado['mes'] = int(dado['mes'])
        
        # Verificar se tem mais registros
        if db_manager.is_duckdb:
            if ug == 'CONSOLIDADO':
                count_query = """
                SELECT COUNT(*) as total FROM receita_lancamento
                WHERE YEAR(dalancamento) = ? AND cocontacontabil = ?
                """
                count_params = [int(ano), conta]
            else:
                count_query = """
                SELECT COUNT(*) as total FROM receita_lancamento
                WHERE YEAR(dalancamento) = ? AND cocontacontabil = ? AND cougcontab = ?
                """
                count_params = [int(ano), conta, ug]
        else:  # PostgreSQL
            if ug == 'CONSOLIDADO':
                count_query = """
                SELECT COUNT(*) as total FROM receita_lancamento
                WHERE EXTRACT(YEAR FROM dalancamento) = :ano AND cocontacontabil = :conta
                """
                count_params = {'ano': int(ano), 'conta': conta}
            else:
                count_query = """
                SELECT COUNT(*) as total FROM receita_lancamento
                WHERE EXTRACT(YEAR FROM dalancamento) = :ano AND cocontacontabil = :conta AND cougcontab = :ug
                """
                count_params = {'ano': int(ano), 'conta': conta, 'ug': ug}
        
        count_result = db_manager.execute_query(count_query, count_params)
        total_registros = count_result[0]['total'] if count_result else 0
        
        # Log temporário para debug
        print(f"🔍 Consulta retornou {len(dados)} registros")
        print(f"   Filtros: ano={ano}, conta={conta}, ug={ug}")
        
        return jsonify({
            'dados': dados,
            'total': len(dados),
            'total_registros': total_registros,
            'tem_mais': total_registros > len(dados),
            'limite_aplicado': int(limite),
            'fonte': 'DuckDB Local' if db_manager.is_duckdb else 'PostgreSQL'
        })
        
    except Exception as e:
        print(f"Erro em get_dados: {str(e)}")
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
        
        # Montar query para totais adaptada para ambos os bancos
        if db_manager.is_duckdb:
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
        else:  # PostgreSQL
            if ug == 'CONSOLIDADO':
                query = """
                SELECT 
                    tipo_lancamento,
                    COUNT(*) as quantidade,
                    SUM(valancamento) as total
                FROM receita_lancamento
                WHERE EXTRACT(YEAR FROM dalancamento) = :ano 
                    AND cocontacontabil = :conta
                GROUP BY tipo_lancamento
                """
                params = {'ano': int(ano), 'conta': conta}
            else:
                query = """
                SELECT 
                    tipo_lancamento,
                    COUNT(*) as quantidade,
                    SUM(valancamento) as total
                FROM receita_lancamento
                WHERE EXTRACT(YEAR FROM dalancamento) = :ano 
                    AND cocontacontabil = :conta 
                    AND cougcontab = :ug
                GROUP BY tipo_lancamento
                """
                params = {'ano': int(ano), 'conta': conta, 'ug': ug}
        
        # Executar query
        result = db_manager.execute_query(query, params)
        
        # Formatar resultado
        totais = {
            'debito': {'quantidade': 0, 'total': 0},
            'credito': {'quantidade': 0, 'total': 0},
            'saldo': 0
        }
        
        for row in result:
            if row['tipo_lancamento'] == 'DEBITO':
                totais['debito']['quantidade'] = row['quantidade']
                totais['debito']['total'] = float(row['total'] or 0)
            elif row['tipo_lancamento'] == 'CREDITO':
                totais['credito']['quantidade'] = row['quantidade']
                totais['credito']['total'] = float(row['total'] or 0)
        
        # Calcular saldo baseado no primeiro dígito da conta contábil
        if str(conta).startswith('5'):
            totais['saldo'] = totais['debito']['total'] - totais['credito']['total']
        else:
            totais['saldo'] = totais['credito']['total'] - totais['debito']['total']
        
        return jsonify(totais)
        
    except Exception as e:
        print(f"Erro em get_totais: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500