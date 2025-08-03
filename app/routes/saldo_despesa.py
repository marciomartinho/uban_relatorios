"""
Blueprint para consultas de saldo de despesa
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.database import db
import pandas as pd

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
        # Buscar apenas anos únicos inicialmente
        anos_query = """
        SELECT DISTINCT coexercicio 
        FROM despesas.fato_despesa_saldo 
        ORDER BY coexercicio DESC
        """
        result = db.execute_query(anos_query)
        anos = [str(row[0]) for row in result]
        
        return jsonify({
            'anos': anos
        })
        
    except Exception as e:
        print(f"Erro em get_filtros: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@saldo_despesa.route('/api/contas-por-ano')
def get_contas_por_ano():
    """Retorna as contas contábeis disponíveis para um ano específico"""
    try:
        ano = request.args.get('ano')
        
        if not ano:
            return jsonify({'erro': 'Ano é obrigatório'}), 400
            
        # Validar que ano é numérico para evitar SQL injection
        try:
            int(ano)
        except ValueError:
            return jsonify({'erro': 'Ano deve ser numérico'}), 400
            
        # Buscar contas contábeis que possuem dados no ano selecionado
        contas_query = f"""
        SELECT DISTINCT cocontacontabil 
        FROM despesas.fato_despesa_saldo 
        WHERE coexercicio = {ano}
        ORDER BY cocontacontabil
        """
        
        result = db.execute_query(contas_query)
        contas = [str(row[0]) for row in result]
        
        return jsonify({
            'contas': contas
        })
        
    except Exception as e:
        print(f"Erro em get_contas_por_ano: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@saldo_despesa.route('/api/ugs-por-ano-conta')
def get_ugs_por_ano_conta():
    """Retorna as UGs disponíveis para um ano e conta específicos"""
    try:
        ano = request.args.get('ano')
        conta = request.args.get('conta')
        
        if not all([ano, conta]):
            return jsonify({'erro': 'Ano e conta são obrigatórios'}), 400
            
        # Validar que ano e conta são numéricos para evitar SQL injection
        try:
            int(ano)
            int(conta)
        except ValueError:
            return jsonify({'erro': 'Ano e conta devem ser numéricos'}), 400
            
        # Buscar UGs que possuem dados no ano e conta selecionados
        ugs_query = f"""
        SELECT DISTINCT coug 
        FROM despesas.fato_despesa_saldo 
        WHERE coexercicio = {ano} AND cocontacontabil = {conta}
        ORDER BY coug
        """
        
        result = db.execute_query(ugs_query)
        ugs = [str(row[0]) for row in result]
        
        return jsonify({
            'ugs': ugs
        })
        
    except Exception as e:
        print(f"Erro em get_ugs_por_ano_conta: {str(e)}")
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
        
        # Converter parâmetros para os tipos corretos
        try:
            ano = int(ano)
            conta = int(conta)
            ug = int(ug) if ug != 'CONSOLIDADO' else ug
        except ValueError:
            return jsonify({'erro': 'Parâmetros inválidos'}), 400
        
        # Montar query base
        if ug == 'CONSOLIDADO':
            # Se for consolidado, agrupa por mês
            query = f"""
            SELECT 
                inmes,
                'CONSOLIDADO' as cocontacorrente,
                MAX(intipoadm) as intipoadm,
                SUM(saldo_contabil_despesa) as saldo_contabil_despesa,
                -- Para consolidado, campos individuais ficam nulos
                NULL::integer as conatureza,
                NULL::bigint as cofonte,
                NULL::integer as inesfera,
                NULL::integer as couo,
                NULL::integer as cofuncao,
                NULL::integer as cosubfuncao,
                NULL::integer as coprograma,
                NULL::integer as coprojeto,
                NULL::integer as cosubtitulo,
                -- Campos derivados também nulos
                NULL::varchar as cogrupo,
                NULL::varchar as comodalidade,
                NULL::varchar as coelemento,
                NULL::varchar as cosubelemento
            FROM despesas.fato_despesa_saldo
            WHERE coexercicio = {ano} AND cocontacontabil = {conta}
            GROUP BY inmes
            ORDER BY inmes
            """
        else:
            # Query normal com UG específica
            query = f"""
            SELECT 
                inmes,
                cocontacorrente,
                intipoadm,
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
                cosubelemento
            FROM despesas.fato_despesa_saldo
            WHERE coexercicio = {ano} 
                AND cocontacontabil = {conta} 
                AND coug = {ug}
            ORDER BY inmes, conatureza, cofonte
            """
        
        # Executar query
        df = db.read_sql(query, None)
        
        # Converter para lista de dicionários
        dados = df.to_dict('records')
        
        return jsonify({
            'dados': dados,
            'total': len(dados)
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500