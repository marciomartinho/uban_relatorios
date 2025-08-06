"""
API para o quadro Receita Estimada Líquida
Parte do Balanço Geral GDF
"""
from flask import Blueprint, jsonify
from app.db_manager import db_manager
from datetime import datetime
import traceback

# Criar blueprint
receita_estimada_api = Blueprint('receita_estimada_api', __name__)

# Mapeamento das categorias e fontes
ESTRUTURA_RECEITAS = {
    '1': {
        'nome': 'RECEITAS CORRENTES',
        'fontes': ['11', '12', '13', '14', '15', '16', '17', '19'],
        'nomes_fontes': {
            '11': 'Impostos, Taxas e Contribuições de Melhoria',
            '12': 'Contribuições',
            '13': 'Receita Patrimonial',
            '14': 'Receita Agropecuária',
            '15': 'Receita Industrial',
            '16': 'Receita de Serviços',
            '17': 'Transferências Correntes',
            '19': 'Outras Receitas Correntes'
        }
    },
    '2': {
        'nome': 'RECEITAS DE CAPITAL',
        'fontes': ['21', '22', '23', '24', '29'],
        'nomes_fontes': {
            '21': 'Operações de Crédito',
            '22': 'Alienação de Bens',
            '23': 'Amortização de Empréstimos',
            '24': 'Transferências de Capital',
            '29': 'Outras Receitas de Capital'
        }
    },
    '7': {
        'nome': 'RECEITAS INTRAORÇAMENTÁRIAS CORRENTES',
        'fontes': ['71', '72', '73', '74', '75', '76', '77', '79'],
        'nomes_fontes': {
            '71': 'Contribuições',
            '72': 'Contribuições',
            '73': 'Receita Patrimonial',
            '74': 'Receita Agropecuária',
            '75': 'Receita Industrial',
            '76': 'Receita de Serviços',
            '77': 'Transferências Correntes',
            '79': 'Outras Receitas Correntes'
        }
    },
    '9': {
        'nome': 'RECURSOS ARRECADADOS EM EXERCÍCIOS ANTERIORES - RPPS',
        'fontes': ['91', '92', '93', '94', '95', '96', '97', '98', '99'],
        'nomes_fontes': {}
    }
}

