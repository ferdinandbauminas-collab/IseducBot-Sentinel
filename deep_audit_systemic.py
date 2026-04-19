import sys
import os
import json
import unicodedata
import re

# Garantir que o diretório do projeto está no path
sys.path.append(r'C:\Users\ferdi\.gemini\antigravity\scratch\IseducBot')

from dashboard_sentinel import get_mandatory_slots, clean_str, map_time_to_slot, load_json, HISTORY_FILE

def deep_audit_teachers():
    mandatory = get_mandatory_slots()
    history = load_json(HISTORY_FILE)
    
    # 1. Mapear slots obrigatórios
    pending_slots = {}
    for m in mandatory:
        p_clean = clean_str(m['teacher'], type="teacher")
        d_clean = clean_str(m['discipline'], type="discipline")
        t_clean = clean_str(m['turma'], type="turma")
        key = (p_clean, d_clean, t_clean, m['date'])
        if key not in pending_slots: pending_slots[key] = []
        pending_slots[key].append(m['slot'])

    print("\n" + "="*80)
    print("DIAGNÓSTICO SISTÊMICO - PROFESSORES COMpendências")
    print("="*80)

    # 2. Investigar WESLEY (0%)
    print("\n--- FOCO: WESLEY BEZERRA PORTELA FREITAS ---")
    wesley_history = []
    for entry in history:
        t_clean = clean_str(entry.get('turma', ''), type="turma")
        for lanc in entry.get('lancamentos', []):
            p_clean = clean_str(lanc.get('professor', ''), type="teacher")
            if "WESLEY" in p_clean:
                d_clean = clean_str(lanc.get('componente', lanc.get('discipline', '')), type="discipline")
                dt_raw = lanc.get('data', '').split('/')
                if len(dt_raw) == 3:
                    ld = f"{dt_raw[2]}-{dt_raw[1]}-{dt_raw[0]}"
                    wesley_history.append((ld, lanc.get('horario'), d_clean, t_clean))

    for ld, hr, dc, tc in wesley_history[:5]:
        sid = map_time_to_slot(hr)
        key = ("WESLEYBEZERRAPORTELAFREITAS", dc, tc, ld)
        print(f"Histórico: {ld} | {hr} (Slot {sid}) | Disc: {dc} | Turma: {tc}")
        print(f"  -> Buscando Chave no Plano: {key}")
        if key in pending_slots:
            print(f"  -> [OK] Chave existe! Slots pendentes: {pending_slots[key]}")
        else:
            print(f"  -> [FALHA] Chave não existe no Planejamento para este professor!")

    # 3. Investigar GERSON (56.5%)
    print("\n--- FOCO: GERSON DOS SANTOS ---")
    gerson_history = []
    for entry in history:
        t_clean = clean_str(entry.get('turma', ''), type="turma")
        for lanc in entry.get('lancamentos', []):
            p_clean = clean_str(lanc.get('professor', ''), type="teacher")
            if "GERSON" in p_clean:
                d_clean = clean_str(lanc.get('componente', lanc.get('discipline', '')), type="discipline")
                dt_raw = lanc.get('data', '').split('/')
                if len(dt_raw) == 3:
                    ld = f"{dt_raw[2]}-{dt_raw[1]}-{dt_raw[0]}"
                    gerson_history.append((ld, lanc.get('horario'), d_clean, t_clean))

    failure_count = 0
    for ld, hr, dc, tc in gerson_history:
        key = ("GERSONDOSSANTOS", dc, tc, ld)
        if key not in pending_slots:
            failure_count += 1
            if failure_count <= 5:
                print(f"FALHA MATCH GERSON: {ld} | Turma: {tc} | Disc: {dc}")
    print(f"Total de falhas de Match para Gerson: {failure_count}")

if __name__ == "__main__":
    deep_audit_teachers()
