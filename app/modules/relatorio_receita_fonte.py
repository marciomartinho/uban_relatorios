"""
Módulo de Relatório Receita/Fonte para Sistema de Balanço de Receitas
Versão 2.0 - Reescrita completa com melhor arquitetura

@author: Sistema de Balanço de Receitas
@version: 2.0.0
@description: Gera relatórios agrupados por código de fonte ou receita com suporte a lançamentos
"""

from typing import Dict, List, Optional, Union, Literal, Any
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass, field
import logging
import traceback
import json
from enum import Enum

# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ================== ENUMS E DATACLASSES ==================

class TipoRelatorio(Enum):
    """Tipos de relatório disponíveis"""
    FONTE = 'fonte'
    RECEITA = 'receita'


class TipoReceita(Enum):
    """Tipos de receita para filtro"""
    TODAS = 'todas'
    CORRENTE = '11'
    CAPITAL = '12'
    CORRENTE_INTRA = '13'
    CAPITAL_INTRA = '14'


@dataclass
class ParametrosRelatorio:
    """Parâmetros para geração de relatório"""
    tipo: TipoRelatorio
    ano: int
    mes: int
    coug: Optional[str] = None
    tipo_receita: Optional[str] = None
    
    def __post_init__(self):
        """Validação e conversão de tipos"""
        if isinstance(self.tipo, str):
            self.tipo = TipoRelatorio(self.tipo)
        
        self.ano = int(self.ano)
        self.mes = int(self.mes)
        
        # Validar ranges
        if not 2000 <= self.ano <= 2100:
            raise ValueError(f"Ano inválido: {self.ano}")
        
        if not 1 <= self.mes <= 12:
            raise ValueError(f"Mês inválido: {self.mes}")


@dataclass
class ParametrosLancamentos:
    """Parâmetros para busca de lançamentos"""
    ano: int
    cofonte: Optional[str] = None
    coalinea: Optional[str] = None
    coug: Optional[str] = None
    mes: Optional[int] = None
    limite: int = 1000
    exportar_excel: bool = False
    
    def __post_init__(self):
        """Validação dos parâmetros"""
        self.ano = int(self.ano)
        
        if self.mes is not None:
            self.mes = int(self.mes) if self.mes != 0 else None
        
        if not self.cofonte and not self.coalinea:
            raise ValueError("Pelo menos cofonte ou coalinea deve ser fornecido")


@dataclass
class ItemRelatorio:
    """Item do relatório (linha da tabela)"""
    id: str
    codigo: str
    descricao: str
    nivel: int
    tipo: str
    previsao_inicial: Decimal = Decimal('0')
    previsao_atualizada: Decimal = Decimal('0')
    receita_atual: Decimal = Decimal('0')
    receita_anterior: Decimal = Decimal('0')
    variacao_absoluta: Decimal = Decimal('0')
    variacao_percentual: float = 0.0
    tem_filhos: bool = False
    pai_id: Optional[str] = None
    itens_secundarios: List['ItemRelatorio'] = field(default_factory=list)
    
    def calcular_variacoes(self):
        """Calcula variações absolutas e percentuais"""
        self.variacao_absoluta = self.receita_atual - self.receita_anterior
        
        if self.receita_anterior != 0:
            self.variacao_percentual = float(
                (self.variacao_absoluta / abs(self.receita_anterior)) * 100
            )
        else:
            self.variacao_percentual = 100.0 if self.variacao_absoluta != 0 else 0.0
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'codigo': self.codigo,
            'descricao': self.descricao,
            'nivel': self.nivel,
            'tipo': self.tipo,
            'previsao_inicial': float(self.previsao_inicial),
            'previsao_atualizada': float(self.previsao_atualizada),
            'receita_atual': float(self.receita_atual),
            'receita_anterior': float(self.receita_anterior),
            'variacao_absoluta': float(self.variacao_absoluta),
            'variacao_percentual': self.variacao_percentual,
            'tem_filhos': self.tem_filhos,
            'pai_id': self.pai_id
        }


@dataclass
class Lancamento:
    """Representa um lançamento contábil"""
    conta_contabil: str
    ug_emitente: str
    ug_contabil: str
    documento: str
    evento: str
    dc: str  # Débito ou Crédito
    data: str
    valor: Decimal
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'conta_contabil': self.conta_contabil,
            'ug_emitente': self.ug_emitente,
            'ug_contabil': self.ug_contabil,
            'documento': self.documento,
            'evento': self.evento,
            'dc': self.dc,
            'data': self.data,
            'valor': float(self.valor)
        }


