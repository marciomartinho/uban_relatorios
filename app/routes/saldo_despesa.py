"""
Blueprint para consultas de saldo de despesa - Versão DuckDB
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.database_duckdb import db_duckdb
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
        conn = db_duckdb.get_connection()
        
        # Buscar apenas anos únicos inicialmente
        anos_query = """
        SELECT DISTINCT coexercicio 
        FROM despesa_saldo 
        ORDER BY coexercicio DESC
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
        
        conn = db_duckdb.get_connection()
        
        # Buscar contas contábeis que possuem dados no ano selecionado
        contas_query = """
        SELECT DISTINCT cocontacontabil 
        FROM despesa_saldo 
        WHERE coexercicio = ?
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
        
        conn = db_duckdb.get_connection()
        
        # Buscar UGs que possuem dados no ano e conta selecionados
        ugs_query = """
        SELECT DISTINCT coug 
        FROM despesa_saldo 
        WHERE coexercicio = ? AND cocontacontabil = ?
        ORDER BY coug
        """
        
        ugs = [row[0] for row in conn.execute(ugs_query, [int(ano), conta]).fetchall()]
        
        conn.close()
        
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
        
        conn = db_duckdb.get_connection()
        
        # Montar query base
        if ug == 'CONSOLIDADO':
            # Se for consolidado, agrupa por mês
            query = """
            SELECT 
                inmes,
                'CONSOLIDADO' as cocontacorrente,
                MAX(intipoadm) as intipoadm,
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
        else:
            # Query normal com UG específica
            query = """
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
                cosubelemento,
                -- Tamanho da conta para determinar quais campos mostrar
                LENGTH(TRIM(cocontacorrente)) as tamanho_conta
            FROM despesa_saldo
            WHERE coexercicio = ? AND cocontacontabil = ? AND coug = ?
            ORDER BY inmes, conatureza, cofonte
            """
            params = [int(ano), conta, ug]
        
        # Executar query
        result = conn.execute(query, params).fetchall()
        
        # Converter para lista de dicionários
        dados = []
        colunas = ['inmes', 'cocontacorrente', 'intipoadm', 'saldo_contabil_despesa',
                   'conatureza', 'cofonte', 'inesfera', 'couo', 'cofuncao', 
                   'cosubfuncao', 'coprograma', 'coprojeto', 'cosubtitulo',
                   'cogrupo', 'comodalidade', 'coelemento', 'cosubelemento', 
                   'tamanho_conta']
        
        for row in result:
            # Criar dicionário garantindo conversão de tipos
            dado = {}
            for i, col in enumerate(colunas):
                valor = row[i]
                
                # Converter valores numéricos
                if col == 'saldo_contabil_despesa' and valor is not None:
                    dado[col] = float(valor)
                elif col in ['inmes', 'intipoadm', 'tamanho_conta'] and valor is not None:
                    dado[col] = int(valor)
                else:
                    dado[col] = valor
                    
            dados.append(dado)
        
        conn.close()
        
        # Log temporário para debug
        print(f"🔍 Consulta retornou {len(dados)} registros")
        print(f"   Filtros: ano={ano}, conta={conta}, ug={ug}")
        
        return jsonify({
            'dados': dados,
            'total': len(dados),
            'fonte': 'DuckDB Local'
        })
        
    except Exception as e:
        print(f"Erro em get_dados: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500