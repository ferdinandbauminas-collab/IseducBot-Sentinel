import json
import os
import unicodedata
import re
from datetime import datetime, timedelta

HISTORY_FILE = r'C:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\history.json'
MESTRE_FILE = r'C:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\planejamento_mestre_2026.json'

def load_json(p):
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            return json.load(f)
    return {}

def clean_str(s):
    if not s: return ""
    s = "".join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^A-Z0-9]', '', s)

def audit_gerson():
    mestre = load_json(MESTRE_FILE)
    history = load_json(HISTORY_FILE)
    
    print("--- 1. ALOCAÇÕES NO PLANEJAMENTO MESTRE ---")
    gerson_plan = []
    for day, turmas in mestre.items():
        for turma, slots in turmas.items():
            for slot, info in slots.items():
                if "GERSON" in info.get('teacher', '').upper():
                    gerson_plan.append((day, turma, slot, info.get('discipline')))
                    print(f"{day} | {turma} | Slot {slot} | {info.get('discipline')}")
    
    print("\n--- 2. REGISTROS NO HISTÓRICO (PORTAL) ---")
    gerson_hist = []
    for entry in history:
        t_raw = entry.get('turma')
        for l in entry.get('lancamentos', []):
            if "GERSON" in l.get('professor', '').upper():
                gerson_hist.append((l.get('data'), l.get('horario'), l.get('componente'), t_raw))
                print(f"{l.get('data')} | {l.get('horario')} | {l.get('componente')} | {t_raw}")

if __name__ == "__main__":
    audit_gerson()
