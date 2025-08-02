"""
Blueprint para detalhamento de conta contábil de despesa
Otimizado para grandes volumes de dados
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.database import db
import pandas as pd

# Criar blueprint
detalha_despesa = Blueprint('detalha_despesa', __name__)

@detalha_despesa.route('/consulta')
def consulta():
    """Página de consulta de detalhamento de conta contábil despesa"""
    return render_template('detalha_despesa/consulta_detalha_despesa.html', 
                         title='Detalha Conta Contábil Despesa')

@detalha_despesa.route('/api/filtros')
def get_filtros():
    """Retorna os valores únicos para os filtros usando cache quando disponível"""
    try:
        # Verificar se existe cache para anos (mesma estratégia do saldo_despesa)
        cache_exists_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'cache_filtros_despesa'
        );
        """
        result = db.execute_query(cache_exists_query)
        cache_exists = result[0][0] if result else False
        
        # Se tem cache, usar para anos e UGs (mais rápido)
        if cache_exists:
            # Anos do cache
            anos_query = """
            SELECT valor FROM public.cache_filtros_despesa 
            WHERE tipo_filtro = 'ano' 
            ORDER BY ordem DESC
            """
            anos = [row[0] for row in db.execute_query(anos_query)]
            
            # UGs do cache
            ugs_query = """
            SELECT valor, descricao FROM public.cache_filtros_despesa 
            WHERE tipo_filtro = 'ug' 
            ORDER BY ordem
            """
            ugs_raw = db.execute_query(ugs_query)
            ugs = []
            for ug, desc in ugs_raw:
                if desc:
                    ugs.append({'valor': ug, 'texto': f"{ug} - {desc[:30]}"})
                else:
                    ugs.append({'valor': ug, 'texto': ug})
        else:
            # Fallback sem cache (mais lento)
            # Anos
            anos_query = """
            SELECT DISTINCT CAST(EXTRACT(YEAR FROM dalancamento) AS INTEGER) as ano
            FROM despesas.fato_despesa_lancamento 
            WHERE dalancamento IS NOT NULL
            ORDER BY ano DESC
            LIMIT 10
            """
            anos = [str(row[0]) for row in db.execute_query(anos_query)]
            
            # UGs - limitar para não travar
            ugs_query = """
            SELECT DISTINCT cougcontab 
            FROM despesas.fato_despesa_lancamento 
            WHERE cougcontab IS NOT NULL
            ORDER BY cougcontab
            LIMIT 100
            """
            ugs = [{'valor': str(row[0]), 'texto': str(row[0])} for row in db.execute_query(ugs_query)]
        
        # Contas contábeis - sempre direto da tabela de lançamento (pode ter contas diferentes)
        contas_query = """
        SELECT DISTINCT cocontacontabil 
        FROM despesas.fato_despesa_lancamento 
        WHERE cocontacontabil IS NOT NULL
        ORDER BY cocontacontabil
        LIMIT 500
        """
        contas = [str(row[0]) for row in db.execute_query(contas_query)]
        
        return jsonify({
            'anos': anos,
            'contas': contas,
            'ugs': ugs,
            'cache_disponivel': cache_exists
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

@detalha_despesa.route('/api/dados')
def get_dados():
    """Retorna os dados filtrados com limite para performance"""
    try:
        # Pegar parâmetros da query
        ano = request.args.get('ano')
        conta = request.args.get('conta')
        ug = request.args.get('ug')
        limite = request.args.get('limite', '1000')  # Limite padrão de 1000 registros
        
        # Validar parâmetros obrigatórios
        if not all([ano, conta, ug]):
            return jsonify({'erro': 'Parâmetros obrigatórios: ano, conta, ug'}), 400
        
        # Converter limite
        try:
            limite = min(int(limite), 5000)  # Máximo 5000 registros por vez
        except:
            limite = 1000
        
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
                tipo_lancamento,
                conatureza,
                cofonte,
                couo,
                coprograma
            FROM despesas.fato_despesa_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s
            ORDER BY EXTRACT(MONTH FROM dalancamento), dalancamento, nudocumento
            LIMIT %s
            """
            params = (ano, conta, limite)
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
                tipo_lancamento,
                conatureza,
                cofonte,
                couo,
                coprograma
            FROM despesas.fato_despesa_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s 
                AND cougcontab = %s
            ORDER BY EXTRACT(MONTH FROM dalancamento), dalancamento, nudocumento
            LIMIT %s
            """
            params = (ano, conta, ug, limite)
        
        # Executar query
        df = db.read_sql(query, params)
        
        # Converter data para string no formato brasileiro
        if not df.empty:
            df['dalancamento'] = pd.to_datetime(df['dalancamento']).dt.strftime('%d/%m/%Y')
        
        # Converter para lista de dicionários
        dados = df.to_dict('records')
        
        # Verificar se há mais registros além do limite
        # Query separada para contar total de registros
        if ug == 'CONSOLIDADO':
            count_query = """
            SELECT COUNT(*) as total_registros
            FROM despesas.fato_despesa_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s
            """
            count_params = (ano, conta)
        else:
            count_query = """
            SELECT COUNT(*) as total_registros
            FROM despesas.fato_despesa_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s 
                AND cougcontab = %s
            """
            count_params = (ano, conta, ug)
        
        count_result = db.read_sql(count_query, count_params)
        total_registros = count_result['total_registros'][0] if not count_result.empty else len(dados)
        
        return jsonify({
            'dados': dados,
            'total': len(dados),
            'total_registros': int(total_registros),
            'tem_mais': bool(total_registros > limite),
            'limite_aplicado': limite
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

@detalha_despesa.route('/api/totais')
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
            FROM despesas.fato_despesa_lancamento
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
            FROM despesas.fato_despesa_lancamento
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
        
        # Adicionar informações sobre natureza de despesa mais frequente
        if ug == 'CONSOLIDADO':
            natureza_query = """
            SELECT 
                conatureza,
                COUNT(*) as quantidade,
                SUM(valancamento) as total
            FROM despesas.fato_despesa_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s
            GROUP BY conatureza
            ORDER BY total DESC
            LIMIT 5
            """
            natureza_result = db.read_sql(natureza_query, params)
        else:
            natureza_query = """
            SELECT 
                conatureza,
                COUNT(*) as quantidade,
                SUM(valancamento) as total
            FROM despesas.fato_despesa_lancamento
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s
                AND cougcontab = %s
            GROUP BY conatureza
            ORDER BY total DESC
            LIMIT 5
            """
            natureza_result = db.read_sql(natureza_query, params)
        
        # Adicionar top naturezas aos totais
        totais['top_naturezas'] = []
        for _, row in natureza_result.iterrows():
            if row['conatureza']:
                totais['top_naturezas'].append({
                    'natureza': row['conatureza'],
                    'quantidade': int(row['quantidade']),
                    'total': float(row['total'] or 0)
                })
        
        return jsonify(totais)
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'erro': str(e)}), 500

@detalha_despesa.route('/api/dados-paginados', methods=['POST'])
def get_dados_paginados():
    """Retorna dados paginados para DataTables server-side"""
    try:
        # Parâmetros do DataTables
        draw = request.form.get('draw', type=int)
        start = request.form.get('start', type=int)
        length = request.form.get('length', type=int)
        search_value = request.form.get('search[value]', '')
        
        # Parâmetros dos filtros
        ano = request.form.get('ano')
        conta = request.form.get('conta')
        ug = request.form.get('ug')
        
        # Validar parâmetros obrigatórios
        if not all([ano, conta, ug]):
            return jsonify({'error': 'Parâmetros obrigatórios: ano, conta, ug'}), 400
        
        # Ordenação
        order_column = int(request.form.get('order[0][column]', 0))
        order_dir = request.form.get('order[0][dir]', 'asc')
        
        # Mapeamento de colunas para ordenação
        columns = ['mes', 'nudocumento', 'coevento', 'conatureza', 'cocontacorrente', 
                  'valancamento', 'indebitocredito', 'coug', 'dalancamento', 'tipo_lancamento']
        order_by = columns[order_column] if order_column < len(columns) else 'mes'
        
        # Query base
        if ug == 'CONSOLIDADO':
            where_clause = """
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s
            """
            params = [ano, conta]
            count_params = [ano, conta]
        else:
            where_clause = """
            WHERE EXTRACT(YEAR FROM dalancamento) = %s 
                AND cocontacontabil = %s 
                AND cougcontab = %s
            """
            params = [ano, conta, ug]
            count_params = [ano, conta, ug]
        
        # Adicionar busca se houver
        if search_value:
            where_clause += """
                AND (
                    CAST(nudocumento AS TEXT) ILIKE %s OR
                    CAST(coevento AS TEXT) ILIKE %s OR
                    CAST(cocontacorrente AS TEXT) ILIKE %s OR
                    CAST(conatureza AS TEXT) ILIKE %s
                )
            """
            search_param = f'%{search_value}%'
            params.extend([search_param, search_param, search_param, search_param])
            count_params.extend([search_param, search_param, search_param, search_param])
        
        # Query para contar total de registros filtrados
        count_query = f"""
            SELECT COUNT(*) as total
            FROM despesas.fato_despesa_lancamento
            {where_clause}
        """
        
        count_result = db.read_sql(count_query, count_params)
        records_filtered = int(count_result['total'][0]) if not count_result.empty else 0
        
        # Query para buscar dados paginados
        data_query = f"""
            SELECT 
                CAST(EXTRACT(MONTH FROM dalancamento) AS INTEGER) as mes,
                nudocumento,
                coevento,
                cocontacorrente,
                valancamento,
                indebitocredito,
                coug,
                dalancamento,
                tipo_lancamento,
                conatureza,
                cofonte,
                couo,
                coprograma
            FROM despesas.fato_despesa_lancamento
            {where_clause}
            ORDER BY {order_by} {order_dir.upper()}
            LIMIT %s OFFSET %s
        """
        
        params.extend([length, start])
        
        # Executar query
        df = db.read_sql(data_query, params)
        
        # Converter data para string no formato brasileiro
        if not df.empty:
            df['dalancamento'] = pd.to_datetime(df['dalancamento']).dt.strftime('%d/%m/%Y')
        
        # Preparar dados para DataTables
        data = []
        for _, row in df.iterrows():
            data.append([
                row['mes'],
                row['nudocumento'] or '-',
                row['coevento'] or '-',
                row['conatureza'] or '-',
                row['cocontacorrente'] or '-',
                row['valancamento'],
                row['indebitocredito'] or '-',
                row['coug'] or '-',
                row['dalancamento'] or '-',
                row['tipo_lancamento'] or '-'
            ])
        
        # Resposta no formato esperado pelo DataTables
        response = {
            'draw': draw,
            'recordsTotal': records_filtered,  # Total de registros
            'recordsFiltered': records_filtered,  # Total após filtros
            'data': data
        }
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500