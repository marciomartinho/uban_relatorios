"""
Script para carregar TODAS as tabelas dimensão no PostgreSQL.
Lê os arquivos Excel da pasta 'dados_brutos/dimensao' e os insere
no banco de dados de produção configurado no arquivo .env.
"""
import sys
import os
from datetime import datetime
from pathlib import Path
import pandas as pd

# Adiciona o diretório raiz do projeto ao path para encontrar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa a conexão SQLAlchemy do seu módulo de banco de dados PostgreSQL
from app.modules.database import db

class CarregadorDimensoesPostgres:
    """Classe para carregar tabelas dimensão no PostgreSQL."""
    
    def __init__(self):
        self.dimensao_path = Path("dados_brutos/dimensao")
        # A configuração do banco de dados agora vem do .env e do database.py
        self.engine = db.engine
        
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
        """Processa um arquivo Excel e o carrega no PostgreSQL."""
        try:
            print(f"\n📄 Processando: {arquivo}")
            table_name = config['table_name']

            # 1. Ler o arquivo Excel com pandas
            df = pd.read_excel(caminho)
            print(f"   Lendo {len(df):,} linhas do arquivo Excel.")

            # 2. Padronizar nomes de colunas para minúsculas
            df.columns = df.columns.str.lower()
            
            # 3. Inserir dados no PostgreSQL
            print(f"   Inserindo dados na tabela '{table_name}' do PostgreSQL...")
            
            # df.to_sql é a função mágica do pandas para isso.
            # 'replace' irá apagar a tabela se ela já existir e criar uma nova com os dados.
            # Isso garante que a carga seja sempre completa e limpa.
            df.to_sql(
                name=table_name,
                con=self.engine,
                if_exists='replace',
                index=False
            )
            
            print(f"   ✅ {len(df):,} registros carregados com sucesso em '{table_name}'!")
            return True

        except Exception as e:
            print(f"   ❌ ERRO ao processar {arquivo}: {e}")
            return False

    def executar_carga_completa(self):
        """Orquestra a carga de todas as tabelas de dimensão."""
        print("=" * 80)
        print("CARGA DE TABELAS DIMENSÃO PARA O POSTGRESQL")
        print("=" * 80)
        
        # Testar a conexão com o PostgreSQL antes de começar
        print("🔌 Testando conexão com o PostgreSQL na VPS...")
        if not db.test_connection():
             print("\n❌ Falha na conexão com o PostgreSQL. Verifique seu arquivo .env e as configurações da VPS.")
             return
        
        arquivos_encontrados, arquivos_faltando = self.verificar_arquivos()

        if arquivos_faltando:
            print(f"\n⚠️ ATENÇÃO: {len(arquivos_faltando)} arquivos de dimensão não foram encontrados.")
            resposta = input("Deseja continuar com os arquivos disponíveis? (S/n): ")
            if resposta.lower() == 'n':
                print("\n❌ Carga cancelada pelo usuário.")
                return

        print(f"\n📋 {len(arquivos_encontrados)} tabelas de dimensão serão carregadas/substituídas no PostgreSQL.")
        resposta = input("Confirma o processamento? (S/n): ")
        if resposta.lower() == 'n':
            print("\n❌ Carga cancelada pelo usuário.")
            return

        inicio = datetime.now()
        sucesso = 0
        falha = 0

        for arquivo, caminho in arquivos_encontrados:
            config = self.dimensoes_config[arquivo]
            if self.processar_arquivo(arquivo, caminho, config):
                sucesso += 1
            else:
                falha += 1

        tempo_total = datetime.now() - inicio
        print("\n" + "=" * 80)
        print("RESUMO DA CARGA DAS DIMENSÕES")
        print("=" * 80)
        print(f"✅ Tabelas processadas com sucesso: {sucesso}")
        print(f"❌ Tabelas com falha: {falha}")
        print(f"⏱️ Tempo total da operação: {tempo_total}")
        
        if sucesso > 0:
            print("\n🎉 Carga das tabelas de dimensão no PostgreSQL concluída!")

def main():
    """Função principal para executar o carregador."""
    carregador = CarregadorDimensoesPostgres()
    carregador.executar_carga_completa()

if __name__ == "__main__":
    main()