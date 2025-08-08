"""
Script para debugar documentos específicos que estão aparecendo como inconsistência
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db_manager import db_manager
from app import create_app

def verificar_documentos():
    """Verifica os 3 documentos que estão aparecendo na tela"""
    
    app = create_app()
    
    with app.app_context():
        print("\n" + "=" * 80)
        print("VERIFICAÇÃO DOS DOCUMENTOS QUE APARECEM COMO INCONSISTÊNCIA")
        print("=" * 80)
        
        # Documentos para verificar
        documentos = [
            {'nudocumento': '2025NL00819', 'cougcontab': '220201', 'cofonte': '220000000', 'coalinea': '112101'},
            {'nudocumento': '2025NL00572', 'cougcontab': '130101', 'cofonte': '100100000', 'coalinea': '121552'},
            {'nudocumento': '2025OB00009', 'cougcontab': '320203', 'cofonte': '266000000', 'coalinea': '121501'}
        ]
        
        for doc in documentos:
            print(f"\n{'='*60}")
            print(f"DOCUMENTO: {doc['nudocumento']}")
            print(f"{'='*60}")
            print(f"  UG Contábil (cougcontab): {doc['cougcontab']}")
            print(f"  Fonte: {doc['cofonte']}")
            print(f"  Alínea: {doc['coalinea']}")
            print()
            
            # 1. Verificar se existe na dimensão
            print("1. VERIFICANDO NA DIMENSÃO (dim_receita_fonte_conta_contabil):")
            print("-" * 40)
            
            query_dimensao = """
            SELECT 
                cofonte,
                coalinea,
                instatus,
                COUNT(*) as qtd
            FROM dim_receita_fonte_conta_contabil
            WHERE TRIM(CAST(cofonte AS VARCHAR)) = TRIM(CAST(? AS VARCHAR))
              AND TRIM(CAST(coalinea AS VARCHAR)) = TRIM(CAST(? AS VARCHAR))
            GROUP BY cofonte, coalinea, instatus
            """
            
            try:
                resultado_dim = db_manager.execute_query(query_dimensao, [doc['cofonte'], doc['coalinea']])
                
                if resultado_dim:
                    for reg in resultado_dim:
                        print(f"   ✅ ENCONTRADO na dimensão:")
                        print(f"      Status (instatus): {reg['instatus']}")
                        print(f"      Quantidade: {reg['qtd']}")
                        if reg['instatus'] == 0:
                            print(f"      ➡️ ATIVO - NÃO deveria aparecer como inconsistência!")
                        else:
                            print(f"      ➡️ INATIVO - pode aparecer como inconsistência")
                else:
                    print(f"   ❌ NÃO encontrado na dimensão")
                    print(f"      ➡️ Deve verificar saldo para decidir se é inconsistência")
                    
            except Exception as e:
                print(f"   Erro: {e}")
            
            # 2. Verificar saldo na receita_saldo
            print("\n2. VERIFICANDO SALDO NA RECEITA_SALDO:")
            print("-" * 40)
            print(f"   Buscando na UG (coug): {doc['cougcontab']}")
            print(f"   Padrão conta corrente: {doc['coalinea']}XX{doc['cofonte']}")
            print()
            
            # Query para verificar todas as 100 combinações
            saldos_encontrados = []
            
            for i in range(100):
                variacao = str(i).zfill(2)
                conta_corrente = f"{doc['coalinea']}{variacao}{doc['cofonte']}"
                
                query_saldo = """
                SELECT 
                    cocontacontabil,
                    coug,
                    cocontacorrente,
                    SUM(saldo_contabil_receita) as saldo_total,
                    COUNT(*) as qtd_registros
                FROM receita_saldo
                WHERE cocontacontabil = '621200000'
                  AND CAST(coug AS VARCHAR) = CAST(? AS VARCHAR)
                  AND CAST(cocontacorrente AS VARCHAR) = CAST(? AS VARCHAR)
                  AND saldo_contabil_receita IS NOT NULL
                  AND saldo_contabil_receita != 0
                GROUP BY cocontacontabil, coug, cocontacorrente
                """
                
                try:
                    resultado_saldo = db_manager.execute_query(query_saldo, [doc['cougcontab'], conta_corrente])
                    
                    if resultado_saldo and resultado_saldo[0]['saldo_total']:
                        saldo = resultado_saldo[0]['saldo_total']
                        qtd = resultado_saldo[0]['qtd_registros']
                        
                        saldos_encontrados.append({
                            'variacao': variacao,
                            'conta_corrente': conta_corrente,
                            'saldo': saldo,
                            'qtd': qtd,
                            'coug': resultado_saldo[0]['coug']
                        })
                except:
                    pass
            
            if saldos_encontrados:
                print(f"   ⚠️ SALDO ENCONTRADO em {len(saldos_encontrados)} variação(ões):")
                total_saldo = 0
                for s in saldos_encontrados:
                    print(f"      Var {s['variacao']}: {s['conta_corrente']}")
                    print(f"         UG (coug): {s['coug']}")
                    print(f"         Saldo: R$ {s['saldo']:,.2f}")
                    print(f"         Registros: {s['qtd']}")
                    total_saldo += s['saldo']
                
                print(f"\n   TOTAL SALDO: R$ {total_saldo:,.2f}")
                print(f"   ➡️ TEM SALDO - deve aparecer como inconsistência!")
            else:
                print(f"   ✅ NENHUM SALDO encontrado na UG {doc['cougcontab']}")
                print(f"   ➡️ SEM SALDO - NÃO deveria aparecer como inconsistência!")
            
            # 3. Verificar com a query do sistema (usando SUBSTRING)
            print("\n3. TESTANDO QUERY DO SISTEMA (SUBSTRING):")
            print("-" * 40)
            
            query_sistema = """
            SELECT COUNT(*) as total
            FROM receita_saldo rs
            WHERE rs.cocontacontabil = '621200000'
              AND CAST(rs.coug AS VARCHAR) = CAST(? AS VARCHAR)
              AND rs.saldo_contabil_receita IS NOT NULL
              AND rs.saldo_contabil_receita != 0
              AND LENGTH(CAST(rs.cocontacorrente AS VARCHAR)) = 17
              AND SUBSTRING(CAST(rs.cocontacorrente AS VARCHAR), 1, 6) = CAST(? AS VARCHAR)
              AND SUBSTRING(CAST(rs.cocontacorrente AS VARCHAR), 9, 9) = CAST(? AS VARCHAR)
            """
            
            try:
                resultado_sistema = db_manager.execute_query(query_sistema, 
                    [doc['cougcontab'], doc['coalinea'], doc['cofonte']])
                
                total = resultado_sistema[0]['total'] if resultado_sistema else 0
                
                print(f"   Query do sistema encontrou: {total} registros")
                
                if total > 0:
                    print(f"   ➡️ Sistema considera que TEM SALDO")
                else:
                    print(f"   ➡️ Sistema considera que NÃO TEM SALDO")
                    
            except Exception as e:
                print(f"   Erro: {e}")
            
            # 4. Conclusão para este documento
            print(f"\n4. CONCLUSÃO PARA {doc['nudocumento']}:")
            print("-" * 40)
            
            tem_na_dimensao_ativa = False
            tem_saldo = len(saldos_encontrados) > 0
            
            # Verificar se tem na dimensão ativa
            if resultado_dim:
                for reg in resultado_dim:
                    if reg['instatus'] == 0:
                        tem_na_dimensao_ativa = True
                        break
            
            if tem_na_dimensao_ativa:
                print(f"   ❌ ERRO: Está na dimensão ATIVA (instatus=0)")
                print(f"      NÃO deveria aparecer como inconsistência!")
            elif tem_saldo:
                print(f"   ✅ CORRETO: Não está na dimensão ativa E tem saldo")
                print(f"      DEVE aparecer como inconsistência!")
            else:
                print(f"   ❌ ERRO: Não está na dimensão ativa E não tem saldo")
                print(f"      NÃO deveria aparecer como inconsistência!")
        
        print("\n" + "=" * 80)
        print("FIM DA VERIFICAÇÃO")
        print("=" * 80)

if __name__ == "__main__":
    verificar_documentos()