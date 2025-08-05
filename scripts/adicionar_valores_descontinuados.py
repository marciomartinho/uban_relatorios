#!/usr/bin/env python3
"""
Script para adicionar valores descontinuados de 2024 nas tabelas dimensão
Resolve problemas de integridade para dados históricos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
from pathlib import Path
from datetime import datetime

def adicionar_valores_descontinuados():
    """Adiciona eventos e contas descontinuados nas tabelas dimensão"""
    
    # Caminho do banco
    db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
    
    print("=" * 80)
    print("ADIÇÃO DE VALORES DESCONTINUADOS (2024) NAS DIMENSÕES")
    print("=" * 80)
    print(f"Banco de dados: {db_path}")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Verificar se o banco existe
    if not db_path.exists():
        print(f"❌ ERRO: Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        # Conectar ao banco
        conn = duckdb.connect(str(db_path))
        
        # Valores a adicionar
        eventos_descontinuados = [
            (800281, 'EVENTO 2024 - DESCONTINUADO'),
            (805281, 'EVENTO 2024 - DESCONTINUADO')
        ]
        
        contas_descontinuadas = [
            ('621340199', 'CONTA 2024 - DESCONTINUADA'),
            ('621340101', 'CONTA 2024 - DESCONTINUADA')
        ]
        
        print("📋 VALORES A SEREM ADICIONADOS:")
        print("\nEventos:")
        for evento, descricao in eventos_descontinuados:
            print(f"   - {evento}: {descricao}")
        
        print("\nContas Contábeis:")
        for conta, descricao in contas_descontinuadas:
            print(f"   - {conta}: {descricao}")
        
        print("\n" + "-" * 60)
        
        # Verificar se as tabelas dimensão existem
        print("\n🔍 Verificando tabelas dimensão...")
        
        # Verificar dim_evento
        evento_exists = conn.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'dim_evento'
        """).fetchone()[0] > 0
        
        if not evento_exists:
            print("❌ Tabela dim_evento não encontrada!")
        else:
            print("✅ Tabela dim_evento encontrada")
        
        # Verificar dim_conta_contabil
        conta_exists = conn.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'dim_conta_contabil'
        """).fetchone()[0] > 0
        
        if not conta_exists:
            print("❌ Tabela dim_conta_contabil não encontrada!")
        else:
            print("✅ Tabela dim_conta_contabil encontrada")
        
        if not evento_exists or not conta_exists:
            print("\n❌ Tabelas dimensão necessárias não encontradas!")
            return False
        
        # Confirmar inserção
        print("\n" + "=" * 60)
        print("⚠️  ATENÇÃO: Esta operação irá adicionar registros nas tabelas:")
        print("   - dim_evento (2 registros)")
        print("   - dim_conta_contabil (2 registros)")
        print("=" * 60)
        
        resposta = input("\n❓ Confirma a inserção? (s/N): ")
        if resposta.lower() != 's':
            print("\n❌ Operação cancelada.")
            return False
        
        # Inserir eventos
        print("\n📝 Inserindo eventos descontinuados...")
        eventos_inseridos = 0
        eventos_existentes = 0
        
        for coevento, noevento in eventos_descontinuados:
            try:
                # Verificar se já existe
                existe = conn.execute(
                    "SELECT COUNT(*) FROM dim_evento WHERE coevento = ?", 
                    [coevento]
                ).fetchone()[0] > 0
                
                if existe:
                    print(f"   ⚠️ Evento {coevento} já existe - pulando")
                    eventos_existentes += 1
                else:
                    # Inserir
                    conn.execute(
                        "INSERT INTO dim_evento (coevento, noevento) VALUES (?, ?)",
                        [coevento, noevento]
                    )
                    print(f"   ✅ Evento {coevento} inserido com sucesso")
                    eventos_inseridos += 1
                    
            except Exception as e:
                print(f"   ❌ Erro ao inserir evento {coevento}: {e}")
        
        # Inserir contas contábeis
        print("\n📝 Inserindo contas contábeis descontinuadas...")
        contas_inseridas = 0
        contas_existentes = 0
        
        for cocontacontabil, nocontacontabil in contas_descontinuadas:
            try:
                # Verificar se já existe
                existe = conn.execute(
                    "SELECT COUNT(*) FROM dim_conta_contabil WHERE cocontacontabil = ?", 
                    [cocontacontabil]
                ).fetchone()[0] > 0
                
                if existe:
                    print(f"   ⚠️ Conta {cocontacontabil} já existe - pulando")
                    contas_existentes += 1
                else:
                    # Inserir
                    conn.execute(
                        "INSERT INTO dim_conta_contabil (cocontacontabil, nocontacontabil) VALUES (?, ?)",
                        [cocontacontabil, nocontacontabil]
                    )
                    print(f"   ✅ Conta {cocontacontabil} inserida com sucesso")
                    contas_inseridas += 1
                    
            except Exception as e:
                print(f"   ❌ Erro ao inserir conta {cocontacontabil}: {e}")
        
        # Resumo da operação
        print("\n" + "=" * 60)
        print("RESUMO DA OPERAÇÃO")
        print("=" * 60)
        print(f"Eventos:")
        print(f"   - Inseridos: {eventos_inseridos}")
        print(f"   - Já existentes: {eventos_existentes}")
        print(f"\nContas Contábeis:")
        print(f"   - Inseridas: {contas_inseridas}")
        print(f"   - Já existentes: {contas_existentes}")
        
        # Verificar integridade após inserção
        if eventos_inseridos > 0 or contas_inseridas > 0:
            print("\n🔍 Verificando se os problemas de integridade foram resolvidos...")
            
            # Verificar eventos órfãos
            orfaos_eventos = conn.execute("""
                SELECT COUNT(DISTINCT f.coevento)
                FROM receita_lancamento f
                LEFT JOIN dim_evento d ON f.coevento = d.coevento
                WHERE f.coevento IN (800281, 805281)
                AND d.coevento IS NULL
            """).fetchone()[0]
            
            # Verificar contas órfãs
            orfaos_contas = conn.execute("""
                SELECT COUNT(DISTINCT f.cocontacontabil)
                FROM receita_lancamento f
                LEFT JOIN dim_conta_contabil d ON f.cocontacontabil = d.cocontacontabil
                WHERE f.cocontacontabil IN ('621340199', '621340101')
                AND d.cocontacontabil IS NULL
            """).fetchone()[0]
            
            print(f"\nEventos órfãos restantes: {orfaos_eventos}")
            print(f"Contas órfãs restantes: {orfaos_contas}")
            
            if orfaos_eventos == 0 and orfaos_contas == 0:
                print("\n✅ SUCESSO! Todos os problemas de integridade foram resolvidos!")
            else:
                print("\n⚠️ Ainda existem valores órfãos. Verifique o relatório de integridade.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante a operação: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("\n🔧 ADIÇÃO DE VALORES DESCONTINUADOS")
    print("Este script adiciona eventos e contas de 2024 que foram")
    print("descontinuados em 2025 para resolver problemas de integridade\n")
    
    if adicionar_valores_descontinuados():
        print("\n🎉 Operação concluída!")
        print("\n📌 Próximos passos:")
        print("   1. Execute novamente a verificação de integridade:")
        print("      python scripts/verificar_integridade_duckdb.py")
        print("   2. Os valores órfãos devem ter sido resolvidos")
        print("\n💡 Nota: Os registros foram marcados como 'DESCONTINUADO'")
        print("   para facilitar identificação futura")
    else:
        print("\n❌ Operação falhou ou foi cancelada.")

if __name__ == "__main__":
    main()