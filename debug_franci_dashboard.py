
import json
import os
import unicodedata
import re
from datetime import datetime, timedelta
from collections import defaultdict

# --- CONFIGURAÇÃO ---
BASE_DIR = r"C:\Users\ferdi\.gemini\antigravity\scratch\IseducBot"
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
MESTRE_FILE = os.path.join(BASE_DIR, 'planejamento_mestre_2026.json')
CALENDARIO_FILE = os.path.join(BASE_DIR, 'calendario_letivo_2026.json')
START_DATE = datetime(2026, 2, 19)

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_str(s):
    if not s: return ""
    s = "".join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^A-Z0-9]', '', s)

def normalize_teacher(s):
    # Simplified version for debug
    if "FRANCINEUDA" in s.upper(): return "FRANCINEUDA DA SILVA SOUSA"
    return s.upper()

def get_mandatory_slots():
    mestre = load_json(MESTRE_FILE)
    cal_data = load_json(CALENDARIO_FILE)
    sabados = cal_data.get("SABADOS_LETIVOS_2026", {})
    feriados = cal_data.get("FERIADOS_2026", [])
    today = datetime.now()
    current = START_DATE
    mandatory = []
    dias_map = {0: "SEGUNDA-FEIRA", 1: "TERÇA-FEIRA", 2: "QUARTA-FEIRA", 3: "QUINTA-FEIRA", 4: "SEXTA-FEIRA"}
    
    while current <= today:
        date_str = current.strftime("%Y-%m-%d")
        if date_str in feriados:
            current += timedelta(days=1)
            continue
        
        day_type = sabados.get(date_str) or dias_map.get(current.weekday())
        
        if day_type and day_type in mestre:
            for turma, slots in mestre[day_type].items():
                for slot_idx, info in slots.items():
                    if "FRANCINEUDA" in info['teacher'].upper():
                        mandatory.append({
                            "date": date_str, 
                            "turma": turma, 
                            "slot": str(slot_idx), 
                            "teacher": info['teacher'], 
                            "discipline": info['discipline'],
                            "day_type": day_type
                        })
        current += timedelta(days=1)
    return mandatory

def debug_franci():
    mandatory = get_mandatory_slots()
    history = load_json(HISTORY_FILE)
    
    print(f"--- DEBUG FRANCINEUDA ---")
    print(f"Total de aulas esperadas até hoje: {len(mandatory)}")
    
    # Datas de interesse
    target_dates = ["2026-03-24", "2026-03-31", "2026-04-07", "2026-03-07", "2026-03-28"]
    
    print("\n[ESPERADO] Slots planejados para as datas críticas:")
    for m in mandatory:
        if m['date'] in target_dates:
            print(f"Data: {m['date']} ({m['day_type']}) | Turma: {m['turma']} | Slot: {m['slot']} | Disciplina: {m['discipline']}")

    print("\n[REALIZADO] Lançamentos encontrados no history.json para Francineuda nessas datas:")
    found_any = False
    for entry in history:
        for lanc in entry.get('lancamentos', []):
            if "FRANCINEUDA" in lanc.get('professor', '').upper():
                dt = lanc.get('data', '')
                try:
                    dt_iso = datetime.strptime(dt, "%d/%m/%Y").strftime("%Y-%m-%d")
                    if dt_iso in target_dates:
                        print(f"Data no Portal: {dt} | Turma: {entry.get('turma')} | Horário: {lanc.get('horario')} | Disciplina: {lanc.get('componente')}")
                        found_any = True
                except: pass
    
    if not found_any:
        print("Nenhum lançamento encontrado para estas datas no history.json.")

if __name__ == "__main__":
    debug_franci()