# ================== CLASSE PRINCIPAL ==================

class RelatorioReceitaFonte:
    """
    Classe principal para geração de relatórios de receita/fonte
    """
    
    def __init__(self, db_manager):
        """
        Inicializa o módulo
        
        Args:
            db_manager: Instância do gerenciador de banco de dados
        """
        self.db_manager = db_manager
        self.estrutura_db = self._verificar_estrutura_db()
        
        # Configurações
        self.config = {
            'limite_lancamentos': 1000,
            'timeout_query': 30,
            'cache_ttl': 300  # 5 minutos
        }
        
        # Cache simples
        self._cache = {}
        self._cache_timestamps = {}
        
        logger.info("Módulo RelatorioReceitaFonte v2.0 inicializado")
    
    # ================== VERIFICAÇÃO DE ESTRUTURA ==================
    
    def _verificar_estrutura_db(self) -> Dict[str, bool]:
        """
        Verifica estrutura disponível no banco de dados
        
        Returns:
            Dicionário com disponibilidade das tabelas
        """
        estrutura = {
            'tem_tabela_receitas': False,
            'tem_tabela_fontes': False,
            'tem_tabela_alineas': False,
            'tem_tabela_lancamentos': False
        }
        
        try:
            # Verificar tabela de receitas
            estrutura['tem_tabela_receitas'] = self._tabela_existe('receita_saldo')
            
            # Verificar tabela de fontes
            estrutura['tem_tabela_fontes'] = self._tabela_existe('dim_fonte')
            
            # Verificar tabela de alíneas
            estrutura['tem_tabela_alineas'] = self._tabela_existe('dim_receita_alinea')
            
            # Verificar tabela de lançamentos (se existir)
            estrutura['tem_tabela_lancamentos'] = self._tabela_existe('lancamentos_receita')
            
            logger.info(f"Estrutura do banco verificada: {estrutura}")
            
        except Exception as e:
            logger.error(f"Erro ao verificar estrutura: {e}")
        
        return estrutura
    
    def _tabela_existe(self, nome_tabela: str) -> bool:
        """Verifica se uma tabela existe"""
        try:
            query = f"SELECT 1 FROM {nome_tabela} LIMIT 1"
            self.db_manager.execute_query(query)
            return True
        except:
            return False
    
    # ================== MÉTODOS PÚBLICOS ==================
    
    def gerar_relatorio(self, **kwargs) -> Dict[str, Any]:
        """
        Gera relatório principal
        
        Args:
            **kwargs: Parâmetros do relatório
            
        Returns:
            Dicionário com dados do relatório
        """
        try:
            # Validar e criar parâmetros
            params = ParametrosRelatorio(**kwargs)
            
            logger.info(f"Gerando relatório: {params}")
            
            # Verificar cache
            cache_key = self._gerar_cache_key('relatorio', params)
            cached = self._obter_do_cache(cache_key)
            if cached:
                logger.info("Retornando dados do cache")
                return cached
            
            # Gerar dados
            dados = self._gerar_dados_relatorio(params)
            
            # Calcular totais
            totais = self._calcular_totais(dados)
            
            # Montar resposta
            resultado = {
                'tipo': params.tipo.value,
                'dados': [item.to_dict() for item in dados],
                'totais': totais,
                'tem_dados': len(dados) > 0,
                'periodo': {
                    'ano': params.ano,
                    'mes': params.mes,
                    'ano_anterior': params.ano - 1
                },
                'filtros': {
                    'coug': params.coug,
                    'tipo_receita': params.tipo_receita
                },
                'estrutura': self.estrutura_db,
                'timestamp': datetime.now().isoformat()
            }
            
            # Armazenar em cache
            self._armazenar_em_cache(cache_key, resultado)
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            logger.error(traceback.format_exc())
            
            return {
                'tipo': kwargs.get('tipo', 'fonte'),
                'dados': [],
                'totais': {},
                'tem_dados': False,
                'erro': str(e)
            }
    
    def buscar_lancamentos(self, **kwargs) -> Dict[str, Any]:
        """
        Busca lançamentos detalhados
        
        Args:
            **kwargs: Parâmetros da busca
            
        Returns:
            Dicionário com lançamentos
        """
        try:
            # Validar parâmetros
            params = ParametrosLancamentos(**kwargs)
            
            logger.info(f"Buscando lançamentos: {params}")
            
            # Verificar se tabela existe
            if not self.estrutura_db.get('tem_tabela_lancamentos'):
                # Se não tem tabela de lançamentos, buscar da receita_saldo
                return self._buscar_lancamentos_receita_saldo(params)
            
            # Buscar lançamentos normalmente
            lancamentos = self._buscar_lancamentos_db(params)
            
            # Calcular totais
            totais = self._calcular_totais_lancamentos(lancamentos)
            
            # Montar resposta
            resultado = {
                'lancamentos': [lanc.to_dict() for lanc in lancamentos],
                'totais': totais,
                'total_registros': len(lancamentos),
                'tem_mais_registros': len(lancamentos) >= params.limite and not params.exportar_excel,
                'filtros': {
                    'ano': params.ano,
                    'mes': params.mes,
                    'cofonte': params.cofonte,
                    'coalinea': params.coalinea,
                    'coug': params.coug
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao buscar lançamentos: {e}")
            logger.error(traceback.format_exc())
            
            return {
                'lancamentos': [],
                'totais': {},
                'total_registros': 0,
                'erro': str(e)
            }
    
    # ================== GERAÇÃO DE DADOS DO RELATÓRIO ==================
    
    def _gerar_dados_relatorio(self, params: ParametrosRelatorio) -> List[ItemRelatorio]:
        """
        Gera dados hierárquicos do relatório
        
        Args:
            params: Parâmetros do relatório
            
        Returns:
            Lista de itens do relatório
        """
        # Determinar campos baseado no tipo
        if params.tipo == TipoRelatorio.FONTE:
            config = {
                'campo_principal': 'cofonte',
                'nome_principal': 'nofonte',
                'tabela_principal': 'dim_fonte',
                'campo_secundario': 'coalinea',
                'nome_secundario': 'noalinea',
                'tabela_secundaria': 'dim_receita_alinea'
            }
        else:
            config = {
                'campo_principal': 'coalinea',
                'nome_principal': 'noalinea',
                'tabela_principal': 'dim_receita_alinea',
                'campo_secundario': 'cofonte',
                'nome_secundario': 'nofonte',
                'tabela_secundaria': 'dim_fonte'
            }
        
        # Construir query
        query = self._construir_query_relatorio(params, config)
        
        # Executar query
        resultados = self.db_manager.execute_query(query['sql'], query['params'])
        
        # Processar resultados
        return self._processar_resultados_relatorio(resultados, params.tipo, config)
    
    def _construir_query_relatorio(self, params: ParametrosRelatorio, config: Dict) -> Dict:
        """
        Constrói a query SQL para o relatório
        
        Args:
            params: Parâmetros do relatório
            config: Configuração de campos
            
        Returns:
            Dicionário com SQL e parâmetros
        """
        # Preparar filtros
        filtros = []
        parametros = []
        
        if params.coug:
            filtros.append("rs.coug = ?")
            parametros.append(params.coug)
        
        # Filtro por tipo de receita
        if params.tipo_receita and params.tipo_receita != 'todas':
            mapa_tipos = {
                '11': ['11', '71'],  # Receitas Correntes
                '12': ['12', '72'],  # Receitas de Capital
                '13': ['13', '73'],  # Receitas Correntes Intra
                '14': ['14', '74'],  # Receitas de Capital Intra
                '15': ['15', '75'],  # Receitas Correntes - Fundos
                '16': ['16', '76'],  # Receitas de Capital - Fundos
                '17': ['17', '77'],  # Receitas Correntes - Estados
                '19': ['19', '79'],  # Outras Receitas Correntes
                '21': ['21'],        # Receitas Intra-Orçamentárias
                '22': ['22'],        # Receitas Intra-Orçamentárias Correntes
                '23': ['23'],        # Receitas Intra-Orçamentárias de Capital
                '24': ['24']         # Transferências Intra-Orçamentárias
            }
            
            if params.tipo_receita in mapa_tipos:
                fontes = mapa_tipos[params.tipo_receita]
                placeholders = ','.join(['?' for _ in fontes])
                filtros.append(f"SUBSTRING(rs.cofonte, 1, 2) IN ({placeholders})")
                parametros.extend(fontes)
        
        where_clause = f" AND {' AND '.join(filtros)}" if filtros else ""
        
        # Construir SQL completo
        sql = f"""
        WITH dados_agregados AS (
            -- Agregar dados por fonte/alínea e contas
            SELECT
                rs.{config['campo_principal']} as campo_principal,
                rs.{config['campo_secundario']} as campo_secundario,
                rs.coexercicio,
                rs.inmes,
                
                -- Previsão Inicial (521100000 - 521199999)
                SUM(CASE 
                    WHEN rs.cocontacontabil >= '521100000' 
                     AND rs.cocontacontabil <= '521199999' 
                    THEN rs.saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_inicial,
                
                -- Previsão Atualizada (521100000 - 521299999)
                SUM(CASE 
                    WHEN rs.cocontacontabil >= '521100000' 
                     AND rs.cocontacontabil <= '521299999' 
                    THEN rs.saldo_contabil_receita 
                    ELSE 0 
                END) as previsao_atualizada,
                
                -- Receita Realizada (621200000 - 621399999)
                SUM(CASE 
                    WHEN rs.cocontacontabil >= '621200000' 
                     AND rs.cocontacontabil <= '621399999' 
                    THEN rs.saldo_contabil_receita 
                    ELSE 0 
                END) as receita_liquida
                
            FROM receita_saldo rs
            WHERE 
                rs.{config['campo_principal']} IS NOT NULL
                AND rs.cocategoriareceita IN ('1', '2', '7')
                {where_clause}
            GROUP BY 1, 2, 3, 4
        ),
        dados_sumarizados AS (
            -- Sumarizar por período
            SELECT
                campo_principal,
                campo_secundario,
                
                -- Ano atual
                SUM(CASE 
                    WHEN coexercicio = ? 
                    THEN previsao_inicial 
                    ELSE 0 
                END) as previsao_inicial,
                
                SUM(CASE 
                    WHEN coexercicio = ? 
                    THEN previsao_atualizada 
                    ELSE 0 
                END) as previsao_atualizada,
                
                SUM(CASE 
                    WHEN coexercicio = ? AND inmes <= ? 
                    THEN receita_liquida 
                    ELSE 0 
                END) as receita_atual,
                
                -- Ano anterior
                SUM(CASE 
                    WHEN coexercicio = ? AND inmes <= ? 
                    THEN receita_liquida 
                    ELSE 0 
                END) as receita_anterior
                
            FROM dados_agregados
            WHERE coexercicio IN (?, ?)
            GROUP BY 1, 2
        ),
        totais_principais AS (
            -- Calcular totais por item principal
            SELECT
                campo_principal,
                SUM(previsao_inicial) as total_previsao_inicial,
                SUM(previsao_atualizada) as total_previsao_atualizada,
                SUM(receita_atual) as total_receita_atual,
                SUM(receita_anterior) as total_receita_anterior
            FROM dados_sumarizados
            GROUP BY 1
        )
        -- Query final com joins para nomes
        SELECT 
            ds.campo_principal,
            COALESCE(p.{config['nome_principal']}, 
                     'Código ' || ds.campo_principal) as nome_principal,
            ds.campo_secundario,
            COALESCE(s.{config['nome_secundario']}, 
                     'Código ' || ds.campo_secundario) as nome_secundario,
            ds.previsao_inicial,
            ds.previsao_atualizada,
            ds.receita_atual,
            ds.receita_anterior,
            tp.total_previsao_inicial,
            tp.total_previsao_atualizada,
            tp.total_receita_atual,
            tp.total_receita_anterior
        FROM dados_sumarizados ds
        JOIN totais_principais tp ON ds.campo_principal = tp.campo_principal
        LEFT JOIN {config['tabela_principal']} p 
            ON CAST(ds.campo_principal AS VARCHAR) = CAST(p.{config['campo_principal']} AS VARCHAR)
        LEFT JOIN {config['tabela_secundaria']} s 
            ON CAST(ds.campo_secundario AS VARCHAR) = CAST(s.{config['campo_secundario']} AS VARCHAR)
        WHERE 
            -- Filtrar apenas registros com valores
            (ABS(COALESCE(ds.previsao_inicial, 0)) + 
             ABS(COALESCE(ds.previsao_atualizada, 0)) + 
             ABS(COALESCE(ds.receita_atual, 0)) + 
             ABS(COALESCE(ds.receita_anterior, 0))) > 0.01
        ORDER BY 
            tp.total_receita_atual DESC, 
            ds.campo_principal, 
            ds.receita_atual DESC
        """
        
        # Adicionar parâmetros de período
        parametros.extend([
            params.ano,      # previsao_inicial
            params.ano,      # previsao_atualizada
            params.ano,      # receita_atual - ano
            params.mes,      # receita_atual - mes
            params.ano - 1,  # receita_anterior - ano
            params.mes,      # receita_anterior - mes
            params.ano,      # WHERE coexercicio IN
            params.ano - 1   # WHERE coexercicio IN
        ])
        
        return {
            'sql': sql,
            'params': parametros
        }
    
    def _processar_resultados_relatorio(
        self, 
        resultados: List, 
        tipo: TipoRelatorio,
        config: Dict
    ) -> List[ItemRelatorio]:
        """
        Processa resultados da query em estrutura hierárquica
        
        Args:
            resultados: Resultados da query
            tipo: Tipo do relatório
            config: Configuração de campos
            
        Returns:
            Lista de itens do relatório
        """
        dados_finais = []
        grupos = {}
        
        for row in resultados:
            # Obter código principal
            codigo_principal = str(row.get('campo_principal', ''))
            if not codigo_principal:
                continue
            
            # Criar grupo principal se não existir
            if codigo_principal not in grupos:
                item_principal = ItemRelatorio(
                    id=f'{tipo.value}-{codigo_principal}',
                    codigo=codigo_principal,
                    descricao=row.get('nome_principal', f'Código {codigo_principal}'),
                    nivel=0,
                    tipo='principal',
                    previsao_inicial=Decimal(str(row.get('total_previsao_inicial', 0) or 0)),
                    previsao_atualizada=Decimal(str(row.get('total_previsao_atualizada', 0) or 0)),
                    receita_atual=Decimal(str(row.get('total_receita_atual', 0) or 0)),
                    receita_anterior=Decimal(str(row.get('total_receita_anterior', 0) or 0)),
                    tem_filhos=False
                )
                grupos[codigo_principal] = item_principal
            
            # Adicionar item secundário se existir
            codigo_secundario = row.get('campo_secundario')
            if codigo_secundario:
                grupos[codigo_principal].tem_filhos = True
                
                item_secundario = ItemRelatorio(
                    id=f'{tipo.value}-{codigo_principal}-{codigo_secundario}',
                    codigo=str(codigo_secundario),
                    descricao=row.get('nome_secundario', f'Código {codigo_secundario}'),
                    nivel=1,
                    tipo='secundario',
                    pai_id=f'{tipo.value}-{codigo_principal}',
                    previsao_inicial=Decimal(str(row.get('previsao_inicial', 0) or 0)),
                    previsao_atualizada=Decimal(str(row.get('previsao_atualizada', 0) or 0)),
                    receita_atual=Decimal(str(row.get('receita_atual', 0) or 0)),
                    receita_anterior=Decimal(str(row.get('receita_anterior', 0) or 0)),
                    tem_filhos=False
                )
                
                # Calcular variações
                item_secundario.calcular_variacoes()
                grupos[codigo_principal].itens_secundarios.append(item_secundario)
        
        # Montar lista final
        for grupo in grupos.values():
            # Calcular variações do grupo
            grupo.calcular_variacoes()
            dados_finais.append(grupo)
            
            # Adicionar itens secundários
            for item_sec in grupo.itens_secundarios:
                dados_finais.append(item_sec)
        
        return dados_finais
    
    # ================== BUSCA DE LANÇAMENTOS ==================
    
    def _buscar_lancamentos_receita_saldo(
        self, 
        params: ParametrosLancamentos
    ) -> List[Lancamento]:
        """
        Busca lançamentos da tabela receita_saldo
        
        Args:
            params: Parâmetros da busca
            
        Returns:
            Lista de lançamentos
        """
        # Construir filtros
        filtros = ["rs.coexercicio = ?"]
        parametros = [params.ano]
        
        # Filtro por mês (se não for 0 ou None, busca apenas o mês específico)
        if params.mes and params.mes > 0:
            filtros.append("rs.inmes = ?")
            parametros.append(params.mes)
        # Se mes=0 ou None, busca o ano todo (não adiciona filtro de mês)
        
        # Filtro por fonte
        if params.cofonte:
            filtros.append("rs.cofonte = ?")
            parametros.append(params.cofonte)
        
        # Filtro por alínea
        if params.coalinea:
            filtros.append("rs.coalinea = ?")
            parametros.append(params.coalinea)
        
        # Filtro por UG
        if params.coug:
            filtros.append("rs.coug = ?")
            parametros.append(params.coug)
        
        where_clause = " AND ".join(filtros)
        
        # Query para buscar lançamentos
        sql = f"""
        SELECT
            rs.cocontacontabil as conta_contabil,
            rs.coug as ug_emitente,
            rs.coug as ug_contabil,
            rs.coalinea || '/' || rs.cofonte as documento,
            rs.cocategoriareceita as evento,
            CASE 
                WHEN rs.saldo_contabil_receita >= 0 THEN 'C'
                ELSE 'D'
            END as dc,
            CAST(rs.coexercicio AS VARCHAR) || '-' || 
            LPAD(CAST(rs.inmes AS VARCHAR), 2, '0') || '-01' as data,
            ABS(rs.saldo_contabil_receita) as valor,
            rs.saldo_contabil_receita as valor_original
        FROM receita_saldo rs
        WHERE {where_clause}
            AND rs.saldo_contabil_receita != 0
            AND rs.cocontacontabil >= '621200000'
            AND rs.cocontacontabil <= '621399999'
        ORDER BY rs.inmes, rs.cocontacontabil
        """
        
        # Adicionar limite se não for exportação
        if not params.exportar_excel:
            sql += f" LIMIT {params.limite}"
        
        # Executar query
        resultados = self.db_manager.execute_query(sql, parametros)
        
        # Converter para objetos Lancamento
        lancamentos = []
        for row in resultados:
            lancamento = Lancamento(
                conta_contabil=row.get('conta_contabil', ''),
                ug_emitente=row.get('ug_emitente', ''),
                ug_contabil=row.get('ug_contabil', ''),
                documento=row.get('documento', ''),
                evento=row.get('evento', ''),
                dc=row.get('dc', ''),
                data=row.get('data', ''),
                valor=Decimal(str(row.get('valor', 0)))
            )
            lancamentos.append(lancamento)
        
        return lancamentos
    
    def _buscar_lancamentos_db(self, params: ParametrosLancamentos) -> List[Lancamento]:
        """
        Busca lançamentos da tabela específica de lançamentos (se existir)
        
        Args:
            params: Parâmetros da busca
            
        Returns:
            Lista de lançamentos
        """
        # Se não tem tabela de lançamentos, usar receita_saldo
        if not self.estrutura_db.get('tem_tabela_lancamentos'):
            return self._buscar_lancamentos_receita_saldo(params)
        
        # Construir query para tabela de lançamentos
        filtros = ["l.ano = ?"]
        parametros = [params.ano]
        
        if params.mes and params.mes > 0:
            filtros.append("l.mes = ?")
            parametros.append(params.mes)
        
        if params.cofonte:
            filtros.append("l.cofonte = ?")
            parametros.append(params.cofonte)
        
        if params.coalinea:
            filtros.append("l.coalinea = ?")
            parametros.append(params.coalinea)
        
        if params.coug:
            filtros.append("l.coug = ?")
            parametros.append(params.coug)
        
        where_clause = " AND ".join(filtros)
        
        sql = f"""
        SELECT
            l.conta_contabil,
            l.ug_emitente,
            l.ug_contabil,
            l.documento,
            l.evento,
            l.dc,
            l.data,
            l.valor
        FROM lancamentos_receita l
        WHERE {where_clause}
        ORDER BY l.data, l.conta_contabil
        """
        
        if not params.exportar_excel:
            sql += f" LIMIT {params.limite}"
        
        resultados = self.db_manager.execute_query(sql, parametros)
        
        lancamentos = []
        for row in resultados:
            lancamento = Lancamento(
                conta_contabil=row.get('conta_contabil', ''),
                ug_emitente=row.get('ug_emitente', ''),
                ug_contabil=row.get('ug_contabil', ''),
                documento=row.get('documento', ''),
                evento=row.get('evento', ''),
                dc=row.get('dc', ''),
                data=row.get('data', ''),
                valor=Decimal(str(row.get('valor', 0)))
            )
            lancamentos.append(lancamento)
        
        return lancamentos
    
    # ================== CÁLCULO DE TOTAIS ==================
    
    def _calcular_totais(self, dados: List[ItemRelatorio]) -> Dict:
        """
        Calcula totais gerais do relatório
        
        Args:
            dados: Lista de itens do relatório
            
        Returns:
            Dicionário com totais
        """
        totais = {
            'previsao_inicial': Decimal('0'),
            'previsao_atualizada': Decimal('0'),
            'receita_atual': Decimal('0'),
            'receita_anterior': Decimal('0'),
            'variacao_absoluta': Decimal('0'),
            'variacao_percentual': 0.0
        }
        
        # Somar apenas itens principais (nível 0)
        for item in dados:
            if item.nivel == 0:
                totais['previsao_inicial'] += item.previsao_inicial
                totais['previsao_atualizada'] += item.previsao_atualizada
                totais['receita_atual'] += item.receita_atual
                totais['receita_anterior'] += item.receita_anterior
        
        # Calcular variações
        totais['variacao_absoluta'] = totais['receita_atual'] - totais['receita_anterior']
        
        if totais['receita_anterior'] != 0:
            totais['variacao_percentual'] = float(
                (totais['variacao_absoluta'] / abs(totais['receita_anterior'])) * 100
            )
        else:
            totais['variacao_percentual'] = 100.0 if totais['variacao_absoluta'] != 0 else 0.0
        
        # Converter Decimals para float
        return {
            'previsao_inicial': float(totais['previsao_inicial']),
            'previsao_atualizada': float(totais['previsao_atualizada']),
            'receita_atual': float(totais['receita_atual']),
            'receita_anterior': float(totais['receita_anterior']),
            'variacao_absoluta': float(totais['variacao_absoluta']),
            'variacao_percentual': totais['variacao_percentual']
        }
    
    def _calcular_totais_lancamentos(self, lancamentos: List[Lancamento]) -> Dict:
        """
        Calcula totais dos lançamentos
        
        Args:
            lancamentos: Lista de lançamentos
            
        Returns:
            Dicionário com totais
        """
        total_debito = Decimal('0')
        total_credito = Decimal('0')
        
        for lanc in lancamentos:
            if lanc.dc == 'D':
                total_debito += lanc.valor
            else:
                total_credito += lanc.valor
        
        return {
            'debito': float(total_debito),
            'credito': float(total_credito),
            'saldo': float(total_credito - total_debito)
        }
    
    # ================== CACHE ==================
    
    def _gerar_cache_key(self, tipo: str, params: Any) -> str:
        """Gera chave única para cache"""
        import hashlib
        
        if hasattr(params, '__dict__'):
            params_dict = params.__dict__
        else:
            params_dict = params
        
        params_str = json.dumps(params_dict, sort_keys=True, default=str)
        hash_obj = hashlib.md5(params_str.encode())
        return f"{tipo}_{hash_obj.hexdigest()}"
    
    def _obter_do_cache(self, key: str) -> Optional[Any]:
        """Obtém valor do cache se ainda válido"""
        if key not in self._cache:
            return None
        
        # Verificar TTL
        timestamp = self._cache_timestamps.get(key, 0)
        if (datetime.now().timestamp() - timestamp) > self.config['cache_ttl']:
            del self._cache[key]
            del self._cache_timestamps[key]
            return None
        
        return self._cache[key]
    
    def _armazenar_em_cache(self, key: str, value: Any):
        """Armazena valor no cache"""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now().timestamp()
    
    def limpar_cache(self):
        """Limpa todo o cache"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Cache limpo")


# ================== FUNÇÕES AUXILIARES ==================

def criar_instancia(db_manager) -> RelatorioReceitaFonte:
    """
    Cria instância do módulo
    
    Args:
        db_manager: Gerenciador de banco de dados
        
    Returns:
        Instância de RelatorioReceitaFonte
    """
    return RelatorioReceitaFonte(db_manager)


# ================== EXEMPLO DE USO ==================

if __name__ == "__main__":
    # Exemplo de uso
    from app.db_manager import db_manager
    
    # Criar instância
    relatorio = RelatorioReceitaFonte(db_manager)
    
    # Gerar relatório por fonte
    resultado = relatorio.gerar_relatorio(
        tipo='fonte',
        ano=2025,
        mes=6,
        coug=None,
        tipo_receita='todas'
    )
    
    print(f"Total de registros: {len(resultado['dados'])}")
    print(f"Totais: {resultado['totais']}")
    
    # Buscar lançamentos
    lancamentos = relatorio.buscar_lancamentos(
        ano=2025,
        cofonte='121020590',
        coalinea='132101'
    )
    
    print(f"Total de lançamentos: {lancamentos['total_registros']}")