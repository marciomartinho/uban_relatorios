"""
Blueprint para consultas de saldo de receita
Adaptado para trabalhar com db_manager (DuckDB/PostgreSQL)
"""
from flask import Blueprint, render_template, jsonify, request
from app.db_manager import db_manager
import traceback

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
        # Query para buscar anos distintos
        anos_query = """
        SELECT DISTINCT coexercicio
        FROM receita_saldo
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

@saldo_receita.route('/api/contas-por-ano')
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
            FROM receita_saldo
            WHERE coexercicio = ?
            ORDER BY cocontacontabil
            """
            params = [int(ano)]
        else:
            contas_query = """
            SELECT DISTINCT cocontacontabil
            FROM receita_saldo
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

@saldo_receita.route('/api/ugs-por-ano-conta')
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
            FROM receita_saldo
            WHERE coexercicio = ? AND cocontacontabil = ?
            ORDER BY coug
            """
            params = [int(ano), conta]
        else:
            ugs_query = """
            SELECT DISTINCT coug
            FROM receita_saldo
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
        
        # Montar query base adaptada para ambos os bancos
        if ug == 'CONSOLIDADO':
            # Se for consolidado, agrupa por mês
            if db_manager.is_duckdb:
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
                FROM receita_saldo
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
                FROM receita_saldo
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
                FROM receita_saldo
                WHERE coexercicio = ? AND cocontacontabil = ? AND coug = ?
                ORDER BY inmes, cocontacorrente
                """
                params = [int(ano), conta, ug]
            else:  # PostgreSQL
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
                FROM receita_saldo
                WHERE coexercicio = :ano AND cocontacontabil = :conta AND coug = :ug
                ORDER BY inmes, cocontacorrente
                """
                params = {'ano': int(ano), 'conta': conta, 'ug': ug}
        
        # Executar query
        dados = db_manager.execute_query(query, params)
        
        # Processar dados para garantir tipos corretos
        for dado in dados:
            # Converter valores numéricos
            if 'saldo_contabil_receita' in dado and dado['saldo_contabil_receita'] is not None:
                dado['saldo_contabil_receita'] = float(dado['saldo_contabil_receita'])
            if 'inmes' in dado and dado['inmes'] is not None:
                dado['inmes'] = int(dado['inmes'])
            if 'intipoadm' in dado and dado['intipoadm'] is not None:
                dado['intipoadm'] = int(dado['intipoadm'])
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