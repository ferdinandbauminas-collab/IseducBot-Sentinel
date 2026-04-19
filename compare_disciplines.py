import sys
import os
import json
import unicodedata

# Garantir que o diretório do projeto está no path
sys.path.append(r'C:\Users\ferdi\.gemini\antigravity\scratch\IseducBot')

from dashboard_sentinel import get_mandatory_slots, load_json, HISTORY_FILE, map_time_to_slot

def get_comparison_data():
    mandatory = get_mandatory_slots()
    history = load_json(HISTORY_FILE)
    
    # Mapear slots obrigatórios (Plano)
    # Estrutura: {(data, turma, slot): info}
    plan_map = {}
    for m in mandatory:
        key = (m['date'], m['turma'], m['slot'])
        plan_map[key] = m
    
    results = []
    
    # Percorrer histórico e cruzar com plano
    for entry in history:
        turma_raw = entry.get('turma')
        for lanc in entry.get('lancamentos', []):
            teacher = lanc.get('professor', '')
            # Filtro focado em Gerson para este diagnóstico
            if "GERSON" not in teacher.upper(): continue
            
            dt_raw = lanc.get('data', '').split('/')
            if len(dt_raw) == 3:
                date_iso = f"{dt_raw[2]}-{dt_raw[1]}-{dt_raw[0]}"
                horario = lanc.get('horario', '')
                slot = map_time_to_slot(horario)
                
                # Procurar todas as variações de turma possíveis para o Módulo I
                # (já que a normalização pode estar falhando, tentamos o match manual aqui)
                from dashboard_sentinel import normalize_turma
                t_norm = normalize_turma(turma_raw)
                
                key = (date_iso, t_norm, str(slot))
                if key in plan_map:
                    results.append({
                        "data": date_iso,
                        "turma": t_norm,
                        "slot": slot,
                        "planejamento": plan_map[key]['discipline'],
                        "portal": lanc.get('componente', lanc.get('discipline', '')),
                        "status": "MATCH POSSÍVEL"
                    })
                else:
                    results.append({
                        "data": date_iso,
                        "turma": t_norm,
                        "slot": slot,
                        "planejamento": "NÃO ENCONTRADO",
                        "portal": lanc.get('componente', lanc.get('discipline', '')),
                        "status": "CONFLITO DE TURMA/HORÁRIO"
                    })

    # Unificar por nomes de disciplina
    mappings = {}
    for r in results:
        pair = (r['planejamento'], r['portal'])
        if pair not in mappings: mappings[pair] = 0
        mappings[pair] += 1
        
    print("\n" + "="*80)
    print(f"{'DISCIPLINA NO PLANEJAMENTO':<30} | {'NOME NO PORTAL (ISEDUC)':<40} | OCORRÊNCIAS")
    print("-"*80)
    for (plan, port), count in sorted(mappings.items()):
        print(f"{plan:<30} | {port:<40} | {count}")
    print("="*80 + "\n")

if __name__ == "__main__":
    get_comparison_data()
