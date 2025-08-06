# app/routes/relatorio_receita_fonte.py
"""
Blueprint para Relatório de Receitas por Fonte ou Alínea
Sistema de visualização hierárquica com expansão/colapso
"""
from flask import Blueprint, render_template, jsonify, request
from app.modules.relatorio_receita_fonte import RelatorioReceitaFonte
from datetime import datetime
import traceback

# Criar blueprint
relatorio_receita_fonte = Blueprint('relatorio_receita_fonte', __name__)


@relatorio_receita_fonte.route('/')
def index():
    """Página principal do relatório"""
    return render_template('relatorio_receita_fonte/index.html',
                         title='Relatório Detalhado por Fonte/Receita')


@relatorio_receita_fonte.route('/api/filtros')
def get_filtros():
    """Retorna os filtros disponíveis para o relatório"""
    try:
        from app.db_manager import db_manager
        
        # Buscar anos disponíveis
        anos_query = """
        SELECT DISTINCT coexercicio 
        FROM receita_saldo 
        ORDER BY coexercicio DESC
        """
        anos_result = db_manager.execute_query(anos_query)
        anos = [row['coexercicio'] for row in anos_result]
        
        # Buscar último mês com dados
        ultimo_mes = None
        if anos:
            ano_atual = anos[0]
            meses_query = """
            SELECT DISTINCT inmes 
            FROM receita_saldo 
            WHERE coexercicio = ? 
                AND ABS(saldo_contabil_receita) > 0.01 
            ORDER BY inmes DESC 
            LIMIT 1
            """
            result = db_manager.execute_query(meses_query, [ano_atual])
            ultimo_mes = result[0]['inmes'] if result else 12
        
        # Buscar UGs
        ugs_query = """
        SELECT DISTINCT
            rs.coug,
            COALESCE(ug.noug, 'UG ' || rs.coug) as nome_ug
        FROM receita_saldo rs
        LEFT JOIN dim_unidade_gestora ug ON CAST(rs.coug AS VARCHAR) = CAST(ug.coug AS VARCHAR)
        WHERE ABS(rs.saldo_contabil_receita) > 0.01
        ORDER BY rs.coug
        """
        ugs = []
        for row in db_manager.execute_query(ugs_query):
            ugs.append({
                'codigo': row['coug'],
                'descricao': f"{row['coug']} - {row['nome_ug']}"
            })
        
        return jsonify({
            'anos': anos,
            'ano_atual': anos[0] if anos else None,
            'ultimo_mes': ultimo_mes,
            'ugs': ugs,
            'data_atualizacao': datetime.now().strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        print(f"Erro em get_filtros: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@relatorio_receita_fonte.route('/api/gerar')
def gerar_relatorio():
    """Gera o relatório baseado nos parâmetros"""
    try:
        # Obter parâmetros
        tipo = request.args.get('tipo', 'fonte')  # 'fonte' ou 'receita'
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        coug = request.args.get('coug', '')
        
        # Validar parâmetros obrigatórios
        if not ano or not mes:
            return jsonify({'erro': 'Ano e mês são obrigatórios'}), 400
        
        if tipo not in ['fonte', 'receita']:
            return jsonify({'erro': 'Tipo deve ser "fonte" ou "receita"'}), 400
        
        print(f"DEBUG - Gerando relatório: tipo={tipo}, ano={ano}, mes={mes}, coug={coug}")
        
        # Gerar relatório
        relatorio = RelatorioReceitaFonte()
        resultado = relatorio.gerar_relatorio(
            tipo=tipo,
            ano=ano,
            mes=mes,
            coug=coug if coug else None
        )
        
        # Adicionar informações extras
        resultado['periodo_formatado'] = f"{mes:02d}/{ano}"
        resultado['data_geracao'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Obter nome da UG se especificada
        if coug:
            from app.db_manager import db_manager
            try:
                query = "SELECT noug FROM dim_unidade_gestora WHERE coug = ?"
                result = db_manager.execute_query(query, [int(coug)])
                resultado['nome_ug'] = result[0]['noug'] if result else f"UG {coug}"
            except:
                resultado['nome_ug'] = f"UG {coug}"
        else:
            resultado['nome_ug'] = 'Consolidado'
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Erro em gerar_relatorio: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@relatorio_receita_fonte.route('/api/exportar')
def exportar_relatorio():
    """Exporta o relatório para Excel"""
    try:
        # Obter parâmetros
        tipo = request.args.get('tipo', 'fonte')
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        coug = request.args.get('coug', '')
        formato = request.args.get('formato', 'json')
        
        if not ano or not mes:
            return jsonify({'erro': 'Ano e mês são obrigatórios'}), 400
        
        # Gerar relatório
        relatorio = RelatorioReceitaFonte()
        resultado = relatorio.gerar_relatorio(
            tipo=tipo,
            ano=ano,
            mes=mes,
            coug=coug if coug else None
        )
        
        if formato == 'excel':
            # Preparar dados para Excel
            dados_excel = []
            for item in resultado['dados']:
                dados_excel.append({
                    'Código': item['codigo'],
                    'Descrição': item['descricao'],
                    'Nível': item['nivel'],
                    'Previsão Inicial': item['previsao_inicial'],
                    'Previsão Atualizada': item['previsao_atualizada'],
                    f'Receita {ano}': item['receita_atual'],
                    f'Receita {ano-1}': item['receita_anterior'],
                    'Variação Absoluta': item['variacao_absoluta'],
                    'Variação %': item['variacao_percentual']
                })
            
            # Adicionar totais
            if resultado['totais']:
                dados_excel.append({
                    'Código': '',
                    'Descrição': 'TOTAL GERAL',
                    'Nível': -1,
                    'Previsão Inicial': resultado['totais']['previsao_inicial'],
                    'Previsão Atualizada': resultado['totais']['previsao_atualizada'],
                    f'Receita {ano}': resultado['totais']['receita_atual'],
                    f'Receita {ano-1}': resultado['totais']['receita_anterior'],
                    'Variação Absoluta': resultado['totais']['variacao_absoluta'],
                    'Variação %': resultado['totais']['variacao_percentual']
                })
            
            return jsonify({
                'dados': dados_excel,
                'tipo': tipo,
                'periodo': f"{mes:02d}/{ano}",
                'total_registros': len(dados_excel)
            })
        
        # Retornar JSON padrão
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Erro em exportar_relatorio: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@relatorio_receita_fonte.route('/api/detalhes/<tipo>/<codigo>')
def obter_detalhes(tipo, codigo):
    """Obtém detalhes de um item específico (para expansão futura)"""
    try:
        ano = request.args.get('ano', type=int)
        mes = request.args.get('mes', type=int)
        coug = request.args.get('coug', '')
        
        if not ano or not mes:
            return jsonify({'erro': 'Ano e mês são obrigatórios'}), 400
        
        # Por enquanto, retornar estrutura básica
        # Pode ser expandido para buscar lançamentos ou mais detalhes
        return jsonify({
            'tipo': tipo,
            'codigo': codigo,
            'ano': ano,
            'mes': mes,
            'coug': coug,
            'detalhes': 'Funcionalidade em desenvolvimento'
        })
        
    except Exception as e:
        print(f"Erro em obter_detalhes: {str(e)}")
        return jsonify({'erro': str(e)}), 500