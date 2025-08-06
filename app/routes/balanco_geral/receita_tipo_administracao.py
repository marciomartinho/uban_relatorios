"""
API para o quadro Receita Estimada Líquida por Tipo de Administração
Parte do Balanço Geral GDF
Arquivo: app/routes/balanco_geral/receita_tipo_administracao.py
"""
from flask import Blueprint, jsonify
from app.db_manager import db_manager
from datetime import datetime
import traceback

# Criar blueprint
receita_tipo_adm_api = Blueprint('receita_tipo_adm_api', __name__)

# Mapeamento dos tipos de administração
TIPOS_ADMINISTRACAO = {
    '1': 'ADMINISTRAÇÃO DIRETA',
    '3': 'AUTARQUIAS', 
    '4': 'FUNDAÇÕES',
    '5': 'EMPRESAS PÚBLICAS',  # Empresa Pública + Economia Mista
    '6': 'ECONOMIA MISTA',  # Empresa Pública + Economia Mista (agrupados)
    '7': 'FUNDOS',
    '9': 'FUNDOS DA INDIRETA',    # Fundos + Fundos da Indireta (agrupados)
    '11': 'SERVIÇO SOCIAL AUTÔNOMO'
}

# Ordem das colunas para exibição
ORDEM_COLUNAS = ['1', '3', '4', '5', '7']  # Agrupa 05+06 e 07+09

# Estrutura das categorias e fontes (mesma do outro quadro)
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
            '71': 'Impostos, Taxas e Contribuições de Melhoria',
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
        'nomes_fontes': {}  # Não especificado
    }
}

