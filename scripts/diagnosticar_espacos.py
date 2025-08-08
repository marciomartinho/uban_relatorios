"""
Script de Diagnóstico para verificar espaços em branco e inconsistências
Execute este script para identificar problemas nos dados

Uso:
    python scripts/diagnosticar_espacos.py
"""
import sys
import os
from datetime import datetime
import pandas as pd

# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Agora importa os módulos do projeto
from app.db_manager import db_manager
from app import create_app

def diagnosticar_espacos():
    """Diagnóstico completo de espaços em branco e inconsistências"""
    
    # Criar contexto da aplicação
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("DIAGNÓSTICO DE ESPAÇOS EM BRANCO E INCONSISTÊNCIAS")
        print("=" * 80)
        
        ano_atual = datetime.now().year
        
        # 1. Verificar espaços na tabela dim_receita_fonte_conta_contabil
        print("\n1. VERIFICANDO ESPAÇOS NA TABELA dim_receita_fonte_conta_contabil:")
        print("-" * 60)
        
        query_dim = """
        SELECT 
            cofonte,
            coalinea,
            LENGTH(CAST(cofonte AS VARCHAR)) as len_fonte,
            LENGTH(TRIM(CAST(cofonte AS VARCHAR))) as len_fonte_trim,
            LENGTH(CAST(coalinea AS VARCHAR)) as len_alinea,
            LENGTH(TRIM(CAST(coalinea AS VARCHAR))) as len_alinea_trim,
            CASE 
                WHEN LENGTH(CAST(cofonte AS VARCHAR)) != LENGTH(TRIM(CAST(cofonte AS VARCHAR))) 
                THEN 'SIM' ELSE 'NÃO' 
            END as fonte_tem_espaco,
            CASE 
                WHEN LENGTH(CAST(coalinea AS VARCHAR)) != LENGTH(TRIM(CAST(coalinea AS VARCHAR))) 
                THEN 'SIM' ELSE 'NÃO' 
            END as alinea_tem_espaco
        FROM dim_receita_fonte_conta_contabil
        WHERE instatus = 0
          AND (
            LENGTH(CAST(cofonte AS VARCHAR)) != LENGTH(TRIM(CAST(cofonte AS VARCHAR)))
            OR LENGTH(CAST(coalinea AS VARCHAR)) != LENGTH(TRIM(CAST(coalinea AS VARCHAR)))
          )
        LIMIT 20
        """
        
        try:
            dados_dim = db_manager.execute_query(query_dim)
            if dados_dim:
                print(f"⚠️ ENCONTRADOS {len(dados_dim)} REGISTROS COM ESPAÇOS NA DIMENSÃO:")
                df_dim = pd.DataFrame(dados_dim)
                print(df_dim.to_string())
            else:
                print("✅ Nenhum registro com espaços encontrado na dimensão")
        except Exception as e:
            print(f"❌ Erro ao verificar dimensão: {e}")
        
        # 2. Verificar espaços na tabela receita_lancamento
        print("\n2. VERIFICANDO ESPAÇOS NA TABELA receita_lancamento:")
        print("-" * 60)
        
        query_lanc = """
        SELECT 
            nudocumento,
            cofonte,
            coalinea,
            LENGTH(CAST(cofonte AS VARCHAR)) as len_fonte,
            LENGTH(TRIM(CAST(cofonte AS VARCHAR))) as len_fonte_trim,
            LENGTH(CAST(coalinea AS VARCHAR)) as len_alinea,
            LENGTH(TRIM(CAST(coalinea AS VARCHAR))) as len_alinea_trim,
            CASE 
                WHEN LENGTH(CAST(cofonte AS VARCHAR)) != LENGTH(TRIM(CAST(cofonte AS VARCHAR))) 
                THEN 'SIM' ELSE 'NÃO' 
            END as fonte_tem_espaco,
            CASE 
                WHEN LENGTH(CAST(coalinea AS VARCHAR)) != LENGTH(TRIM(CAST(coalinea AS VARCHAR))) 
                THEN 'SIM' ELSE 'NÃO' 
            END as alinea_tem_espaco
        FROM receita_lancamento
        WHERE coexercicio = ?
          AND (
            LENGTH(CAST(cofonte AS VARCHAR)) != LENGTH(TRIM(CAST(cofonte AS VARCHAR)))
            OR LENGTH(CAST(coalinea AS VARCHAR)) != LENGTH(TRIM(CAST(coalinea AS VARCHAR)))
          )
        LIMIT 20
        """
        
        try:
            dados_lanc = db_manager.execute_query(query_lanc, [ano_atual])
            if dados_lanc:
                print(f"⚠️ ENCONTRADOS {len(dados_lanc)} LANÇAMENTOS COM ESPAÇOS:")
                df_lanc = pd.DataFrame(dados_lanc)
                print(df_lanc.to_string())
            else:
                print("✅ Nenhum lançamento com espaços encontrado")
        except Exception as e:
            print(f"❌ Erro ao verificar lançamentos: {e}")
        
        # 3. Verificar especificamente a combinação 220000000 + 112101
        print("\n3. VERIFICANDO COMBINAÇÃO ESPECÍFICA 220000000 + 112101:")
        print("-" * 60)
        
        # Na dimensão - verificar todas as variações possíveis
        print("\n3.1 - NA TABELA dim_receita_fonte_conta_contabil:")
        query_especifica_dim = """
        SELECT 
            cofonte,
            coalinea,
            '|' || cofonte || '|' as cofonte_delimitado,
            '|' || coalinea || '|' as coalinea_delimitado,
            instatus,
            COUNT(*) as qtd_registros
        FROM dim_receita_fonte_conta_contabil
        WHERE TRIM(CAST(cofonte AS VARCHAR)) = '220000000'
          AND TRIM(CAST(coalinea AS VARCHAR)) = '112101'
        GROUP BY cofonte, coalinea, instatus
        """
        
        try:
            dados_esp_dim = db_manager.execute_query(query_especifica_dim)
            if dados_esp_dim:
                print("✅ COMBINAÇÃO ENCONTRADA NA DIMENSÃO:")
                for reg in dados_esp_dim:
                    print(f"   Fonte: {reg['cofonte_delimitado']} | Alínea: {reg['coalinea_delimitado']}")
                    print(f"   Status: {reg['instatus']} | Quantidade: {reg['qtd_registros']}")
            else:
                print("❌ Combinação NÃO encontrada na dimensão com TRIM")
                
                # Tentar sem TRIM para ver se há diferença
                query_sem_trim = """
                SELECT 
                    cofonte,
                    coalinea,
                    '|' || cofonte || '|' as cofonte_delimitado,
                    '|' || coalinea || '|' as coalinea_delimitado,
                    instatus
                FROM dim_receita_fonte_conta_contabil
                WHERE CAST(cofonte AS VARCHAR) = '220000000'
                  AND CAST(coalinea AS VARCHAR) = '112101'
                """
                dados_sem_trim = db_manager.execute_query(query_sem_trim)
                if dados_sem_trim:
                    print("\n   MAS foi encontrada SEM TRIM (indica espaços):")
                    for reg in dados_sem_trim:
                        print(f"   Fonte: {reg['cofonte_delimitado']} | Alínea: {reg['coalinea_delimitado']}")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        # Verificar valores similares na dimensão
        print("\n3.2 - VALORES SIMILARES NA DIMENSÃO (pode haver variações):")
        query_similar = """
        SELECT DISTINCT
            cofonte,
            coalinea,
            '|' || cofonte || '|' as cofonte_delimitado,
            '|' || coalinea || '|' as coalinea_delimitado,
            instatus
        FROM dim_receita_fonte_conta_contabil
        WHERE CAST(cofonte AS VARCHAR) LIKE '%220000000%'
          AND CAST(coalinea AS VARCHAR) LIKE '%112101%'
        LIMIT 10
        """
        
        try:
            dados_similar = db_manager.execute_query(query_similar)
            if dados_similar:
                print("   Encontradas as seguintes variações:")
                for reg in dados_similar:
                    print(f"   Fonte: {reg['cofonte_delimitado']} | Alínea: {reg['coalinea_delimitado']} | Status: {reg['instatus']}")
            else:
                print("   Nenhuma variação encontrada")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        # Nos lançamentos
        print("\n3.3 - NOS LANÇAMENTOS:")
        query_especifica_lanc = """
        SELECT 
            COUNT(*) as qtd_lancamentos,
            SUM(valancamento) as valor_total,
            MIN(nudocumento) as exemplo_documento
        FROM receita_lancamento
        WHERE TRIM(CAST(cofonte AS VARCHAR)) = '220000000'
          AND TRIM(CAST(coalinea AS VARCHAR)) = '112101'
          AND coexercicio = ?
        """
        
        try:
            dados_esp_lanc = db_manager.execute_query(query_especifica_lanc, [ano_atual])
            if dados_esp_lanc and dados_esp_lanc[0]['qtd_lancamentos'] > 0:
                print(f"   Quantidade: {dados_esp_lanc[0]['qtd_lancamentos']}")
                print(f"   Valor Total: R$ {dados_esp_lanc[0]['valor_total']:,.2f}")
                print(f"   Documento exemplo: {dados_esp_lanc[0]['exemplo_documento']}")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        # 4. Verificar o formato exato dos valores
        print("\n4. ANÁLISE DE FORMATO DOS VALORES:")
        print("-" * 60)
        
        # Verificar caracteres ASCII
        print("\n4.1 - ANÁLISE DE CARACTERES (ASCII) DO DOCUMENTO 2025NL00819:")
        query_ascii = """
        SELECT 
            cofonte,
            coalinea,
            LENGTH(CAST(cofonte AS VARCHAR)) as len_fonte,
            LENGTH(CAST(coalinea AS VARCHAR)) as len_alinea
        FROM receita_lancamento
        WHERE nudocumento = '2025NL00819'
        """
        
        try:
            dados_ascii = db_manager.execute_query(query_ascii)
            if dados_ascii:
                for reg in dados_ascii:
                    print(f"\n   FONTE: '{reg['cofonte']}' (length: {reg['len_fonte']})")
                    print(f"   ALÍNEA: '{reg['coalinea']}' (length: {reg['len_alinea']})")
                    
                    # Mostrar caractere por caractere
                    fonte_str = str(reg['cofonte'])
                    alinea_str = str(reg['coalinea'])
                    
                    print(f"\n   Caracteres da FONTE: ", end="")
                    for i, char in enumerate(fonte_str):
                        print(f"[{i}:'{char}':ASCII {ord(char)}] ", end="")
                    
                    print(f"\n   Caracteres da ALÍNEA: ", end="")
                    for i, char in enumerate(alinea_str):
                        print(f"[{i}:'{char}':ASCII {ord(char)}] ", end="")
                    print()
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        # 5. Verificar todas as combinações únicas que estão causando problemas
        print("\n5. TOP 10 COMBINAÇÕES PROBLEMÁTICAS:")
        print("-" * 60)
        
        query_top_problemas = """
        SELECT 
            TRIM(CAST(rl.cofonte AS VARCHAR)) as cofonte,
            TRIM(CAST(rl.coalinea AS VARCHAR)) as coalinea,
            COUNT(DISTINCT rl.nudocumento) as qtd_docs,
            SUM(ABS(rl.valancamento)) as valor_total
        FROM receita_lancamento rl
        WHERE rl.coexercicio = ?
          AND rl.cofonte IS NOT NULL
          AND rl.coalinea IS NOT NULL
          AND NOT EXISTS(
              SELECT 1 
              FROM dim_receita_fonte_conta_contabil d 
              WHERE TRIM(CAST(d.cofonte AS VARCHAR)) = TRIM(CAST(rl.cofonte AS VARCHAR))
                AND TRIM(CAST(d.coalinea AS VARCHAR)) = TRIM(CAST(rl.coalinea AS VARCHAR))
                AND d.instatus = 0
          )
        GROUP BY TRIM(CAST(rl.cofonte AS VARCHAR)), TRIM(CAST(rl.coalinea AS VARCHAR))
        ORDER BY valor_total DESC
        LIMIT 10
        """
        
        try:
            dados_top = db_manager.execute_query(query_top_problemas, [ano_atual])
            if dados_top:
                df_top = pd.DataFrame(dados_top)
                print("\n")
                print(df_top.to_string(index=False))
                
                # Verificar se 220000000 + 112101 está na lista
                for item in dados_top:
                    if item['cofonte'] == '220000000' and item['coalinea'] == '112101':
                        print(f"\n⚠️ A combinação 220000000 + 112101 ESTÁ na lista de problemas!")
                        print(f"   Isso indica que ela NÃO está cadastrada corretamente na dimensão.")
                        break
            else:
                print("✅ Nenhuma combinação problemática encontrada")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        # 6. Query de debug final - verificação cruzada
        print("\n6. VERIFICAÇÃO CRUZADA FINAL:")
        print("-" * 60)
        
        query_debug = """
        SELECT 
            'Lançamentos' as origem,
            COUNT(DISTINCT nudocumento) as qtd,
            TRIM(CAST(cofonte AS VARCHAR)) as cofonte_trim,
            TRIM(CAST(coalinea AS VARCHAR)) as coalinea_trim
        FROM receita_lancamento
        WHERE TRIM(CAST(cofonte AS VARCHAR)) = '220000000'
          AND TRIM(CAST(coalinea AS VARCHAR)) = '112101'
          AND coexercicio = ?
        GROUP BY TRIM(CAST(cofonte AS VARCHAR)), TRIM(CAST(coalinea AS VARCHAR))
        
        UNION ALL
        
        SELECT 
            'Dimensão' as origem,
            COUNT(*) as qtd,
            TRIM(CAST(cofonte AS VARCHAR)) as cofonte_trim,
            TRIM(CAST(coalinea AS VARCHAR)) as coalinea_trim
        FROM dim_receita_fonte_conta_contabil
        WHERE TRIM(CAST(cofonte AS VARCHAR)) = '220000000'
          AND TRIM(CAST(coalinea AS VARCHAR)) = '112101'
          AND instatus = 0
        GROUP BY TRIM(CAST(cofonte AS VARCHAR)), TRIM(CAST(coalinea AS VARCHAR))
        """
        
        try:
            dados_debug = db_manager.execute_query(query_debug, [ano_atual])
            if dados_debug:
                print("\nRESULTADO DA VERIFICAÇÃO CRUZADA:")
                for reg in dados_debug:
                    print(f"   {reg['origem']}: {reg['qtd']} registros | Fonte: '{reg['cofonte_trim']}' | Alínea: '{reg['coalinea_trim']}'")
                
                # Verificar se há registros em ambas as tabelas
                tem_lancamento = any(r['origem'] == 'Lançamentos' for r in dados_debug)
                tem_dimensao = any(r['origem'] == 'Dimensão' for r in dados_debug)
                
                if tem_lancamento and not tem_dimensao:
                    print("\n❌ PROBLEMA CONFIRMADO: Existem lançamentos mas NÃO existe na dimensão!")
                elif tem_lancamento and tem_dimensao:
                    print("\n⚠️ INCONSISTÊNCIA: Existe em ambas as tabelas mas ainda aparece como erro.")
                    print("   Possível problema com o campo instatus ou com a lógica da query.")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        print("\n" + "=" * 80)
        print("FIM DO DIAGNÓSTICO")
        print("=" * 80)

if __name__ == "__main__":
    diagnosticar_espacos()