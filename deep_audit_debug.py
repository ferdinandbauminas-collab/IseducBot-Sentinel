
import json
import os
import unicodedata
import re
from datetime import datetime, timedelta
from collections import defaultdict

# --- PATHS ---
BASE_DIR = r"C:\Users\ferdi\.gemini\antigravity\scratch\IseducBot"
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
MESTRE_FILE = os.path.join(BASE_DIR, 'planejamento_mestre_2026.json')
CALENDARIO_FILE = os.path.join(BASE_DIR, 'calendario_letivo_2026.json')
START_DATE = datetime(2026, 2, 19)

def load_json(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return json.load(f)

# COPY LOGIC FROM dashboard_sentinel.py
def normalize_turma(s):
    if not s: return ""
    s = str(s).upper().strip()
    portal_map = {
        "EMTEJAMARKMODULOIINA": "MOD I A MARK",
        "EMTEJAMARK-DIG-MODULO I-N-A": "MOD I A MARK",
        "EMTEJAALTE-MODULO I-N-A": "MOD I A ALT",
        "EMTEJAINFO-MODULO I-N-A": "MOD I A",
        "EMTEJAINFO-MODULO III-N-A": "MOD III A",
        "EMTEJAINFO-MODULO III-N-B": "MOD III B",
        "EMTEJAINFO-MODULO V-N-A": "MOD V A",
        "EMTEJAINFO-MODULO V-N-B": "MOD V B",
        "EMTEJAINFO-MODULO V-N-C": "MOD V C",
        "EMTEJAINFO-MODULO V-N-D": "MOD V D",
        "MÓDULO INFO IA": "MOD I A",
        "MÓDULO MARK IA": "MOD I A MARK",
        "MÓDULO ALTE IA": "MOD I A ALT"
    }
    if s in portal_map: return portal_map[s]
    s_alt = s.replace("EMEJA", "EMTEJA")
    if s_alt in portal_map: return portal_map[s_alt]
    m = re.search(r'MODULO\s*([IVX]+)[^A-Z]*([A-Z])', s)
    if m:
        t = f"MOD {m.group(1)} {m.group(2)}"
        if "MARK" in s: t += " MARK"
        elif "ALT" in s: t += " ALT"
        return t
    return s

def normalize_teacher(s):
    if not s: return ""
    s = str(s).upper().strip()
    mapping = {
        "FRANCINEUDA DA SILVA SOUSA": "FRANCINEUDA DA SILVA SOUSA"
    }
    name_clean = "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    for key, target in mapping.items():
        key_clean = "".join(c for c in unicodedata.normalize('NFD', key.upper()) if unicodedata.category(c) != 'Mn')
        if key_clean in name_clean or name_clean in key_clean:
            return target
    return s

def normalize_discipline(s):
    if not s: return ""
    s = str(s).upper().strip()
    mapping = {
        "PROJETO DE APRENDIZAGEM INTERDISCIPLINAR": "PAI",
        "PROJETO DE DESENVOLVIMENTO DE SISTEMAS": "PDS",
        "EMPREENDEDORISMO PARA TI": "EMP. TI",
        "EMPREENDEDORISMO PARA TECNOLOGIA DA INFORMAÇÃO": "EMP. TI",
        "REDES DE COMPUTADORES": "REDES",
        "BANCO DE DADOS": "BD",
        "PROGRAMAÇÃO PARA COMPUTADORES": "PROG. COMP",
        "INGLÊS INSTRUMENTAL": "INGLÊS INST.",
        "LÍNGUA PORTUGUESA": "PORTUGUÊS",
        "FUNDAMENTOS DA ADMINISTRAÇÃO": "FDA",
        "ED. FISICA A": "ED. FÍSICA",
        "ED. FÍSICA A": "ED. FÍSICA",
        "EDUCAÇÃO FÍSICA": "ED. FÍSICA"
    }
    for key, sigla in mapping.items():
        if key in s: return sigla
    if any(x in s for x in ["PORTUGUÊS", "LÍNGUA PORTUGUESA", "LINGUA PORTUGUESA"]): return "PORTUGUÊS"
    return s

def clean_str(s, type="general"):
    if not s: return ""
    if type == "turma": s = normalize_turma(s)
    elif type == "teacher": s = normalize_teacher(s)
    elif type == "discipline": s = normalize_discipline(s)
    s = "".join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^A-Z0-9]', '', s)

