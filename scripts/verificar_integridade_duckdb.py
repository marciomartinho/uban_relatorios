#!/usr/bin/env python3
"""
Script para verificar integridade referencial entre tabelas fato e dimensão
Identifica valores órfãos e problemas de relacionamento
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
from pathlib import Path
from datetime import datetime
import pandas as pd

class VerificadorIntegridade:
    """Classe para verificar integridade referencial no DuckDB"""
    
    def __init__(self):
        self.db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
        
        # Mapeamento de relacionamentos fato -> dimensão
        self.relacionamentos = {
            # Relacionamentos comuns a todas as tabelas fato
            'comum': {
                'coug': 'dim_unidade_gestora',
                'cogestao': 'dim_gestao',
                'coevento': 'dim_evento',
                'cocontacontabil': 'dim_conta_contabil',
            },
            
            # Relacionamentos específicos de despesa
            'despesa': {
                'cofuncao': 'dim_funcao',
                'cosubfuncao': 'dim_subfuncao',
                'coprograma': 'dim_programa',
                'coprojeto': 'dim_projeto',
                'cosubtitulo': 'dim_subtitulo',
                'cofonte': 'dim_fonte',
                'incategoria': 'dim_categoria_despesa',
                'cogrupo': 'dim_grupo_despesa',
                'comodalidade': 'dim_modalidade',
                'coelemento': 'dim_elemento',
            },
            
            # Relacionamentos específicos de receita
            'receita': {
                'coclasseorc': 'dim_classificacao_orcamentaria',
                'cocategoriareceita': 'dim_receita_categoria',
                'cofontereceita': 'dim_receita_origem',
                'cosubfontereceita': 'dim_receita_especie',
                'corubrica': 'dim_receita_especificacao',
                'coalinea': 'dim_receita_alinea',
            }
        }
        
        self.tabelas_fato = [
            'despesa_lancamento',
            'despesa_saldo',
            'receita_lancamento',
            'receita_saldo'
        ]
    
    def verificar_tabela_existe(self, conn, tabela):
        """Verifica se uma tabela existe no banco"""
        query = f"""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_name = '{tabela}'
        """
        return conn.execute(query).fetchone()[0] > 0
    
    def verificar_coluna_existe(self, conn, tabela, coluna):
        """Verifica se uma coluna existe em uma tabela"""
        query = f"""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = '{tabela}' AND column_name = '{coluna}'
        """
        return conn.execute(query).fetchone()[0] > 0
    
    def verificar_integridade_relacionamento(self, conn, tabela_fato, coluna_fk, tabela_dim):
        """Verifica integridade de um relacionamento específico"""
        resultado = {
            'tabela_fato': tabela_fato,
            'coluna_fk': coluna_fk,
            'tabela_dimensao': tabela_dim,
            'status': 'OK',
            'total_fato': 0,
            'valores_distintos': 0,
            'valores_orfaos': 0,
            'exemplos_orfaos': []
        }
        
        try:
            # Verificar se a tabela dimensão existe
            if not self.verificar_tabela_existe(conn, tabela_dim):
                resultado['status'] = 'TABELA_DIM_NAO_EXISTE'
                return resultado
            
            # Verificar se a coluna existe na tabela fato
            if not self.verificar_coluna_existe(conn, tabela_fato, coluna_fk):
                resultado['status'] = 'COLUNA_FK_NAO_EXISTE'
                return resultado
            
            # Contar total de registros e valores distintos na tabela fato
            query_totais = f"""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT {coluna_fk}) as distintos
            FROM {tabela_fato}
            WHERE {coluna_fk} IS NOT NULL
            """
            totais = conn.execute(query_totais).fetchone()
            resultado['total_fato'] = totais[0]
            resultado['valores_distintos'] = totais[1]
            
            # Verificar valores órfãos (que não existem na dimensão)
            query_orfaos = f"""
            SELECT DISTINCT f.{coluna_fk}
            FROM {tabela_fato} f
            LEFT JOIN {tabela_dim} d ON f.{coluna_fk} = d.{coluna_fk}
            WHERE f.{coluna_fk} IS NOT NULL
            AND d.{coluna_fk} IS NULL
            """
            
            orfaos = conn.execute(query_orfaos).fetchall()
            resultado['valores_orfaos'] = len(orfaos)
            
            # Pegar alguns exemplos de valores órfãos
            if orfaos:
                resultado['exemplos_orfaos'] = [str(o[0]) for o in orfaos[:5]]
                resultado['status'] = 'PROBLEMAS_ENCONTRADOS'
            
        except Exception as e:
            resultado['status'] = 'ERRO'
            resultado['erro'] = str(e)
        
        return resultado
    
    def executar_verificacao(self):
        """Executa verificação completa de integridade"""
        print("=" * 80)
        print("VERIFICAÇÃO DE INTEGRIDADE REFERENCIAL - DUCKDB")
        print("=" * 80)
        print(f"Banco de dados: {self.db_path}")
        print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        
        if not self.db_path.exists():
            print(f"❌ ERRO: Banco de dados não encontrado: {self.db_path}")
            return
        
        # Nome do arquivo de relatório
        output_file = f"integridade_duckdb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            conn = duckdb.connect(str(self.db_path), read_only=True)
            
            # Abrir arquivo de relatório
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 100 + "\n")
                f.write("RELATÓRIO DE INTEGRIDADE REFERENCIAL - DUCKDB\n")
                f.write("=" * 100 + "\n\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Banco: {self.db_path}\n\n")
                
                # Verificar cada tabela fato
                total_verificacoes = 0
                total_problemas = 0
                problemas_detalhados = []
                
                for tabela_fato in self.tabelas_fato:
                    print(f"\n📊 Verificando tabela: {tabela_fato}")
                    f.write(f"\n{'='*100}\n")
                    f.write(f"TABELA: {tabela_fato.upper()}\n")
                    f.write(f"{'='*100}\n\n")
                    
                    if not self.verificar_tabela_existe(conn, tabela_fato):
                        print(f"   ⚠️ Tabela não existe!")
                        f.write("❌ TABELA NÃO EXISTE NO BANCO\n")
                        continue
                    
                    # Determinar tipo da tabela (despesa ou receita)
                    tipo = 'despesa' if 'despesa' in tabela_fato else 'receita'
                    
                    # Relacionamentos a verificar
                    relacionamentos = {}
                    relacionamentos.update(self.relacionamentos['comum'])
                    relacionamentos.update(self.relacionamentos[tipo])
                    
                    # Verificar cada relacionamento
                    verificacoes_tabela = []
                    
                    for coluna_fk, tabela_dim in relacionamentos.items():
                        print(f"   Verificando: {coluna_fk} -> {tabela_dim}")
                        resultado = self.verificar_integridade_relacionamento(
                            conn, tabela_fato, coluna_fk, tabela_dim
                        )
                        verificacoes_tabela.append(resultado)
                        total_verificacoes += 1
                        
                        if resultado['status'] == 'PROBLEMAS_ENCONTRADOS':
                            total_problemas += 1
                            problemas_detalhados.append(resultado)
                    
                    # Escrever resultados da tabela
                    f.write(f"{'Coluna FK':<20} {'Tabela Dimensão':<35} {'Status':<20} {'Valores Órfãos':<15}\n")
                    f.write("-" * 90 + "\n")
                    
                    for v in verificacoes_tabela:
                        status_emoji = {
                            'OK': '✅',
                            'PROBLEMAS_ENCONTRADOS': '❌',
                            'TABELA_DIM_NAO_EXISTE': '⚠️',
                            'COLUNA_FK_NAO_EXISTE': '➖',
                            'ERRO': '💥'
                        }.get(v['status'], '❓')
                        
                        f.write(f"{v['coluna_fk']:<20} {v['tabela_dimensao']:<35} "
                               f"{status_emoji + ' ' + v['status']:<20} ")
                        
                        if v['status'] == 'PROBLEMAS_ENCONTRADOS':
                            f.write(f"{v['valores_orfaos']:>15,}")
                        elif v['status'] == 'OK':
                            f.write(f"{'0':>15}")
                        else:
                            f.write(f"{'-':>15}")
                        
                        f.write("\n")
                    
                    # Resumo da tabela
                    f.write(f"\nResumo: {len(verificacoes_tabela)} verificações realizadas\n")
                
                # Detalhes dos problemas encontrados
                if problemas_detalhados:
                    f.write("\n\n" + "="*100 + "\n")
                    f.write("DETALHAMENTO DOS PROBLEMAS ENCONTRADOS\n")
                    f.write("="*100 + "\n\n")
                    
                    for problema in problemas_detalhados:
                        f.write(f"\n{problema['tabela_fato']}.{problema['coluna_fk']} -> "
                               f"{problema['tabela_dimensao']}\n")
                        f.write("-" * 50 + "\n")
                        f.write(f"Total de registros afetados: {problema['total_fato']:,}\n")
                        f.write(f"Valores distintos: {problema['valores_distintos']:,}\n")
                        f.write(f"Valores órfãos: {problema['valores_orfaos']:,}\n")
                        
                        if problema['exemplos_orfaos']:
                            f.write(f"Exemplos de valores órfãos: {', '.join(problema['exemplos_orfaos'])}\n")
                
                # Resumo final
                f.write("\n\n" + "="*100 + "\n")
                f.write("RESUMO FINAL\n")
                f.write("="*100 + "\n\n")
                f.write(f"Total de verificações: {total_verificacoes}\n")
                f.write(f"Verificações OK: {total_verificacoes - total_problemas}\n")
                f.write(f"Problemas encontrados: {total_problemas}\n")
                
                if total_problemas == 0:
                    f.write("\n🎉 PARABÉNS! Nenhum problema de integridade foi encontrado!\n")
                else:
                    f.write(f"\n⚠️ ATENÇÃO: Foram encontrados {total_problemas} problemas de integridade!\n")
                    f.write("\nRECOMENDAÇÕES:\n")
                    f.write("1. Verifique se todas as tabelas dimensão foram carregadas corretamente\n")
                    f.write("2. Considere criar registros 'DESCONHECIDO' ou 'NÃO INFORMADO' nas dimensões\n")
                    f.write("3. Analise os valores órfãos para entender se são dados válidos\n")
                    f.write("4. Execute limpeza ou correção dos dados nas tabelas fato se necessário\n")
                
                f.write("\n" + "="*100 + "\n")
                f.write("FIM DO RELATÓRIO\n")
                f.write("="*100 + "\n")
            
            conn.close()
            
            print(f"\n✅ Verificação concluída!")
            print(f"📄 Relatório salvo em: {output_file}")
            
            # Mostrar resumo na tela
            print(f"\n📊 RESUMO:")
            print(f"   Total de verificações: {total_verificacoes}")
            print(f"   Problemas encontrados: {total_problemas}")
            
            if total_problemas > 0:
                print(f"\n⚠️ ATENÇÃO: Foram encontrados problemas de integridade!")
                print(f"   Consulte o relatório para mais detalhes.")
                
                # Criar script SQL de correção?
                resposta = input("\nDeseja gerar script SQL para análise dos problemas? (s/N): ")
                if resposta.lower() == 's':
                    self.gerar_script_analise(problemas_detalhados)
            
        except Exception as e:
            print(f"\n❌ Erro durante a verificação: {e}")
            import traceback
            traceback.print_exc()
    
    def gerar_script_analise(self, problemas):
        """Gera script SQL para análise dos problemas encontrados"""
        output_sql = f"analise_integridade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        with open(output_sql, 'w', encoding='utf-8') as f:
            f.write("-- Script de análise dos problemas de integridade\n")
            f.write(f"-- Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            
            for problema in problemas:
                f.write(f"\n-- Análise: {problema['tabela_fato']}.{problema['coluna_fk']} -> "
                       f"{problema['tabela_dimensao']}\n")
                f.write("-" * 60 + "\n")
                
                # Query para listar todos os valores órfãos
                f.write(f"-- Valores órfãos (total: {problema['valores_orfaos']})\n")
                f.write(f"SELECT DISTINCT f.{problema['coluna_fk']}, COUNT(*) as qtd\n")
                f.write(f"FROM {problema['tabela_fato']} f\n")
                f.write(f"LEFT JOIN {problema['tabela_dimensao']} d "
                       f"ON f.{problema['coluna_fk']} = d.{problema['coluna_fk']}\n")
                f.write(f"WHERE f.{problema['coluna_fk']} IS NOT NULL\n")
                f.write(f"AND d.{problema['coluna_fk']} IS NULL\n")
                f.write(f"GROUP BY f.{problema['coluna_fk']}\n")
                f.write(f"ORDER BY COUNT(*) DESC;\n\n")
                
                # Query para ver exemplos de registros afetados
                f.write(f"-- Exemplos de registros afetados\n")
                f.write(f"SELECT *\n")
                f.write(f"FROM {problema['tabela_fato']} f\n")
                f.write(f"WHERE f.{problema['coluna_fk']} IN (\n")
                f.write(f"    SELECT DISTINCT f2.{problema['coluna_fk']}\n")
                f.write(f"    FROM {problema['tabela_fato']} f2\n")
                f.write(f"    LEFT JOIN {problema['tabela_dimensao']} d "
                       f"ON f2.{problema['coluna_fk']} = d.{problema['coluna_fk']}\n")
                f.write(f"    WHERE f2.{problema['coluna_fk']} IS NOT NULL\n")
                f.write(f"    AND d.{problema['coluna_fk']} IS NULL\n")
                f.write(f")\nLIMIT 10;\n\n")
        
        print(f"\n📄 Script SQL gerado: {output_sql}")

def main():
    """Função principal"""
    print("\n🔍 VERIFICADOR DE INTEGRIDADE REFERENCIAL")
    print("Este script irá verificar:")
    print("  - Se todos os valores FK nas tabelas fato existem nas dimensões")
    print("  - Identificar valores órfãos")
    print("  - Gerar relatório detalhado dos problemas\n")
    
    resposta = input("Iniciar verificação? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Operação cancelada.")
        return
    
    verificador = VerificadorIntegridade()
    verificador.executar_verificacao()

if __name__ == "__main__":
    main()