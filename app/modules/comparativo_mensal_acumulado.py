# app/modules/comparativo_mensal_acumulado.py
"""
Módulo para gerar o comparativo mensal acumulado de receitas
Mostra a evolução acumulada mês a mês com variações percentuais
Adaptado para trabalhar com a estrutura DuckDB do sistema
"""

from flask import Blueprint, jsonify, request
from app.db_manager import db_manager
from datetime import datetime
import traceback

# Criar blueprint
comparativo_mensal = Blueprint('comparativo_mensal', __name__)

class ComparativoMensalAcumulado:
    """Classe para gerar dados do comparativo mensal acumulado"""
    
    def __init__(self):
        self.meses_nomes = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
    
    def gerar_comparativo(self, ano: int, coug: str = None, tipo_receita: str = None):
        """
        Gera o comparativo mensal acumulado de receitas
        """
        # Construir filtros
        filtros_sql = []
        params = {'ano': ano, 'ano_anterior': ano - 1}
        
        if coug:
            filtros_sql.append("rs.coug = :coug")
            params['coug'] = coug
        
        # Filtro por tipo de receita (fonte)
        if tipo_receita and tipo_receita != 'todas':
            # Para receitas intra-orçamentárias, incluir também as correspondentes
            if tipo_receita in ['11', '12', '13', '14', '15', '16', '17', '19']:
                filtros_sql.append(f"(SUBSTRING(rs.cofontereceita, 1, 2) IN ('{tipo_receita}', '7{tipo_receita[1:]}'))")
            else:
                filtros_sql.append(f"SUBSTRING(rs.cofontereceita, 1, 2) = '{tipo_receita}'")
        
        where_clause = " AND " + " AND ".join(filtros_sql) if filtros_sql else ""
        
        # Query adaptada para DuckDB
        if db_manager.is_duckdb:
            query = f"""
            WITH receitas_mensais AS (
                SELECT
                    rs.coexercicio,
                    rs.inmes,
                    SUM(CASE 
                        WHEN rs.cocontacontabil >= '621200000' AND rs.cocontacontabil <= '621399999' 
                        THEN rs.saldo_contabil_receita 
                        ELSE 0 
                    END) as receita_liquida
                FROM receita_saldo rs
                WHERE
                    rs.coexercicio IN (?, ?)
                    AND rs.cocategoriareceita IN ('1', '2', '7')
                    {where_clause.replace(':coug', '?').replace(':ano', '?').replace(':ano_anterior', '?')}
                GROUP BY rs.coexercicio, rs.inmes
            ),
            meses_acumulados AS (
                SELECT 
                    m1.coexercicio,
                    m1.inmes,
                    SUM(m2.receita_liquida) as receita_acumulada
                FROM receitas_mensais m1
                JOIN receitas_mensais m2 
                    ON m1.coexercicio = m2.coexercicio 
                    AND m2.inmes <= m1.inmes
                GROUP BY m1.coexercicio, m1.inmes
            )
            SELECT
                atual.inmes,
                atual.receita_acumulada as receita_atual,
                COALESCE(anterior.receita_acumulada, 0) as receita_anterior
            FROM meses_acumulados atual
            LEFT JOIN meses_acumulados anterior 
                ON atual.inmes = anterior.inmes 
                AND anterior.coexercicio = ?
            WHERE atual.coexercicio = ?
            ORDER BY atual.inmes
            """
            # Preparar parâmetros para DuckDB
            query_params = [ano, ano - 1]
            if coug:
                query_params.append(coug)
            query_params.extend([ano - 1, ano])
        else:
            # Query para PostgreSQL
            query = f"""
            WITH receitas_mensais AS (
                SELECT
                    rs.coexercicio,
                    rs.inmes,
                    SUM(CASE 
                        WHEN rs.cocontacontabil >= '621200000' AND rs.cocontacontabil <= '621399999' 
                        THEN rs.saldo_contabil_receita 
                        ELSE 0 
                    END) as receita_liquida
                FROM receita_saldo rs
                WHERE
                    rs.coexercicio IN (:ano, :ano_anterior)
                    AND rs.cocategoriareceita IN ('1', '2', '7')
                    {where_clause}
                GROUP BY rs.coexercicio, rs.inmes
            ),
            meses_acumulados AS (
                SELECT 
                    m1.coexercicio,
                    m1.inmes,
                    SUM(m2.receita_liquida) as receita_acumulada
                FROM receitas_mensais m1
                JOIN receitas_mensais m2 
                    ON m1.coexercicio = m2.coexercicio 
                    AND m2.inmes <= m1.inmes
                GROUP BY m1.coexercicio, m1.inmes
            )
            SELECT
                atual.inmes,
                atual.receita_acumulada as receita_atual,
                COALESCE(anterior.receita_acumulada, 0) as receita_anterior
            FROM meses_acumulados atual
            LEFT JOIN meses_acumulados anterior 
                ON atual.inmes = anterior.inmes 
                AND anterior.coexercicio = :ano_anterior
            WHERE atual.coexercicio = :ano
            ORDER BY atual.inmes
            """
            query_params = params
        
        # Executar query
        resultados = db_manager.execute_query(query, params=query_params)
        
        # Processar resultados
        dados_finais = []
        for row in resultados:
            mes = row['inmes']
            receita_atual = float(row['receita_atual'] or 0)
            receita_anterior = float(row['receita_anterior'] or 0)
            
            if receita_atual != 0 or receita_anterior != 0:
                variacao_absoluta = receita_atual - receita_anterior
                if receita_anterior != 0:
                    variacao_percentual = (variacao_absoluta / abs(receita_anterior)) * 100
                else:
                    variacao_percentual = 100.0 if receita_atual != 0 else 0.0
                
                dados_finais.append({
                    'mes': mes,
                    'nome_mes': self.meses_nomes.get(mes, f'Mês {mes}'),
                    'ano_atual': ano,
                    'ano_anterior': ano - 1,
                    'receita_atual': receita_atual,
                    'receita_anterior': receita_anterior,
                    'variacao_absoluta': variacao_absoluta,
                    'variacao_percentual': variacao_percentual
                })
        
        return dados_finais
    
    def formatar_para_html(self, dados: list) -> dict:
        """Formata os dados para exibição HTML"""
        if not dados:
            return {'meses': [], 'tem_dados': False}
        
        meses_formatados = []
        for item in dados:
            # Determinar classe CSS para variação
            if item['variacao_percentual'] > 0:
                variacao_classe = 'text-success'
                icone_variacao = '↑'
            elif item['variacao_percentual'] < 0:
                variacao_classe = 'text-danger'
                icone_variacao = '↓'
            else:
                variacao_classe = 'text-muted'
                icone_variacao = '→'
            
            meses_formatados.append({
                'nome_mes': item['nome_mes'],
                'label_ate': f"Total até {item['nome_mes']}",
                'ano_atual': item['ano_atual'],
                'ano_anterior': item['ano_anterior'],
                'receita_atual_formatada': self._formatar_moeda(item['receita_atual']),
                'receita_anterior_formatada': self._formatar_moeda(item['receita_anterior']),
                'variacao_formatada': f"{icone_variacao} {abs(item['variacao_percentual']):.2f}%",
                'variacao_classe': variacao_classe,
                'variacao_percentual': item['variacao_percentual'],
                'variacao_absoluta_formatada': self._formatar_moeda(abs(item['variacao_absoluta']))
            })
        
        return {'meses': meses_formatados, 'tem_dados': True}
    
    def gerar_dados_grafico(self, dados: list) -> dict:
        """Gera dados formatados para o gráfico Chart.js"""
        if not dados:
            return {'labels': [], 'datasets': []}
        
        labels = [item['nome_mes'] for item in dados]
        valores_atuais = [item['receita_atual'] for item in dados]
        valores_anteriores = [item['receita_anterior'] for item in dados]
        variacoes = [item['variacao_percentual'] for item in dados]
        
        ano_atual = dados[0]['ano_atual'] if dados else 2025
        ano_anterior = dados[0]['ano_anterior'] if dados else 2024
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': str(ano_anterior),
                    'data': valores_anteriores,
                    'borderColor': '#95a5a6',
                    'backgroundColor': 'rgba(149, 165, 166, 0.1)',
                    'borderWidth': 2,
                    'tension': 0.1,
                    'pointRadius': 4,
                    'pointHoverRadius': 6
                },
                {
                    'label': str(ano_atual),
                    'data': valores_atuais,
                    'borderColor': '#2a5298',
                    'backgroundColor': 'rgba(42, 82, 152, 0.1)',
                    'borderWidth': 3,
                    'tension': 0.1,
                    'pointRadius': 5,
                    'pointHoverRadius': 7
                }
            ],
            'variacoes': variacoes  # Para uso em tooltips customizados
        }
    
    def _formatar_moeda(self, valor: float) -> str:
        """Formata valor para moeda brasileira"""
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# Rotas da API
@comparativo_mensal.route('/api/comparativo-mensal')
def gerar_comparativo_mensal():
    """Endpoint para gerar o comparativo mensal acumulado"""
    try:
        # Obter parâmetros
        ano = request.args.get('ano', type=int)
        coug = request.args.get('coug', '')
        tipo_receita = request.args.get('tipo_receita', 'todas')
        
        if not ano:
            return jsonify({'erro': 'Ano é obrigatório'}), 400
        
        # Gerar comparativo
        comparativo = ComparativoMensalAcumulado()
        dados = comparativo.gerar_comparativo(ano, coug, tipo_receita)
        dados_html = comparativo.formatar_para_html(dados)
        dados_grafico = comparativo.gerar_dados_grafico(dados)
        
        # Obter nome da UG se especificada
        nome_ug = 'Consolidado'
        if coug:
            try:
                query = "SELECT noug FROM dim_unidade_gestora WHERE coug = ?"
                result = db_manager.execute_query(query, [int(coug)])
                if result:
                    nome_ug = result[0]['noug']
            except:
                nome_ug = f"UG {coug}"
        
        return jsonify({
            'dados_html': dados_html,
            'dados_grafico': dados_grafico,
            'dados_brutos': dados,
            'filtros': {
                'ano': ano,
                'coug': coug,
                'nome_ug': nome_ug,
                'tipo_receita': tipo_receita
            },
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        print(f"Erro em gerar_comparativo_mensal: {str(e)}")
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@comparativo_mensal.route('/api/comparativo-mensal/exportar')
def exportar_comparativo_mensal():
    """Endpoint para exportar dados do comparativo mensal"""
    try:
        # Obter parâmetros
        ano = request.args.get('ano', type=int)
        coug = request.args.get('coug', '')
        tipo_receita = request.args.get('tipo_receita', 'todas')
        formato = request.args.get('formato', 'json')
        
        if not ano:
            return jsonify({'erro': 'Ano é obrigatório'}), 400
        
        # Gerar dados
        comparativo = ComparativoMensalAcumulado()
        dados = comparativo.gerar_comparativo(ano, coug, tipo_receita)
        
        if formato == 'csv':
            # Implementar exportação CSV se necessário
            pass
        
        return jsonify({
            'dados': dados,
            'total_meses': len(dados)
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500