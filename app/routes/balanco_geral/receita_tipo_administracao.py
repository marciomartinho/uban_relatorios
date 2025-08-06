"""
API para o quadro Receita Estimada Líquida por Tipo de Administração
Parte do Balanço Geral GDF
Arquivo: app/routes/balanco_geral/receita_tipo_administracao.py
Versão refatorada para buscar a estrutura de receitas (categorias e fontes) dinamicamente.
"""
from flask import Blueprint, jsonify
from app.db_manager import db_manager
from datetime import datetime
import traceback

# Criar blueprint
receita_tipo_adm_api = Blueprint('receita_tipo_adm_api', __name__)

# Mapeamento estático mantido conforme solicitado, pois não há tabela de dimensão.
TIPOS_ADMINISTRACAO = {
    '1': 'ADMINISTRAÇÃO DIRETA',
    '3': 'AUTARQUIAS',
    '4': 'FUNDAÇÕES',
    '5': 'EMPRESAS PÚBLICAS',  # Agrupa Empresa Pública (5) e Economia Mista (6)
    '7': 'FUNDOS'             # Agrupa Fundos (7) e Fundos da Indireta (9)
}

# O dicionário estático ESTRUTURA_RECEITAS foi completamente removido.
# A estrutura de receitas agora é lida dinamicamente do banco de dados.

