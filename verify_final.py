import sys
import os

# Garantir que o diretório do projeto está no path
sys.path.append(r'C:\Users\ferdi\.gemini\antigravity\scratch\IseducBot')

try:
    from dashboard_sentinel import get_compliance_stats
    
    stats, count, global_eff = get_compliance_stats()
    
    teachers_to_check = ["FRANCINEUDA DA SILVA SOUSA", "GERSON DOS SANTOS", "WESLEY BEZERRA PORTELA FREITAS"]
    
    print("\n" + "="*50)
    print("RELATÓRIO DE CONFORMIDADE FINAL")
    print("="*50)
    
    total_global_done = 0
    total_global_req = 0

    for t in teachers_to_check:
        if t in stats:
            data = stats[t]
            total_global_done += data['done']
            total_global_req += data['total']
            perc = (data['done'] / data['total'] * 100) if data['total'] > 0 else 0
            print(f"PROFESSOR: {t:30} | {data['done']:>3}/{data['total']:>3} | {perc:>6.1f}%")
            if data['gaps']:
                print(f"  -> {len(data['gaps'])} LACUNAS RESTANTES (visualize na Dashboard)")
        else:
            print(f"PROFESSOR: {t:30} | NÃO ENCONTRADO NO SISTEMA")
            
    global_perc = (total_global_done / total_global_req * 100) if total_global_req > 0 else 0
    print("="*50)
    print(f"MÉDIA GERAL DE CONFORMIDADE DA ESCOLA: {global_perc:>6.1f}%")
    print(f"TOTAL DE AULAS AUDITADAS: {count}")
    print("="*50 + "\n")

except Exception as e:
    print(f"Erro ao gerar conformidade: {e}")