@receita_tipo_adm_api.route('/api/dados-receita-tipo-administracao')
def get_dados_receita_tipo_administracao():
    """Retorna os dados da receita estimada líquida por tipo de administração"""
    try:
        # Obter ano mais recente
        ano_query = """
        SELECT DISTINCT coexercicio 
        FROM receita_saldo 
        WHERE coexercicio >= 2024
        ORDER BY coexercicio DESC
        LIMIT 1
        """
        ano_result = db_manager.execute_query(ano_query)
        
        if not ano_result:
            return jsonify({'erro': 'Nenhum dado encontrado para o ano especificado.'}), 400
        
        ano_atual = ano_result[0]['coexercicio']
        
        # Query para buscar dados agregados por tipo de administração
        query = """
        WITH dados_agregados AS (
            SELECT 
                rs.cocategoriareceita,
                SUBSTRING(rs.cofontereceita, 1, 2) as fonte_principal,
                rs.intipoadm,
                SUM(CASE 
                    WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521199999' 
                    THEN rs.saldo_contabil_receita 
                    ELSE 0 
                END) as receita_prevista
            FROM receita_saldo rs
            WHERE 
                rs.coexercicio = ?
                AND rs.cocategoriareceita IN ('1', '2', '7', '9')
            GROUP BY rs.cocategoriareceita, SUBSTRING(rs.cofontereceita, 1, 2), rs.intipoadm
        )
        SELECT 
            da.cocategoriareceita,
            da.fonte_principal,
            da.intipoadm,
            da.receita_prevista,
            COALESCE(dro.nofontereceita, 'Fonte ' || da.fonte_principal) as nome_fonte
        FROM dados_agregados da
        LEFT JOIN dim_receita_origem dro ON da.fonte_principal = CAST(dro.cofontereceita AS VARCHAR)
        WHERE da.receita_prevista != 0
        ORDER BY da.cocategoriareceita, da.fonte_principal, da.intipoadm
        """
        
        params = [ano_atual]
        resultados = db_manager.execute_query(query, params)
        
        # Processar resultados
        dados = processar_dados_tipo_administracao(resultados, ano_atual)
        
        return jsonify({
            'ano': ano_atual,
            'dados': dados,
            'colunas': get_colunas_tipo_adm(),
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        print(f"Erro em get_dados_receita_tipo_administracao: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def get_colunas_tipo_adm():
    """Retorna as colunas de tipo de administração para o cabeçalho"""
    return [
        {'codigo': '1', 'nome': 'ADMINISTRAÇÃO DIRETA'},
        {'codigo': '3', 'nome': 'AUTARQUIAS'},
        {'codigo': '4', 'nome': 'FUNDAÇÕES'},
        {'codigo': '5', 'nome': 'EMPRESAS PÚBLICAS'},  # Agrupa 05 e 06
        {'codigo': '7', 'nome': 'FUNDOS'}     # Agrupa 07 e 09
    ]

def processar_dados_tipo_administracao(resultados, ano_atual):
    """Processa os resultados da query em estrutura hierárquica por tipo de administração"""
    # Inicializar estrutura de dados
    dados_por_categoria = {}
    
    # Organizar dados por categoria, fonte e tipo de administração
    for row in resultados:
        cat_id = row['cocategoriareceita']
        fonte_id = row['fonte_principal']
        tipo_adm = row['intipoadm']
        valor = float(row['receita_prevista'] or 0)
        
        # Agrupar empresas (05 e 06) e fundos (07 e 09)
        if tipo_adm == '6':
            tipo_adm = '5'  # Agrupa com Empresa Pública
        elif tipo_adm == '9':
            tipo_adm = '7'  # Agrupa com Fundos
        
        if cat_id not in dados_por_categoria:
            dados_por_categoria[cat_id] = {
                'fontes': {},
                'totais_tipo_adm': {}
            }
        
        if fonte_id not in dados_por_categoria[cat_id]['fontes']:
            dados_por_categoria[cat_id]['fontes'][fonte_id] = {
                'nome': row['nome_fonte'],
                'valores_tipo_adm': {}
            }
        
        # Somar ao tipo de administração correto
        if tipo_adm not in dados_por_categoria[cat_id]['fontes'][fonte_id]['valores_tipo_adm']:
            dados_por_categoria[cat_id]['fontes'][fonte_id]['valores_tipo_adm'][tipo_adm] = 0
        dados_por_categoria[cat_id]['fontes'][fonte_id]['valores_tipo_adm'][tipo_adm] += valor
        
        # Acumular totais por tipo de administração
        if tipo_adm not in dados_por_categoria[cat_id]['totais_tipo_adm']:
            dados_por_categoria[cat_id]['totais_tipo_adm'][tipo_adm] = 0
        dados_por_categoria[cat_id]['totais_tipo_adm'][tipo_adm] += valor
    
    # Montar estrutura final
    dados_finais = []
    totais_gerais = {}  # Para linha de total final
    
    for cat_id in ['1', '2', '7', '9']:  # Ordem fixa das categorias
        if cat_id not in ESTRUTURA_RECEITAS:
            continue
            
        cat_info = ESTRUTURA_RECEITAS[cat_id]
        cat_data = dados_por_categoria.get(cat_id, {'fontes': {}, 'totais_tipo_adm': {}})
        
        # Adicionar categoria principal
        categoria = {
            'tipo': 'categoria',
            'nome': cat_info['nome'],
            'valores_tipo_adm': cat_data['totais_tipo_adm'],
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
                    'valores_tipo_adm': fonte_data['valores_tipo_adm']
                }
                
                # Só adicionar se tiver algum valor
                if any(fonte_data['valores_tipo_adm'].values()):
                    categoria['fontes'].append(fonte)
        
        # Só adicionar categoria se tiver algum valor
        if any(cat_data['totais_tipo_adm'].values()):
            dados_finais.append(categoria)
            
            # Acumular para totais gerais
            for tipo_adm, valor in cat_data['totais_tipo_adm'].items():
                if tipo_adm not in totais_gerais:
                    totais_gerais[tipo_adm] = 0
                totais_gerais[tipo_adm] += valor
    
    # Adicionar linha de total
    dados_finais.append({
        'tipo': 'total',
        'nome': 'RECEITA LÍQUIDA',
        'valores_tipo_adm': totais_gerais
    })
    
    return dados_finais