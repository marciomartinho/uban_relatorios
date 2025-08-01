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
    """Retorna os valores únicos para os filtros usando cache"""
    try:
        # Verificar se existe cache
        cache_exists_query = """
        SELECT COUNT(*) > 0 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'cache_filtros_despesa'
        """
        cache_exists = db.execute_query(cache_exists_query)[0][0]
        
        if cache_exists:
            # Usar cache (MUITO mais rápido)
            anos_query = """
            SELECT valor FROM public.cache_filtros_despesa 
            WHERE tipo_filtro = 'ano' 
            ORDER BY ordem DESC
            """
            anos = [row[0] for row in db.execute_query(anos_query)]
            
            contas_query = """
            SELECT valor FROM public.cache_filtros_despesa 
            WHERE tipo_filtro = 'conta' 
            ORDER BY ordem
            """
            contas = [row[0] for row in db.execute_query(contas_query)]
            
            ugs_query = """
            SELECT valor, descricao FROM public.cache_filtros_despesa 
            WHERE tipo_filtro = 'ug' 
            ORDER BY ordem
            """
            ugs_raw = db.execute_query(ugs_query)
            # Formatar UG com descrição se disponível
            ugs = []
            for ug, desc in ugs_raw:
                if desc:
                    ugs.append({'valor': ug, 'texto': f"{ug} - {desc[:30]}"})
                else:
                    ugs.append({'valor': ug, 'texto': ug})
        else:
            # Fallback para queries diretas (mais lento)
            # Limitar resultados para não travar
            anos_query = """
            SELECT DISTINCT coexercicio 
            FROM despesas.fato_despesa_saldo 
            ORDER BY coexercicio DESC
            LIMIT 10
            """
            anos = [str(row[0]) for row in db.execute_query(anos_query)]
            
            contas_query = """
            SELECT DISTINCT cocontacontabil 
            FROM despesas.fato_despesa_saldo 
            ORDER BY cocontacontabil
            LIMIT 100
            """
            contas = [str(row[0]) for row in db.execute_query(contas_query)]
            
            ugs_query = """
            SELECT DISTINCT coug, MAX(noug) as nome
            FROM despesas.fato_despesa_saldo 
            GROUP BY coug
            ORDER BY coug
            LIMIT 100
            """
            ugs_raw = db.execute_query(ugs_query)
            ugs = []
            for ug, desc in ugs_raw:
                if desc:
                    ugs.append({'valor': str(ug), 'texto': f"{ug} - {desc[:30]}"})
                else:
                    ugs.append({'valor': str(ug), 'texto': str(ug)})
        
        return jsonify({
            'anos': anos,
            'contas': contas,
            'ugs': ugs,
            'cache': cache_exists
        })
        
    except Exception as e:
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
            query = """
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
            WHERE coexercicio = :ano AND cocontacontabil = :conta
            GROUP BY inmes
            ORDER BY inmes
            """
            params = {"ano": ano, "conta": conta}
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
                cosubelemento
            FROM despesas.fato_despesa_saldo
            WHERE coexercicio = :ano 
                AND cocontacontabil = :conta 
                AND coug = :ug
            ORDER BY inmes, conatureza, cofonte
            """
            params = {"ano": ano, "conta": conta, "ug": ug}
        
        # Executar query
        df = db.read_sql(query, params)
        
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