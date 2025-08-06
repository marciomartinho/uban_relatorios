# app/modules/relatorio_receita_fonte.py
"""
Módulo para gerar relatórios agrupados por Código de Receita ou Código de Fonte
Permite visualização hierárquica com expansão/colapso
Adaptado para trabalhar com a estrutura DuckDB do sistema
"""
from typing import List, Dict, Optional, Literal
from app.db_manager import db_manager
import traceback

# ===== ARQUIVO DE ATUALIZAÇÃO DO app/__init__.py =====
# Adicione as seguintes linhas no arquivo app/__init__.py após os outros blueprints:
#
# from app.routes.relatorio_receita_fonte import relatorio_receita_fonte
# app.register_blueprint(relatorio_receita_fonte, url_prefix='/relatorio-receita-fonte')
#
# ===== FIM DAS INSTRUÇÕES DE ATUALIZAÇÃO =====


class RelatorioReceitaFonte:
    """Classe para gerar relatórios agrupados por receita ou fonte"""

    def __init__(self):
        self.db_manager = db_manager
        self.estrutura = self._verificar_estrutura()

    def _verificar_estrutura(self):
        """Verifica estrutura disponível no banco"""
        tem_tabela_receitas = False
        tem_tabela_fontes = False
        tem_tabela_alineas = False
        
        try:
            # Verificar tabela de receitas
            try:
                query = "SELECT 1 FROM receita_saldo LIMIT 1"
                result = self.db_manager.execute_query(query)
                tem_tabela_receitas = True
                print(f"DEBUG - Tabela receita_saldo encontrada")
            except:
                tem_tabela_receitas = False
            
            # Verificar tabela de fontes (dim_receita_origem)
            try:
                query = "SELECT 1 FROM dim_receita_origem LIMIT 1"
                result = self.db_manager.execute_query(query)
                tem_tabela_fontes = True
                print(f"DEBUG - Tabela dim_receita_origem encontrada")
            except:
                tem_tabela_fontes = False
            
            # Verificar tabela de alíneas
            try:
                query = "SELECT 1 FROM dim_receita_alinea LIMIT 1"
                result = self.db_manager.execute_query(query)
                tem_tabela_alineas = True
                print(f"DEBUG - Tabela dim_receita_alinea encontrada")
            except:
                tem_tabela_alineas = False
                        
        except Exception as e:
            print(f"Erro ao verificar estrutura: {e}")
            
        resultado = {
            'tem_tabela_receitas': tem_tabela_receitas,
            'tem_tabela_fontes': tem_tabela_fontes,
            'tem_tabela_alineas': tem_tabela_alineas
        }
        print(f"DEBUG - Estrutura verificada: {resultado}")
        return resultado

    def gerar_relatorio(self, tipo: Literal['receita', 'fonte'],
                       ano: int, mes: int,
                       coug: Optional[str] = None) -> Dict:
        """
        Gera o relatório principal
        
        Args:
            tipo: 'receita' para agrupar por alínea, 'fonte' para agrupar por fonte
            ano: Ano do exercício
            mes: Mês de referência
            coug: Código da UG (opcional)
        
        Returns:
            Dict com dados do relatório
        """
        print(f"DEBUG - gerar_relatorio: tipo={tipo}, ano={ano}, mes={mes}, coug={coug}")
        
        try:
            dados = self._gerar_dados_relatorio(tipo, ano, mes, coug)
            totais = self._calcular_totais(dados)
            
            return {
                'tipo': tipo,
                'dados': dados,
                'totais': totais,
                'tem_dados': len(dados) > 0,
                'coug_selecionada': coug,
                'estrutura': self.estrutura,
                'periodo': {
                    'ano': ano,
                    'mes': mes,
                    'ano_anterior': ano - 1
                }
            }
            
        except Exception as e:
            print(f"Erro ao gerar relatório: {e}")
            traceback.print_exc()
            return {
                'tipo': tipo,
                'dados': [],
                'totais': {},
                'tem_dados': False,
                'erro': str(e)
            }

    def _gerar_dados_relatorio(self, tipo: Literal['receita', 'fonte'],
                               ano: int, mes: int,
                               coug: Optional[str] = None) -> List[Dict]:
        """Gera os dados do relatório com hierarquia"""
        
        # Preparar filtros
        filtros = []
        params = []
        
        if coug:
            filtros.append("rs.coug = ?")
            params.append(coug)
        
        where_clause = " AND " + " AND ".join(filtros) if filtros else ""
        
        # Define campos baseado no tipo
        if tipo == 'receita':
            campo_principal = 'coalinea'
            nome_principal = 'noalinea'
            tabela_principal = 'dim_receita_alinea'
            campo_secundario = 'cofontereceita'
            nome_secundario = 'nofontereceita'
            tabela_secundaria = 'dim_receita_origem'
        else:  # tipo == 'fonte'
            campo_principal = 'cofontereceita'
            nome_principal = 'nofontereceita'
            tabela_principal = 'dim_receita_origem'
            campo_secundario = 'coalinea'
            nome_secundario = 'noalinea'
            tabela_secundaria = 'dim_receita_alinea'
        
        # Query principal
        query = f"""
        WITH dados_agregados AS (
            SELECT
                rs.{campo_principal},
                rs.{campo_secundario},
                rs.coexercicio,
                rs.inmes,
                SUM(CASE 
                    WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521199999' 
                    THEN rs.saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_inicial,
                SUM(CASE 
                    WHEN rs.cocontacontabil >= '521100000' AND rs.cocontacontabil <= '521299999' 
                    THEN rs.saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_atualizada,
                SUM(CASE 
                    WHEN rs.cocontacontabil >= '621200000' AND rs.cocontacontabil <= '621399999' 
                    THEN rs.saldo_contabil_receita 
                    ELSE 0 
                END) as receita_liquida
            FROM receita_saldo rs
            WHERE 
                rs.{campo_principal} IS NOT NULL 
                AND rs.cocategoriareceita IN ('1', '2', '7')
                {where_clause}
            GROUP BY 1, 2, 3, 4
        ),
        dados_sumarizados AS (
            SELECT
                {campo_principal},
                {campo_secundario},
                SUM(CASE WHEN coexercicio = ? THEN previsao_inicial ELSE 0 END) as previsao_inicial,
                SUM(CASE WHEN coexercicio = ? THEN previsao_atualizada ELSE 0 END) as previsao_atualizada,
                SUM(CASE WHEN coexercicio = ? AND inmes <= ? THEN receita_liquida ELSE 0 END) as receita_atual,
                SUM(CASE WHEN coexercicio = ? AND inmes <= ? THEN receita_liquida ELSE 0 END) as receita_anterior
            FROM dados_agregados
            WHERE coexercicio IN (?, ?)
            GROUP BY 1, 2
        ),
        totais_principais AS (
            SELECT
                {campo_principal},
                SUM(previsao_inicial) as total_previsao_inicial,
                SUM(previsao_atualizada) as total_previsao_atualizada,
                SUM(receita_atual) as total_receita_atual,
                SUM(receita_anterior) as total_receita_anterior
            FROM dados_sumarizados
            GROUP BY 1
        )
        SELECT 
            ds.{campo_principal},
            p.{nome_principal} as nome_principal,
            ds.{campo_secundario},
            s.{nome_secundario} as nome_secundario,
            ds.previsao_inicial,
            ds.previsao_atualizada,
            ds.receita_atual,
            ds.receita_anterior,
            tp.total_previsao_inicial,
            tp.total_previsao_atualizada,
            tp.total_receita_atual,
            tp.total_receita_anterior
        FROM dados_sumarizados ds
        JOIN totais_principais tp ON ds.{campo_principal} = tp.{campo_principal}
        LEFT JOIN {tabela_principal} p ON CAST(ds.{campo_principal} AS VARCHAR) = CAST(p.{campo_principal} AS VARCHAR)
        LEFT JOIN {tabela_secundaria} s ON CAST(ds.{campo_secundario} AS VARCHAR) = CAST(s.{campo_secundario} AS VARCHAR)
        WHERE (ABS(COALESCE(ds.previsao_inicial, 0)) + ABS(COALESCE(ds.previsao_atualizada, 0)) + 
               ABS(COALESCE(ds.receita_atual, 0)) + ABS(COALESCE(ds.receita_anterior, 0))) > 0.01
        ORDER BY tp.total_receita_atual DESC, ds.{campo_principal}, ds.receita_atual DESC
        """
        
        # Adicionar parâmetros da query
        params.extend([ano, ano, ano, mes, ano - 1, mes, ano, ano - 1])
        
        # Executar query
        resultados = self.db_manager.execute_query(query, params)
        
        # Processar resultados em estrutura hierárquica
        dados_finais = []
        grupos = {}
        
        for row in resultados:
            codigo_principal = str(row.get(campo_principal, ''))
            if not codigo_principal:
                continue
            
            # Criar grupo principal se não existir
            if codigo_principal not in grupos:
                grupos[codigo_principal] = {
                    'id': f'{tipo}-{codigo_principal}',
                    'codigo': codigo_principal,
                    'descricao': row.get('nome_principal', f'Código {codigo_principal}'),
                    'tipo': 'principal',
                    'nivel': 0,
                    'previsao_inicial': float(row.get('total_previsao_inicial', 0) or 0),
                    'previsao_atualizada': float(row.get('total_previsao_atualizada', 0) or 0),
                    'receita_atual': float(row.get('total_receita_atual', 0) or 0),
                    'receita_anterior': float(row.get('total_receita_anterior', 0) or 0),
                    'tem_filhos': False,
                    'expandido': False,
                    'itens_secundarios': []
                }
            
            # Adicionar item secundário
            codigo_secundario = row.get(campo_secundario)
            if codigo_secundario:
                grupos[codigo_principal]['tem_filhos'] = True
                
                item_secundario = {
                    'id': f'{tipo}-{codigo_principal}-{codigo_secundario}',
                    'codigo': str(codigo_secundario),
                    'descricao': row.get('nome_secundario', f'Código {codigo_secundario}'),
                    'tipo': 'secundario',
                    'nivel': 1,
                    'pai_id': f'{tipo}-{codigo_principal}',
                    'previsao_inicial': float(row.get('previsao_inicial', 0) or 0),
                    'previsao_atualizada': float(row.get('previsao_atualizada', 0) or 0),
                    'receita_atual': float(row.get('receita_atual', 0) or 0),
                    'receita_anterior': float(row.get('receita_anterior', 0) or 0),
                    'tem_filhos': False
                }
                grupos[codigo_principal]['itens_secundarios'].append(item_secundario)
        
        # Montar lista final e calcular variações
        for grupo in grupos.values():
            self._calcular_variacoes(grupo)
            dados_finais.append(grupo)
            
            for item in grupo['itens_secundarios']:
                self._calcular_variacoes(item)
                dados_finais.append(item)
        
        print(f"DEBUG - Total de resultados: {len(dados_finais)}")
        return dados_finais

    def _calcular_variacoes(self, item: Dict) -> None:
        """Calcula variações absolutas e percentuais"""
        receita_atual = item.get('receita_atual', 0) or 0
        receita_anterior = item.get('receita_anterior', 0) or 0
        
        item['variacao_absoluta'] = receita_atual - receita_anterior
        
        if receita_anterior != 0:
            item['variacao_percentual'] = (item['variacao_absoluta'] / abs(receita_anterior)) * 100
        else:
            item['variacao_percentual'] = 100.0 if item['variacao_absoluta'] != 0 else 0.0

    def _calcular_totais(self, dados: List[Dict]) -> Dict:
        """Calcula totais gerais do relatório"""
        totais = {
            'previsao_inicial': 0,
            'previsao_atualizada': 0,
            'receita_atual': 0,
            'receita_anterior': 0,
            'variacao_absoluta': 0,
            'variacao_percentual': 0
        }
        
        for item in dados:
            if item.get('nivel') == 0:  # Apenas itens principais
                totais['previsao_inicial'] += item.get('previsao_inicial', 0)
                totais['previsao_atualizada'] += item.get('previsao_atualizada', 0)
                totais['receita_atual'] += item.get('receita_atual', 0)
                totais['receita_anterior'] += item.get('receita_anterior', 0)
        
        totais['variacao_absoluta'] = totais['receita_atual'] - totais['receita_anterior']
        
        if totais['receita_anterior'] != 0:
            totais['variacao_percentual'] = (totais['variacao_absoluta'] / abs(totais['receita_anterior'])) * 100
        else:
            totais['variacao_percentual'] = 100.0 if totais['variacao_absoluta'] != 0 else 0.0
        
        return totais