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
    """Retorna os valores únicos para os filtros"""
    try:
        # Buscar anos únicos
        anos_query = """
        SELECT DISTINCT coexercicio 
        FROM receitas.fato_receita_saldo 
        ORDER BY coexercicio DESC
        """
        anos = [row[0] for row in db.execute_query(anos_query)]
        
        # Buscar contas contábeis únicas
        contas_query = """
        SELECT DISTINCT cocontacontabil 
        FROM receitas.fato_receita_saldo 
        ORDER BY cocontacontabil
        """
        contas = [row[0] for row in db.execute_query(contas_query)]
        
        # Buscar UGs únicas
        ugs_query = """
        SELECT DISTINCT coug 
        FROM receitas.fato_receita_saldo 
        ORDER BY coug
        """
        ugs = [row[0] for row in db.execute_query(ugs_query)]
        
        return jsonify({
            'anos': anos,
            'contas': contas,
            'ugs': ugs
        })
        
    except Exception as e:
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
        return jsonify({'erro': str(e)}), 500