@receita_estimada_api.route('/api/dados-receita-estimada')
def get_dados_receita_estimada():
    """Retorna os dados da receita estimada líquida"""
    try:
        # Obter anos disponíveis
        anos_query = """
        SELECT DISTINCT coexercicio 
        FROM receita_saldo 
        WHERE coexercicio >= 2024
        ORDER BY coexercicio DESC
        """
        anos_result = db_manager.execute_query(anos_query)
        
        if len(anos_result) < 2:
            return jsonify({'erro': 'Dados insuficientes. São necessários pelo menos 2 anos de dados.'}), 400
        
        # Pegar os dois anos mais recentes
        ano_atual = anos_result[0]['coexercicio']
        ano_anterior = anos_result[1]['coexercicio']
        
        # Query para buscar dados agregados
        query = """
        WITH dados_agregados AS (
            SELECT 
                rs.coexercicio,
                rs.cocategoriareceita,
                SUBSTRING(rs.cofontereceita, 1, 2) as fonte_principal,
                SUM(CASE 
                    WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521199999' 
                    THEN rs.saldo_contabil_receita 
                    ELSE 0 
                END) as receita_prevista
            FROM receita_saldo rs
            WHERE 
                rs.coexercicio IN (?, ?)
                AND rs.cocategoriareceita IN ('1', '2', '7', '9')
            GROUP BY rs.coexercicio, rs.cocategoriareceita, SUBSTRING(rs.cofontereceita, 1, 2)
        )
        SELECT 
            da.coexercicio,
            da.cocategoriareceita,
            da.fonte_principal,
            da.receita_prevista,
            COALESCE(dro.nofontereceita, 'Fonte ' || da.fonte_principal) as nome_fonte
        FROM dados_agregados da
        LEFT JOIN dim_receita_origem dro ON da.fonte_principal = CAST(dro.cofontereceita AS VARCHAR)
        WHERE da.receita_prevista != 0
        ORDER BY da.cocategoriareceita, da.fonte_principal
        """
        
        params = [ano_atual, ano_anterior]
        resultados = db_manager.execute_query(query, params)
        
        # Processar resultados
        dados = processar_dados_receita(resultados, ano_atual, ano_anterior)
        
        return jsonify({
            'ano_atual': ano_atual,
            'ano_anterior': ano_anterior,
            'dados': dados,
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        print(f"Erro em get_dados_receita_estimada: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def processar_dados_receita(resultados, ano_atual, ano_anterior):
    """Processa os resultados da query em estrutura hierárquica"""
    # Inicializar estrutura de dados
    dados_por_categoria = {}
    
    # Organizar dados por categoria e fonte
    for row in resultados:
        cat_id = row['cocategoriareceita']
        fonte_id = row['fonte_principal']
        exercicio = row['coexercicio']
        valor = float(row['receita_prevista'] or 0)
        
        if cat_id not in dados_por_categoria:
            dados_por_categoria[cat_id] = {
                'fontes': {},
                'total_atual': 0,
                'total_anterior': 0
            }
        
        if fonte_id not in dados_por_categoria[cat_id]['fontes']:
            dados_por_categoria[cat_id]['fontes'][fonte_id] = {
                'nome': row['nome_fonte'],
                'valor_atual': 0,
                'valor_anterior': 0
            }
        
        if exercicio == ano_atual:
            dados_por_categoria[cat_id]['fontes'][fonte_id]['valor_atual'] = valor
            dados_por_categoria[cat_id]['total_atual'] += valor
        else:
            dados_por_categoria[cat_id]['fontes'][fonte_id]['valor_anterior'] = valor
            dados_por_categoria[cat_id]['total_anterior'] += valor
    
    # Calcular totais gerais
    total_geral_atual = sum(cat['total_atual'] for cat in dados_por_categoria.values())
    total_geral_anterior = sum(cat['total_anterior'] for cat in dados_por_categoria.values())
    
    # Montar estrutura final
    dados_finais = []
    
    for cat_id in ['1', '2', '7', '9']:  # Ordem fixa das categorias
        if cat_id not in ESTRUTURA_RECEITAS:
            continue
            
        cat_info = ESTRUTURA_RECEITAS[cat_id]
        cat_data = dados_por_categoria.get(cat_id, {'fontes': {}, 'total_atual': 0, 'total_anterior': 0})
        
        # Adicionar categoria principal
        categoria = {
            'tipo': 'categoria',
            'nome': cat_info['nome'],
            'valor_atual': cat_data['total_atual'],
            'valor_anterior': cat_data['total_anterior'],
            'percentual_atual': (cat_data['total_atual'] / total_geral_atual * 100) if total_geral_atual > 0 else 0,
            'percentual_anterior': (cat_data['total_anterior'] / total_geral_anterior * 100) if total_geral_anterior > 0 else 0,
            'variacao': calcular_variacao(cat_data['total_atual'], cat_data['total_anterior']),
            'fontes': []
        }
        
        # Adicionar fontes
        for fonte_id in cat_info['fontes']:
            if fonte_id in cat_data['fontes']:
                fonte_data = cat_data['fontes'][fonte_id]
                nome_fonte = cat_info['nomes_fontes'].get(fonte_id, fonte_data['nome'])
                
                fonte = {
                    'tipo': 'fonte',
                    'nome': nome_fonte,
                    'valor_atual': fonte_data['valor_atual'],
                    'valor_anterior': fonte_data['valor_anterior'],
                    'percentual_atual': (fonte_data['valor_atual'] / total_geral_atual * 100) if total_geral_atual > 0 else 0,
                    'percentual_anterior': (fonte_data['valor_anterior'] / total_geral_anterior * 100) if total_geral_anterior > 0 else 0,
                    'variacao': calcular_variacao(fonte_data['valor_atual'], fonte_data['valor_anterior'])
                }
                
                if fonte['valor_atual'] != 0 or fonte['valor_anterior'] != 0:
                    categoria['fontes'].append(fonte)
        
        if categoria['valor_atual'] != 0 or categoria['valor_anterior'] != 0:
            dados_finais.append(categoria)
    
    # Adicionar linha de total
    dados_finais.append({
        'tipo': 'total',
        'nome': 'RECEITA LÍQUIDA',
        'valor_atual': total_geral_atual,
        'valor_anterior': total_geral_anterior,
        'percentual_atual': 100.0,
        'percentual_anterior': 100.0,
        'variacao': calcular_variacao(total_geral_atual, total_geral_anterior)
    })
    
    return dados_finais

def calcular_variacao(valor_atual, valor_anterior):
    """Calcula a variação percentual entre dois valores"""
    if valor_anterior == 0:
        return 100.0 if valor_atual > 0 else 0.0
    return ((valor_atual - valor_anterior) / abs(valor_anterior)) * 100