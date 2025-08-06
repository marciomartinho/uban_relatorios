"""
Blueprint para consultas de saldo de despesa
Adaptado para trabalhar com db_manager (DuckDB/PostgreSQL)
"""
from flask import Blueprint, render_template, jsonify, request
from app.db_manager import db_manager
import traceback

# Criar blueprint
saldo_despesa = Blueprint('saldo_despesa', __name__)

@saldo_despesa.route('/consulta')
def consulta():
    """Página de consulta de saldo de despesa"""
    return render_template('saldo_despesa/consulta_saldo_despesa.html',
                         title='Consulta Saldo Despesa')

@saldo_despesa.route('/api/filtros')
def get_filtros():
    """Retorna apenas os anos únicos - filtros iniciais"""
    try:
        # Query para buscar anos distintos
        anos_query = """
        SELECT DISTINCT coexercicio
        FROM despesa_saldo
        ORDER BY coexercicio DESC
        """
        
        anos_result = db_manager.execute_query(anos_query)
        anos = [row['coexercicio'] for row in anos_result]
        
        return jsonify({
            'anos': anos,
            'fonte': 'DuckDB Local' if db_manager.is_duckdb else 'PostgreSQL'
        })
        
    except Exception as e:
        print(f"Erro em get_filtros: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@saldo_despesa.route('/api/contas-por-ano')
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
            FROM despesa_saldo
            WHERE coexercicio = ?
            ORDER BY cocontacontabil
            """
            params = [int(ano)]
        else:
            contas_query = """
            SELECT DISTINCT cocontacontabil
            FROM despesa_saldo
            WHERE coexercicio = :ano
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

@saldo_despesa.route('/api/ugs-por-ano-conta')
def get_ugs_por_ano_conta():
    """Retorna as UGs disponíveis para um ano e conta específicos"""
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
            SELECT DISTINCT coug
            FROM despesa_saldo
            WHERE coexercicio = ? AND cocontacontabil = ?
            ORDER BY coug
            """
            params = [int(ano), conta]
        else:
            ugs_query = """
            SELECT DISTINCT coug
            FROM despesa_saldo
            WHERE coexercicio = :ano AND cocontacontabil = :conta
            ORDER BY coug
            """
            params = {'ano': int(ano), 'conta': conta}
        
        ugs_result = db_manager.execute_query(ugs_query, params)
        ugs = [row['coug'] for row in ugs_result]
        
        return jsonify({
            'ugs': ugs
        })
        
    except Exception as e:
        print(f"Erro em get_ugs_por_ano_conta: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

@saldo_despesa.route('/api/dados')
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
        
        # Montar query base adaptada para ambos os bancos
        if ug == 'CONSOLIDADO':
            # Se for consolidado, agrupa por mês
            if db_manager.is_duckdb:
                query = """
                SELECT 
                    inmes,
                    'CONSOLIDADO' as cocontacorrente,
                    SUM(saldo_contabil_despesa) as saldo_contabil_despesa,
                    -- Para consolidado, campos individuais ficam nulos
                    NULL as conatureza,
                    NULL as cofonte,
                    NULL as inesfera,
                    NULL as couo,
                    NULL as cofuncao,
                    NULL as cosubfuncao,
                    NULL as coprograma,
                    NULL as coprojeto,
                    NULL as cosubtitulo,
                    -- Campos derivados também nulos
                    NULL as cogrupo,
                    NULL as comodalidade,
                    NULL as coelemento,
                    NULL as cosubelemento,
                    0 as tamanho_conta
                FROM despesa_saldo
                WHERE coexercicio = ? AND cocontacontabil = ?
                GROUP BY inmes
                ORDER BY inmes
                """
                params = [int(ano), conta]
            else:  # PostgreSQL
                query = """
                SELECT 
                    inmes,
                    'CONSOLIDADO' as cocontacorrente,
                    SUM(saldo_contabil_despesa) as saldo_contabil_despesa,
                    -- Para consolidado, campos individuais ficam nulos
                    NULL as conatureza,
                    NULL as cofonte,
                    NULL as inesfera,
                    NULL as couo,
                    NULL as cofuncao,
                    NULL as cosubfuncao,
                    NULL as coprograma,
                    NULL as coprojeto,
                    NULL as cosubtitulo,
                    -- Campos derivados também nulos
                    NULL as cogrupo,
                    NULL as comodalidade,
                    NULL as coelemento,
                    NULL as cosubelemento,
                    0 as tamanho_conta
                FROM despesa_saldo
                WHERE coexercicio = :ano AND cocontacontabil = :conta
                GROUP BY inmes
                ORDER BY inmes
                """
                params = {'ano': int(ano), 'conta': conta}
        else:
            # Query normal com UG específica
            if db_manager.is_duckdb:
                query = """
                SELECT 
                    inmes,
                    cocontacorrente,
                    saldo_contabil_despesa,
                    -- Campos principais
                    conatureza,
                    cofonte,
                    inesfera,
                    couo,
                    cofuncao,
                    cosubfuncao,
                    coprograma,
                    coprojeto,
                    cosubtitulo,
                    -- Campos derivados de conatureza
                    cogrupo,
                    comodalidade,
                    coelemento,
                    cosubelemento,
                    -- Tamanho da conta para determinar quais campos mostrar
                    LENGTH(TRIM(cocontacorrente)) as tamanho_conta
                FROM despesa_saldo
                WHERE coexercicio = ? AND cocontacontabil = ? AND coug = ?
                ORDER BY inmes, conatureza, cofonte
                """
                params = [int(ano), conta, ug]
            else:  # PostgreSQL
                query = """
                SELECT 
                    inmes,
                    cocontacorrente,
                    saldo_contabil_despesa,
                    -- Campos principais
                    conatureza,
                    cofonte,
                    inesfera,
                    couo,
                    cofuncao,
                    cosubfuncao,
                    coprograma,
                    coprojeto,
                    cosubtitulo,
                    -- Campos derivados de conatureza
                    cogrupo,
                    comodalidade,
                    coelemento,
                    cosubelemento,
                    -- Tamanho da conta para determinar quais campos mostrar
                    LENGTH(TRIM(cocontacorrente)) as tamanho_conta
                FROM despesa_saldo
                WHERE coexercicio = :ano AND cocontacontabil = :conta AND coug = :ug
                ORDER BY inmes, conatureza, cofonte
                """
                params = {'ano': int(ano), 'conta': conta, 'ug': ug}
        
        # Executar query
        dados = db_manager.execute_query(query, params)
        
        # Processar dados para garantir tipos corretos
        for dado in dados:
            # Converter valores numéricos
            if 'saldo_contabil_despesa' in dado and dado['saldo_contabil_despesa'] is not None:
                dado['saldo_contabil_despesa'] = float(dado['saldo_contabil_despesa'])
            if 'inmes' in dado and dado['inmes'] is not None:
                dado['inmes'] = int(dado['inmes'])
            if 'tamanho_conta' in dado and dado['tamanho_conta'] is not None:
                dado['tamanho_conta'] = int(dado['tamanho_conta'])
        
        # Log temporário para debug
        print(f"🔍 Consulta retornou {len(dados)} registros")
        print(f"   Filtros: ano={ano}, conta={conta}, ug={ug}")
        
        return jsonify({
            'dados': dados,
            'total': len(dados),
            'fonte': 'DuckDB Local' if db_manager.is_duckdb else 'PostgreSQL'
        })
        
    except Exception as e:
        print(f"Erro em get_dados: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500