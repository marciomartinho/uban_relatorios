"""
Blueprint para consultas de saldo de receita
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.database import db
import pandas as pd

# Criar blueprint
saldo_receita = Blueprint('saldo_receita', __name__)

@saldo_receita.route('/consulta')
def consulta():
    """Página de consulta de saldo de receita"""
    return render_template('saldo_receita/consulta_saldo_receita.html', 
                         title='Consulta Saldo Receita')

@saldo_receita.route('/api/filtros')
def get_filtros():
    """Retorna apenas os anos únicos - filtros iniciais"""
    try:
        # Buscar apenas anos únicos inicialmente
        anos_query = """
        SELECT DISTINCT coexercicio 
        FROM receitas.fato_receita_saldo 
        ORDER BY coexercicio DESC
        """
        result = db.execute_query(anos_query)
        anos = [row[0] for row in result]
        
        return jsonify({
            'anos': anos
        })
        
    except Exception as e:
        print(f"Erro em get_filtros: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@saldo_receita.route('/api/contas-por-ano')
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
        FROM receitas.fato_receita_saldo 
        WHERE coexercicio = '{ano}'
        ORDER BY cocontacontabil
        """
        
        result = db.execute_query(contas_query)
        contas = [row[0] for row in result]
        
        return jsonify({
            'contas': contas
        })
        
    except Exception as e:
        print(f"Erro em get_contas_por_ano: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@saldo_receita.route('/api/ugs-por-ano-conta')
def get_ugs_por_ano_conta():
    """Retorna as UGs disponíveis para um ano e conta específicos"""
    try:
        ano = request.args.get('ano')
        conta = request.args.get('conta')
        
        if not all([ano, conta]):
            return jsonify({'erro': 'Ano e conta são obrigatórios'}), 400
            
        # Validar que ano é numérico para evitar SQL injection
        try:
            int(ano)
        except ValueError:
            return jsonify({'erro': 'Ano deve ser numérico'}), 400
            
        # Escapar conta para evitar SQL injection
        conta_escaped = conta.replace("'", "''")
            
        # Buscar UGs que possuem dados no ano e conta selecionados
        ugs_query = f"""
        SELECT DISTINCT coug 
        FROM receitas.fato_receita_saldo 
        WHERE coexercicio = '{ano}' AND cocontacontabil = '{conta_escaped}'
        ORDER BY coug
        """
        
        result = db.execute_query(ugs_query)
        ugs = [row[0] for row in result]
        
        return jsonify({
            'ugs': ugs
        })
        
    except Exception as e:
        print(f"Erro em get_ugs_por_ano_conta: {str(e)}")
        return jsonify({'erro': str(e)}), 500

@saldo_receita.route('/api/dados')
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
            # Se for consolidado, agrupa por mês
            query = """
            SELECT 
                inmes,
                'CONSOLIDADO' as cocontacorrente,
                MAX(intipoadm) as intipoadm,
                SUM(saldo_contabil_receita) as saldo_contabil_receita,
                -- Campos que serão NULL no consolidado
                NULL as coclasseorc,
                NULL as cofonte,
                NULL as cocategoriareceita,
                NULL as cofontereceita,
                NULL as cosubfontereceita,
                NULL as corubrica,
                NULL as coalinea,
                NULL as inesfera,
                NULL as couo,
                NULL as cofuncao,
                NULL as cosubfuncao,
                NULL as coprograma,
                NULL as coprojeto,
                NULL as cosubtitulo,
                NULL as conatureza,
                NULL as incategoria,
                NULL as cogrupo,
                NULL as comodalidade,
                NULL as coelemento,
                0 as tamanho_conta
            FROM receitas.fato_receita_saldo
            WHERE coexercicio = %s AND cocontacontabil = %s
            GROUP BY inmes
            ORDER BY inmes
            """
            params = (ano, conta)
        else:
            # Query normal com UG específica
            query = """
            SELECT 
                inmes,
                cocontacorrente,
                intipoadm,
                saldo_contabil_receita,
                -- Campos de 17 chars
                coclasseorc,
                cofonte,
                cocategoriareceita,
                cofontereceita,
                cosubfontereceita,
                corubrica,
                coalinea,
                -- Campos de 38 chars
                inesfera,
                couo,
                cofuncao,
                cosubfuncao,
                coprograma,
                coprojeto,
                cosubtitulo,
                conatureza,
                incategoria,
                cogrupo,
                comodalidade,
                coelemento,
                -- Tamanho da conta para determinar quais campos mostrar
                LENGTH(TRIM(cocontacorrente)) as tamanho_conta
            FROM receitas.fato_receita_saldo
            WHERE coexercicio = %s AND cocontacontabil = %s AND coug = %s
            ORDER BY inmes, cocontacorrente
            """
            params = (ano, conta, ug)
        
        # Executar query
        df = db.read_sql(query, params)
        
        # Converter para lista de dicionários
        dados = df.to_dict('records')
        
        return jsonify({
            'dados': dados,
            'total': len(dados)
        })
        
    except Exception as e:
        print(f"Erro em get_dados: {str(e)}")
        return jsonify({'erro': str(e)}), 500