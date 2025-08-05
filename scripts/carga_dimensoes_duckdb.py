#!/usr/bin/env python3
"""
Script para carregar todas as tabelas dimensão no DuckDB
Processa arquivos Excel da pasta dados_brutos/dimensao
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CarregadorDimensoes:
    """Classe para carregar tabelas dimensão no DuckDB"""
    
    def __init__(self):
        self.db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
        self.dimensao_path = Path("dados_brutos/dimensao")
        
        # Configuração das dimensões com seus arquivos e chaves
        self.dimensoes_config = {
            'ClassificacaoOrcamentaria.xlsx': {
                'table_name': 'dim_classificacao_orcamentaria',
                'primary_key': 'coclasseorc',
                'description': 'Classificação Orçamentária'
            },
            'ContaContabil.xlsx': {
                'table_name': 'dim_conta_contabil',
                'primary_key': 'cocontacontabil',
                'description': 'Conta Contábil'
            },
            'Despesa_CategoriaDespesa.xlsx': {
                'table_name': 'dim_categoria_despesa',
                'primary_key': 'incategoria',
                'description': 'Categoria de Despesa'
            },
            'Despesa_Funcao.xlsx': {
                'table_name': 'dim_funcao',
                'primary_key': 'cofuncao',
                'description': 'Função'
            },
            'Despesa_GrupoDespesa.xlsx': {
                'table_name': 'dim_grupo_despesa',
                'primary_key': 'cogrupo',
                'description': 'Grupo de Despesa'
            },
            'Despesa_Modalidade.xlsx': {
                'table_name': 'dim_modalidade',
                'primary_key': 'comodalidade',
                'description': 'Modalidade de Aplicação'
            },
            'Despesa_Programa.xlsx': {
                'table_name': 'dim_programa',
                'primary_key': 'coprograma',
                'description': 'Programa'
            },
            'Despesa_Projeto.xlsx': {
                'table_name': 'dim_projeto',
                'primary_key': 'coprojeto',
                'description': 'Projeto/Atividade'
            },
            'Despesa_Subfuncao.xlsx': {
                'table_name': 'dim_subfuncao',
                'primary_key': 'cosubfuncao',
                'description': 'Subfunção'
            },
            'Despesa_Subtitulo.xlsx': {
                'table_name': 'dim_subtitulo',
                'primary_key': 'cosubtitulo',  # Corrigido - era COPROJETO
                'description': 'Subtítulo'
            },
            'Elemento.xlsx': {
                'table_name': 'dim_elemento',
                'primary_key': 'coelemento',
                'description': 'Elemento de Despesa'
            },
            'Evento.xlsx': {
                'table_name': 'dim_evento',
                'primary_key': 'coevento',
                'description': 'Evento'
            },
            'Fonte.xlsx': {
                'table_name': 'dim_fonte',
                'primary_key': 'cofonte',
                'description': 'Fonte de Recursos'
            },
            'Gestao.xlsx': {
                'table_name': 'dim_gestao',
                'primary_key': 'cogestao',
                'description': 'Gestão'
            },
            'Receita_Alinea.xlsx': {
                'table_name': 'dim_receita_alinea',
                'primary_key': 'coalinea',
                'description': 'Alínea da Receita'
            },
            'Receita_Categoria.xlsx': {
                'table_name': 'dim_receita_categoria',
                'primary_key': 'cocategoriareceita',
                'description': 'Categoria da Receita'
            },
            'Receita_Especie.xlsx': {
                'table_name': 'dim_receita_especie',
                'primary_key': 'cosubfontereceita',
                'description': 'Espécie da Receita'
            },
            'Receita_Especificacao.xlsx': {
                'table_name': 'dim_receita_especificacao',
                'primary_key': 'corubrica',
                'description': 'Especificação da Receita'
            },
            'Receita_Origem.xlsx': {
                'table_name': 'dim_receita_origem',
                'primary_key': 'cofontereceita',
                'description': 'Origem da Receita'
            },
            'UnidadeGestora.xlsx': {
                'table_name': 'dim_unidade_gestora',
                'primary_key': 'coug',
                'description': 'Unidade Gestora'
            }
        }
    
    def verificar_arquivos(self):
        """Verifica quais arquivos existem na pasta dimensão"""
        print(f"\n🔍 Verificando arquivos em: {self.dimensao_path}")
        
        arquivos_encontrados = []
        arquivos_faltando = []
        
        for arquivo, config in self.dimensoes_config.items():
            caminho = self.dimensao_path / arquivo
            if caminho.exists():
                arquivos_encontrados.append((arquivo, caminho))
                print(f"   ✅ {arquivo}")
            else:
                arquivos_faltando.append(arquivo)
                print(f"   ❌ {arquivo} - NÃO ENCONTRADO")
        
        return arquivos_encontrados, arquivos_faltando
    
    def processar_arquivo(self, arquivo, caminho, config):
        """Processa um arquivo Excel e carrega no DuckDB"""
        try:
            print(f"\n📄 Processando: {arquivo}")
            
            # Ler arquivo Excel
            df = pd.read_excel(caminho)
            print(f"   Linhas: {len(df):,}")
            print(f"   Colunas: {', '.join(df.columns)}")
            
            # Converter nomes das colunas para minúsculas
            df.columns = df.columns.str.lower()
            
            # Verificar se a chave primária existe
            pk = config['primary_key'].lower()
            if pk not in df.columns:
                print(f"   ⚠️ AVISO: Chave primária '{pk}' não encontrada nas colunas!")
                print(f"   Colunas disponíveis: {', '.join(df.columns)}")
            
            # Conectar ao DuckDB
            conn = duckdb.connect(str(self.db_path))
            
            try:
                # Verificar se a tabela já existe
                table_exists = conn.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = '{config['table_name']}'
                """).fetchone()[0] > 0
                
                if table_exists:
                    # Contar registros existentes
                    count_before = conn.execute(f"SELECT COUNT(*) FROM {config['table_name']}").fetchone()[0]
                    print(f"   ⚠️ Tabela já existe com {count_before:,} registros")
                    
                    resposta = input(f"   Deseja SUBSTITUIR a tabela {config['table_name']}? (s/N): ")
                    if resposta.lower() != 's':
                        print(f"   ⏭️ Pulando {arquivo}")
                        return False
                    
                    # Dropar tabela existente
                    conn.execute(f"DROP TABLE {config['table_name']}")
                    print(f"   🗑️ Tabela anterior removida")
                
                # Criar tabela a partir do DataFrame
                conn.register('df_temp', df)
                conn.execute(f"""
                    CREATE TABLE {config['table_name']} AS 
                    SELECT * FROM df_temp
                """)
                conn.unregister('df_temp')
                
                # Adicionar chave primária se a coluna existir
                if pk in df.columns:
                    try:
                        # Verificar duplicatas antes de criar PK
                        duplicatas = conn.execute(f"""
                            SELECT {pk}, COUNT(*) as qtd 
                            FROM {config['table_name']} 
                            GROUP BY {pk} 
                            HAVING COUNT(*) > 1
                        """).fetchall()
                        
                        if duplicatas:
                            print(f"   ⚠️ AVISO: Encontradas {len(duplicatas)} chaves duplicadas em '{pk}'")
                            print(f"   Não foi possível criar chave primária")
                        else:
                            # DuckDB não suporta ALTER TABLE ADD PRIMARY KEY diretamente
                            # Mas podemos criar um índice único
                            conn.execute(f"""
                                CREATE UNIQUE INDEX idx_{config['table_name']}_{pk} 
                                ON {config['table_name']}({pk})
                            """)
                            print(f"   🔑 Índice único criado em '{pk}'")
                    except Exception as e:
                        print(f"   ⚠️ Erro ao criar índice: {e}")
                
                # Verificar total inserido
                count_after = conn.execute(f"SELECT COUNT(*) FROM {config['table_name']}").fetchone()[0]
                print(f"   ✅ {count_after:,} registros carregados com sucesso!")
                
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"   ❌ ERRO ao processar {arquivo}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def executar_carga(self):
        """Executa a carga de todas as dimensões"""
        print("=" * 80)
        print("CARGA DE TABELAS DIMENSÃO - DUCKDB")
        print("=" * 80)
        print(f"Banco de dados: {self.db_path}")
        print(f"Pasta de origem: {self.dimensao_path}")
        
        # Verificar se o banco existe
        if not self.db_path.exists():
            print(f"\n❌ ERRO: Banco de dados não encontrado: {self.db_path}")
            return
        
        # Verificar arquivos
        arquivos_encontrados, arquivos_faltando = self.verificar_arquivos()
        
        if arquivos_faltando:
            print(f"\n⚠️ ATENÇÃO: {len(arquivos_faltando)} arquivos não encontrados")
            resposta = input("\nDeseja continuar com os arquivos disponíveis? (S/n): ")
            if resposta.lower() == 'n':
                print("\n❌ Carga cancelada")
                return
        
        print(f"\n📋 {len(arquivos_encontrados)} arquivos serão processados")
        resposta = input("\nConfirma o processamento? (S/n): ")
        if resposta.lower() == 'n':
            print("\n❌ Carga cancelada")
            return
        
        # Processar cada arquivo
        inicio = datetime.now()
        sucesso = 0
        falha = 0
        
        for arquivo, caminho in arquivos_encontrados:
            config = self.dimensoes_config[arquivo]
            if self.processar_arquivo(arquivo, caminho, config):
                sucesso += 1
            else:
                falha += 1
        
        # Resumo final
        tempo_total = datetime.now() - inicio
        print("\n" + "=" * 80)
        print("RESUMO DA CARGA")
        print("=" * 80)
        print(f"✅ Sucesso: {sucesso} tabelas")
        print(f"❌ Falha: {falha} tabelas")
        print(f"⏱️ Tempo total: {tempo_total}")
        
        if sucesso > 0:
            print("\n🎉 Carga concluída!")
            print("\n📌 Próximos passos:")
            print("   1. Gerar nova documentação da estrutura:")
            print("      python scripts/atualizar_documentacao_duckdb.py")
            print("   2. Verificar integridade dos relacionamentos:")
            print("      python scripts/verificar_integridade_duckdb.py")

def main():
    """Função principal"""
    carregador = CarregadorDimensoes()
    carregador.executar_carga()

if __name__ == "__main__":
    main()