def map_time_to_slot(time_str):
    if not time_str: return None
    h = time_str[:2]
    if h == "18": return "1"
    if h == "19": return "2"
    if h == "20": return "3"
    if h == "21": return "4"
    return None

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
                        mandatory.append({"date": date_str, "turma": turma, "slot": str(slot_idx), "teacher": info['teacher'], "discipline": info['discipline']})
        current += timedelta(days=1)
    return mandatory

def deep_audit():
    mandatory = get_mandatory_slots()
    history = load_json(HISTORY_FILE)
    
    realized_slots = set()
    pending_slots = defaultdict(list)
    
    # 1. Map mandatory
    print("--- SLOTS MANDATÓRIOS (PENDING_SLOTS) ---")
    for m in mandatory:
        p_clean = clean_str(m['teacher'], type="teacher")
        d_clean = clean_str(m['discipline'], type="discipline")
        t_clean = clean_str(m['turma'], type="turma")
        key = (p_clean, d_clean, t_clean, m['date'])
        pending_slots[key].append(m['slot'])
        if "2026-03-24" in m['date']:
            print(f"Key: {key} | Slot: {m['slot']}")

    # 2. Extract unique history
    unique_history_entries = set()
    for entry in history:
        t_clean = clean_str(entry.get('turma', ''), type="turma")
        for lanc in entry.get('lancamentos', []):
            p_clean = clean_str(lanc.get('professor', ''), type="teacher")
            d_clean = clean_str(lanc.get('discipline', lanc.get('componente', '')), type="discipline")
            dt_raw = lanc.get('data', '').split('/')
            if len(dt_raw) == 3:
                lesson_date = f"{dt_raw[2]}-{dt_raw[1]}-{dt_raw[0]}"
                horario = lanc.get('horario', '')
                if "FRANCINEUDA" in p_clean and "2026-03-24" in lesson_date:
                    print(f"HISTORY: Turma:{t_clean} Data:{lesson_date} Hora:{horario} Prof:{p_clean} Disc:{d_clean}")
                unique_history_entries.add((t_clean, lesson_date, horario, p_clean, d_clean))

    # 3. Match
    print("\n--- MATCHING PROCESS ---")
    for t_clean, lesson_date, horario, p_clean, d_clean in unique_history_entries:
        slot_id = map_time_to_slot(horario)
        day_key = (p_clean, d_clean, t_clean, lesson_date)
        
        if "FRANCINEUDA" in p_clean and "2026-03-24" in lesson_date:
            print(f"Tentando match para {day_key} no slot {slot_id}")
            if day_key in pending_slots:
                print(f"  Encontrado no pending_slots! Slots disponíveis: {pending_slots[day_key]}")
            else:
                print(f"  NÃO encontrado no pending_slots.")
        
        if slot_id and slot_id in pending_slots[day_key]:
            realized_slots.add((p_clean, d_clean, t_clean, lesson_date, slot_id))
            pending_slots[day_key].remove(slot_id)
            if "FRANCINEUDA" in p_clean and "2026-03-24" in lesson_date:
                print(f"  ✅ MATCH SUCESSO! Realized: {(p_clean, d_clean, t_clean, lesson_date, slot_id)}")
        elif pending_slots[day_key]:
            any_slot = pending_slots[day_key].pop(0)
            realized_slots.add((p_clean, d_clean, t_clean, lesson_date, any_slot))
            if "FRANCINEUDA" in p_clean and "2026-03-24" in lesson_date:
                print(f"  ✅ MATCH FLEXÍVEL! Slot {any_slot} consumido.")

if __name__ == "__main__":
    deep_audit()