@receita_tipo_adm_api.route('/api/dados-receita-tipo-administracao')
def get_dados_receita_tipo_administracao():
    """Retorna os dados da receita estimada líquida por tipo de administração"""
    try:
        # Obter ano mais recente (lógica mantida)
        ano_query = "SELECT DISTINCT coexercicio FROM receita_saldo WHERE coexercicio >= 2024 ORDER BY coexercicio DESC LIMIT 1"
        ano_result = db_manager.execute_query(ano_query)

        if not ano_result:
            return jsonify({'erro': 'Nenhum dado encontrado para o ano especificado.'}), 400

        ano_atual = ano_result[0]['coexercicio']

        # Nova Query SQL Dinâmica para buscar receitas, categorias e fontes
        # Adicionado CAST para compatibilidade entre DuckDB e PostgreSQL
        query = """
        WITH dados_agregados AS (
            SELECT
                CAST(rs.cocategoriareceita AS VARCHAR) as cocategoriareceita,
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
            GROUP BY CAST(rs.cocategoriareceita AS VARCHAR), SUBSTRING(rs.cofontereceita, 1, 2), rs.intipoadm
        )
        SELECT
            da.cocategoriareceita,
            da.fonte_principal,
            da.intipoadm,
            da.receita_prevista,
            COALESCE(drc.nocategoriareceita, CONCAT('Categoria ', da.cocategoriareceita)) as nocategoriareceita,
            COALESCE(dro.nofontereceita, CONCAT('Fonte ', da.fonte_principal)) as nofontereceita
        FROM dados_agregados da
        LEFT JOIN DIM_RECEITA_CATEGORIA drc ON da.cocategoriareceita = drc.cocategoriareceita
        LEFT JOIN dim_receita_origem dro ON da.fonte_principal = CAST(dro.cofontereceita AS VARCHAR)
        WHERE da.receita_prevista != 0
        ORDER BY da.cocategoriareceita, da.fonte_principal, da.intipoadm
        """

        # Passar parâmetros como lista para db_manager (ele vai converter para o formato correto)
        params = [ano_atual]
        resultados = db_manager.execute_query(query, params)

        # Processar resultados com a nova função dinâmica
        dados = processar_dados_tipo_administracao_dinamico(resultados)

        return jsonify({
            'ano': ano_atual,
            'dados': dados,
            'colunas': get_colunas_tipo_adm(), # Função mantida pois depende do mapeamento estático
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M')
        })

    except Exception as e:
        print(f"Erro em get_dados_receita_tipo_administracao: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

def get_colunas_tipo_adm():
    """
    Retorna as colunas de tipo de administração para o cabeçalho.
    Mantido pois depende da regra de negócio estática de TIPOS_ADMINISTRACAO.
    """
    return [
        {'codigo': '1', 'nome': 'ADMINISTRAÇÃO DIRETA'},
        {'codigo': '3', 'nome': 'AUTARQUIAS'},
        {'codigo': '4', 'nome': 'FUNDAÇÕES'},
        {'codigo': '5', 'nome': 'EMPRESAS PÚBLICAS'},  # Agrupa 05 e 06
        {'codigo': '7', 'nome': 'FUNDOS'}             # Agrupa 07 e 09
    ]

def processar_dados_tipo_administracao_dinamico(resultados):
    """
    Processa os resultados da query em estrutura hierárquica por tipo de administração
    de forma dinâmica para as categorias e fontes.
    """
    dados_por_categoria = {}
    totais_gerais = {}

    # Etapa 1: Agrupar os dados lidos do banco
    for row in resultados:
        cat_id = row['cocategoriareceita']
        cat_nome = row['nocategoriareceita']
        fonte_id = row['fonte_principal']
        fonte_nome = row['nofontereceita']
        tipo_adm = str(row['intipoadm']) # Garantir que seja string para o lookup
        valor = float(row['receita_prevista'] or 0)

        # Aplicar regra de negócio para agrupar tipos de administração
        if tipo_adm == '6': tipo_adm = '5'  # Agrupa Economia Mista com Empresas Públicas
        if tipo_adm == '9': tipo_adm = '7'  # Agrupa Fundos da Indireta com Fundos

        # Cria a entrada da categoria dinamicamente
        if cat_id not in dados_por_categoria:
            dados_por_categoria[cat_id] = {
                'nome': cat_nome,
                'fontes': {},
                'totais_tipo_adm': {}
            }

        # Cria a entrada da fonte dinamicamente
        if fonte_id not in dados_por_categoria[cat_id]['fontes']:
            dados_por_categoria[cat_id]['fontes'][fonte_id] = {
                'nome': fonte_nome,
                'valores_tipo_adm': {}
            }

        # Inicializa e soma os valores para a fonte
        dados_por_categoria[cat_id]['fontes'][fonte_id]['valores_tipo_adm'][tipo_adm] = \
            dados_por_categoria[cat_id]['fontes'][fonte_id]['valores_tipo_adm'].get(tipo_adm, 0) + valor

        # Inicializa e soma os valores para o total da categoria
        dados_por_categoria[cat_id]['totais_tipo_adm'][tipo_adm] = \
            dados_por_categoria[cat_id]['totais_tipo_adm'].get(tipo_adm, 0) + valor
            
        # Acumula totais gerais
        totais_gerais[tipo_adm] = totais_gerais.get(tipo_adm, 0) + valor

    # Etapa 2: Montar a estrutura final para a API
    dados_finais = []
    # Itera sobre as categorias encontradas, em ordem
    for cat_id, cat_data in sorted(dados_por_categoria.items()):
        categoria = {
            'tipo': 'categoria',
            'nome': cat_data['nome'],
            'valores_tipo_adm': cat_data['totais_tipo_adm'],
            'fontes': []
        }
        
        # Itera sobre as fontes encontradas, em ordem
        for fonte_id, fonte_data in sorted(cat_data['fontes'].items()):
            # Só adiciona a fonte se ela tiver valores
            if any(fonte_data['valores_tipo_adm'].values()):
                fonte = {
                    'tipo': 'fonte',
                    'nome': fonte_data['nome'],
                    'valores_tipo_adm': fonte_data['valores_tipo_adm']
                }
                categoria['fontes'].append(fonte)

        # Só adiciona a categoria se ela tiver valores
        if any(categoria['valores_tipo_adm'].values()):
            dados_finais.append(categoria)

    # Adicionar linha de total
    dados_finais.append({
        'tipo': 'total',
        'nome': 'RECEITA LÍQUIDA',
        'valores_tipo_adm': totais_gerais
    })

    return dados_finais