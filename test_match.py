import json
import unicodedata
import re
from datetime import datetime, timedelta

def normalize_turma(s):
    if not s: return ""
    s = str(s).upper().strip()
    portal_map = {
        "EMTEJAMARKMODULOIINA": "MOD I A MARK",
        "EMTEJAALTE-MODULO I-N-A": "MOD I A ALT",
        "EMTEJAINFO-MODULO I-N-A": "MOD I A",
        "EMTEJAINFO-MODULO III-N-A": "MOD III A"
    }
    if s in portal_map: return portal_map[s]
    # Se não está no mapa, tenta regex
    m = re.search(r'MODULO\s*([IVX]+)[^A-Z]*([A-Z])', s)
    if m:
        t = f"MOD {m.group(1)} {m.group(2)}"
        if "MARK" in s: t += " MARK"
        if "ALT" in s: t += " ALT"
        return t
    return s

def normalize_teacher(s):
    mapping = {
        "CARMEN SILVIA NUNES DE MOURA SANTOS": "CARMEN",
        "EDNARDO LUIZ AMARANTE DOS SANTOS": "EDNARDO FERREIRA DE SOUSA"
    }
    s = str(s).upper().strip()
    clean = "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    for key, target in mapping.items():
        key_clean = "".join(c for c in unicodedata.normalize('NFD', key.upper()) if unicodedata.category(c) != 'Mn')
        if key_clean in clean: return target
    return s

def normalize_discipline(s):
    if not s in ["LÍNGUA PORTUGUESA", "LÍNGUA INGLESA"]: return s
    return "PORTUGUÊS" if "PORT" in s else "LÍNGUA INGLESA"

def c_s(s, type="general"):
    if type == "turma": s = normalize_turma(s)
    elif type == "teacher": s = normalize_teacher(s)
    elif type == "discipline": s = normalize_discipline(s)
    s = "".join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^A-Z0-9]', '', s)

def map_slot(h_str):
    h = h_str[:2]
    if h == "18": return "1"
    if h in ["13", "14", "15", "16"]: return str(int(h) - 8)
    return None

def test_match():
    h_path = r'c:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\history.json'
    m_path = r'c:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\planejamento_mestre_2026.json'
    
    with open(h_path, 'r', encoding='utf-8', errors='ignore') as f:
        history = json.load(f)
    with open(m_path, 'r', encoding='utf-8', errors='ignore') as f:
        mestre = json.load(f)

    # Pegar metas da Carmen
    print("--- METAS NO MESTRE (CARMEN) ---")
    m_keys = set()
    for day, turmas in mestre.items():
        for t_name, slots in turmas.items():
            for slot_idx, info in slots.items():
                if 'CARMEN' in info['teacher'].upper():
                    t_c = c_s(t_name, "turma")
                    p_c = c_s(info['teacher'], "teacher")
                    d_c = c_s(info['discipline'], "discipline")
                    m_keys.add((p_c, d_c, t_c, day, str(slot_idx)))
                    print(f"MESTRE: {day} | {t_name} | Slot {slot_idx} | {info['discipline']}")
                    print(f"KEY: {p_c} | {d_c} | {t_c} | {slot_idx}")

    print("\n--- LANÇAMENTOS NO PORTAL (CARMEN) ---")
    dias_pt = {4: "SEXTA-FEIRA", 0: "SEGUNDA-FEIRA", 1: "TERÇA-FEIRA", 2: "QUARTA-FEIRA", 3: "QUINTA-FEIRA"}
    for entry in history:
        t_raw = entry.get('turma', '')
        t_c = c_s(t_raw, "turma")
        for l in entry.get('lancamentos', []):
            if 'CARMEN' in l.get('professor', '').upper():
                p_c = c_s(l.get('professor'), "teacher")
                d_c = c_s(l.get('discipline', l.get('componente', '')), "discipline")
                dt_raw = l.get('data', '')
                dt = datetime.strptime(dt_raw, "%d/%m/%Y")
                day_name = dias_pt[dt.weekday()]
                slot = map_slot(l.get('horario', ''))
                
                print(f"\nPORTAL: {dt_raw} ({day_name}) | {t_raw} | {l.get('horario')} | {l.get('professor')}")
                key = (p_c, d_c, t_c, day_name, slot)
                print(f"KEY: {p_c} | {d_c} | {t_c} | {slot}")
                
                if key in m_keys:
                    print(">>> MATCH FOUND! ✅")
                else:
                    print(">>> MATCH FAILED ❌")
                    # Debug why
                    found_any = False
                    for mk in m_keys:
                        if mk[0] == p_c and mk[3] == day_name and mk[4] == slot:
                            found_any = True
                            print(f"Diferença em: {'Turma' if mk[2]!=t_c else ''} {'Disc' if mk[1]!=d_c else ''}")
                            print(f"Mestre esperava: {mk}")

if __name__ == '__main__':
    test_match()
