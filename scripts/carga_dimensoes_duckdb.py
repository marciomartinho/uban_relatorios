#!/usr/bin/env python3
"""
Script VERDADEIRAMENTE INTELIGENTE para carregar dimensões no DuckDB.
Aprende e lembra dos mapeamentos arquivo->tabela usando um arquivo JSON.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime
import logging
import re
import json
import hashlib

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CarregadorVerdadeiramenteInteligente:
    """Carregador que REALMENTE aprende e lembra dos mapeamentos"""
    
    def __init__(self):
        self.db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
        self.dimensao_path = Path("dados_brutos/dimensao")
        
        # Arquivo onde salvamos os mapeamentos aprendidos
        self.mapeamento_file = Path("dados_brutos/dimensao/.mapeamento_dimensoes.json")
        self.historico_file = Path("dados_brutos/dimensao/.historico_cargas.json")
        
        # Carrega mapeamentos salvos ou cria novo
        self.mapeamentos = self.carregar_mapeamentos()
        self.historico = self.carregar_historico()
    
    def carregar_mapeamentos(self):
        """Carrega mapeamentos salvos do arquivo JSON"""
        if self.mapeamento_file.exists():
            try:
                with open(self.mapeamento_file, 'r', encoding='utf-8') as f:
                    mapeamentos = json.load(f)
                print(f"📚 Mapeamentos carregados: {len(mapeamentos)} registros conhecidos")
                return mapeamentos
            except Exception as e:
                print(f"⚠️ Erro ao carregar mapeamentos: {e}")
                return {}
        else:
            print("📝 Criando novo arquivo de mapeamentos...")
            return {}
    
    def salvar_mapeamentos(self):
        """Salva mapeamentos aprendidos no arquivo JSON"""
        try:
            with open(self.mapeamento_file, 'w', encoding='utf-8') as f:
                json.dump(self.mapeamentos, f, indent=2, ensure_ascii=False)
            print(f"💾 Mapeamentos salvos: {len(self.mapeamentos)} registros")
        except Exception as e:
            print(f"❌ Erro ao salvar mapeamentos: {e}")
    
    def carregar_historico(self):
        """Carrega histórico de cargas realizadas"""
        if self.historico_file.exists():
            try:
                with open(self.historico_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def salvar_historico(self, arquivo, tabela, acao, registros):
        """Salva no histórico cada operação realizada"""
        if arquivo not in self.historico:
            self.historico[arquivo] = []
        
        self.historico[arquivo].append({
            'data': datetime.now().isoformat(),
            'tabela': tabela,
            'acao': acao,
            'registros': registros
        })
        
        try:
            with open(self.historico_file, 'w', encoding='utf-8') as f:
                json.dump(self.historico, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def calcular_hash_arquivo(self, caminho):
        """Calcula hash do arquivo para detectar mudanças"""
        hash_md5 = hashlib.md5()
        with open(caminho, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def gerar_nome_tabela_inteligente(self, nome_arquivo):
        """Gera nome de tabela usando aprendizado ou sugestão"""
        # Primeiro verifica se já aprendeu este mapeamento
        if nome_arquivo in self.mapeamentos:
            info = self.mapeamentos[nome_arquivo]
            print(f"   🧠 Mapeamento conhecido: {nome_arquivo} → {info['tabela']}")
            return info['tabela']
        
        # Se não conhece, gera sugestão
        nome = nome_arquivo.replace('.xlsx', '').replace('.xls', '').replace('.csv', '')
        
        # Converte CamelCase para snake_case
        nome = re.sub('([A-Z]+)([A-Z][a-z])', r'\1_\2', nome)
        nome = re.sub('([a-z\d])([A-Z])', r'\1_\2', nome)
        nome = nome.lower()
        
        # Adiciona prefixo dim_ se não tiver
        if not nome.startswith('dim_') and not nome.startswith('fato_'):
            nome = 'dim_' + nome
        
        print(f"   💡 Sugestão de nome: {nome}")
        return nome
    
    def detectar_chave_primaria(self, df, nome_tabela):
        """Detecta chave primária inteligentemente"""
        colunas = df.columns.str.lower()
        
        # Se já conhece este arquivo, usa a PK salva
        for arquivo, info in self.mapeamentos.items():
            if info['tabela'] == nome_tabela and 'pk' in info:
                if info['pk'] in colunas:
                    return info['pk']
        
        # Senão, tenta detectar
        candidatos = []
        
        for col in colunas:
            # Calcula score para cada coluna
            score = 0
            
            # Padrões comuns
            if col.startswith('co'):
                score += 3
            if col.startswith('id'):
                score += 3
            if 'codigo' in col or 'code' in col:
                score += 2
            if col.endswith('id'):
                score += 1
            
            # Verifica unicidade
            if len(df[col].dropna()) > 0:
                unicidade = df[col].nunique() / len(df)
                if unicidade == 1.0:
                    score += 5
                elif unicidade > 0.95:
                    score += 3
                elif unicidade > 0.8:
                    score += 1
            
            if score > 0:
                candidatos.append((col, score))
        
        # Ordena por score e pega o melhor
        if candidatos:
            candidatos.sort(key=lambda x: x[1], reverse=True)
            return candidatos[0][0]
        
        return colunas[0]
    
    def analisar_situacao_completa(self):
        """Análise completa e inteligente da situação"""
        print("\n" + "="*80)
        print("🧠 ANÁLISE INTELIGENTE COMPLETA")
        print("="*80)
        
        # Listar arquivos Excel
        arquivos_excel = list(self.dimensao_path.glob("*.xlsx")) + \
                        list(self.dimensao_path.glob("*.xls"))
        
        # Listar tabelas no banco
        tabelas_banco = set()
        if self.db_path.exists():
            conn = duckdb.connect(str(self.db_path))
            try:
                result = conn.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'main'
                """).fetchall()
                tabelas_banco = {t[0] for t in result}
            finally:
                conn.close()
        
        # Classificar arquivos
        status_arquivos = {
            'novos': [],
            'conhecidos_existentes': [],
            'conhecidos_ausentes': [],
            'modificados': [],
            'desconhecidos_com_tabela': []
        }
        
        for arquivo in arquivos_excel:
            nome_arquivo = arquivo.name
            hash_atual = self.calcular_hash_arquivo(arquivo)
            
            if nome_arquivo in self.mapeamentos:
                # Arquivo conhecido
                info = self.mapeamentos[nome_arquivo]
                nome_tabela = info['tabela']
                
                if nome_tabela in tabelas_banco:
                    # Tabela existe
                    if info.get('hash') != hash_atual:
                        status_arquivos['modificados'].append({
                            'arquivo': nome_arquivo,
                            'tabela': nome_tabela,
                            'ultima_carga': info.get('ultima_carga', 'desconhecida'),
                            'caminho': arquivo
                        })
                    else:
                        status_arquivos['conhecidos_existentes'].append({
                            'arquivo': nome_arquivo,
                            'tabela': nome_tabela,
                            'ultima_carga': info.get('ultima_carga', 'desconhecida'),
                            'caminho': arquivo
                        })
                else:
                    # Tabela não existe (foi deletada?)
                    status_arquivos['conhecidos_ausentes'].append({
                        'arquivo': nome_arquivo,
                        'tabela': nome_tabela,
                        'caminho': arquivo
                    })
            else:
                # Arquivo desconhecido
                nome_sugerido = self.gerar_nome_tabela_inteligente(nome_arquivo)
                
                if nome_sugerido in tabelas_banco:
                    # Pode ser um arquivo renomeado
                    status_arquivos['desconhecidos_com_tabela'].append({
                        'arquivo': nome_arquivo,
                        'tabela_sugerida': nome_sugerido,
                        'caminho': arquivo
                    })
                else:
                    # Completamente novo
                    status_arquivos['novos'].append({
                        'arquivo': nome_arquivo,
                        'tabela_sugerida': nome_sugerido,
                        'caminho': arquivo
                    })
        
        return status_arquivos, tabelas_banco
    
    def processar_arquivo_com_aprendizado(self, info_arquivo):
        """Processa arquivo e aprende o mapeamento"""
        arquivo = info_arquivo['arquivo']
        caminho = info_arquivo['caminho']
        
        # Determina nome da tabela
        if 'tabela' in info_arquivo:
            nome_tabela = info_arquivo['tabela']
        else:
            nome_tabela = info_arquivo.get('tabela_sugerida', 
                                          self.gerar_nome_tabela_inteligente(arquivo))
        
        print(f"\n📄 Processando: {arquivo}")
        
        try:
            # Ler arquivo
            df = pd.read_excel(caminho)
            df.columns = df.columns.str.lower()
            
            print(f"   📊 {len(df):,} linhas, {len(df.columns)} colunas")
            
            # Detectar PK
            pk = self.detectar_chave_primaria(df, nome_tabela)
            print(f"   🔑 Chave primária: {pk}")
            
            # Perguntar confirmação
            print(f"   📋 Tabela: {nome_tabela}")
            resp = input("   Confirmar (Enter), digitar outro nome (n), ou pular (p)? ").strip()
            
            if resp.lower() == 'p':
                print("   ⏭️ Pulado")
                return False
            elif resp.lower() == 'n':
                novo_nome = input("   Digite o nome da tabela: ").strip()
                if novo_nome:
                    nome_tabela = novo_nome
            
            # Verificar se tabela existe
            conn = duckdb.connect(str(self.db_path))
            try:
                existe = conn.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = '{nome_tabela}'
                """).fetchone()[0] > 0
                
                if existe:
                    count = conn.execute(f"SELECT COUNT(*) FROM {nome_tabela}").fetchone()[0]
                    print(f"   ⚠️ Tabela existe com {count:,} registros")
                    resp = input("   Substituir? (s/N): ")
                    if resp.lower() != 's':
                        return False
                    conn.execute(f"DROP TABLE {nome_tabela}")
                
                # Criar tabela
                conn.register('df_temp', df)
                conn.execute(f"CREATE TABLE {nome_tabela} AS SELECT * FROM df_temp")
                conn.unregister('df_temp')
                
                count_final = conn.execute(f"SELECT COUNT(*) FROM {nome_tabela}").fetchone()[0]
                print(f"   ✅ {count_final:,} registros carregados!")
                
                # APRENDER E SALVAR o mapeamento
                self.mapeamentos[arquivo] = {
                    'tabela': nome_tabela,
                    'pk': pk,
                    'hash': self.calcular_hash_arquivo(caminho),
                    'ultima_carga': datetime.now().isoformat(),
                    'registros': count_final,
                    'colunas': list(df.columns)
                }
                self.salvar_mapeamentos()
                
                # Salvar no histórico
                self.salvar_historico(arquivo, nome_tabela, 'carga', count_final)
                
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return False
    
    def menu_principal(self):
        """Menu principal inteligente"""
        print("\n" + "="*80)
        print("🧠 CARREGADOR VERDADEIRAMENTE INTELIGENTE")
        print("="*80)
        
        # Análise
        status, tabelas = self.analisar_situacao_completa()
        
        # Mostrar resumo
        if status['novos']:
            print(f"\n🆕 Arquivos COMPLETAMENTE NOVOS: {len(status['novos'])}")
            for item in status['novos']:
                print(f"   • {item['arquivo']}")
        
        if status['modificados']:
            print(f"\n📝 Arquivos MODIFICADOS: {len(status['modificados'])}")
            for item in status['modificados']:
                print(f"   • {item['arquivo']} (última carga: {item['ultima_carga'][:10]})")
        
        if status['conhecidos_existentes']:
            print(f"\n✅ Arquivos SINCRONIZADOS: {len(status['conhecidos_existentes'])}")
        
        if status['conhecidos_ausentes']:
            print(f"\n⚠️ Tabelas DELETADAS do banco: {len(status['conhecidos_ausentes'])}")
            for item in status['conhecidos_ausentes']:
                print(f"   • {item['arquivo']} → {item['tabela']} (tabela não existe mais)")
        
        # Menu
        print("\n" + "="*80)
        print("OPÇÕES:")
        print("[1] Carregar apenas NOVOS")
        print("[2] Atualizar MODIFICADOS")
        print("[3] Recriar tabelas DELETADAS")
        print("[4] Processar TUDO")
        print("[5] Ver histórico de cargas")
        print("[6] Resetar aprendizado")
        print("[0] Sair")
        
        opcao = input("\nEscolha: ").strip()
        
        if opcao == '1':
            for item in status['novos']:
                self.processar_arquivo_com_aprendizado(item)
        
        elif opcao == '2':
            for item in status['modificados']:
                print(f"\n📝 Arquivo modificado: {item['arquivo']}")
                resp = input("   Atualizar? (s/N): ")
                if resp.lower() == 's':
                    self.processar_arquivo_com_aprendizado(item)
        
        elif opcao == '3':
            for item in status['conhecidos_ausentes']:
                self.processar_arquivo_com_aprendizado(item)
        
        elif opcao == '4':
            todos = (status['novos'] + status['modificados'] + 
                    status['conhecidos_ausentes'] + status['conhecidos_existentes'])
            for item in todos:
                self.processar_arquivo_com_aprendizado(item)
        
        elif opcao == '5':
            print("\n📜 HISTÓRICO DE CARGAS:")
            for arquivo, historico in self.historico.items():
                print(f"\n{arquivo}:")
                for h in historico[-3:]:  # Últimas 3 operações
                    print(f"   • {h['data'][:19]} - {h['acao']} - {h['registros']} registros")
        
        elif opcao == '6':
            resp = input("⚠️ Isso apagará todo o aprendizado. Confirma? (s/N): ")
            if resp.lower() == 's':
                self.mapeamentos = {}
                self.historico = {}
                self.salvar_mapeamentos()
                print("🧹 Aprendizado resetado!")
        
        print("\n✨ Operação concluída!")

def main():
    """Função principal"""
    carregador = CarregadorVerdadeiramenteInteligente()
    carregador.menu_principal()

if __name__ == "__main__":
    main()