import json
import unicodedata
import re
from datetime import datetime

# Simulação da lógica do Dashboard v4.9
def normalize_teacher(s):
    mapping = {
        "ALEXSANDRA MARIA LINARD PAES LANDIM RIBAMAR": "ALEXSANDRA MARIA LINARD PAES LANDIM",
        "FRANCISCO DAS CHAGAS MENDES DA SILVA JUNIOR": "FRANCISCO JR",
        "ELLYDA FERNANDA DE SOUSA OLIVEIRA": "ELLYDA",
        "JARBAS FERNANDES DE OLIVEIRA": "JARBAS",
        "JOANA DARC DE SOUSA CARDOSO": "JOANA DARC",
        "SALOMAO DA SILVA FERREIRA": "SALOMÃO",
        "CARMEN SILVIA NUNES DE MOURA SANTOS": "CARMEN",
        "EDNARDO LUIZ AMARANTE DOS SANTOS": "EDNARDO FERREIRA DE SOUSA",
        "LINDELVÂNIA DE SOUSA ALMEIDA": "LINDELVÂNIA"
    }
    s = str(s).upper().strip()
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
        "FUNDAMENTOS DA ADMINISTRAÇÃO": "FDA"
    }
    for key, sigla in mapping.items():
        if key in s: return sigla
    return s

def clean_str(s, type="general"):
    if not s: return ""
    if type == "teacher": s = normalize_teacher(s)
    elif type == "discipline": s = normalize_discipline(s)
    # Note: excluding "turma" for simplicity in this debug
    s = "".join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^A-Z0-9]', '', s)

def debug():
    h_path = r'c:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\history.json'
    m_path = r'c:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\planejamento_mestre_2026.json'
    
    with open(h_path, 'r', encoding='utf-8', errors='ignore') as f:
        history = json.load(f)
    with open(m_path, 'r', encoding='utf-8', errors='ignore') as f:
        mestre = json.load(f)
        
    print("--- DEBUG AUDIT: CARMEN ---")
    carmen_found = False
    for entry in history:
        t_raw = entry.get('turma', '')
        t_clean = c_s_simple(t_raw)
        for l in entry.get('lancamentos', []):
            prof = l.get('professor', '')
            if 'CARMEN' in prof.upper():
                carmen_found = True
                p_clean = clean_str(prof, type="teacher")
                disc = l.get('discipline', l.get('componente', ''))
                d_clean = clean_str(disc, type="discipline")
                date_raw = l.get('data', '')
                dt = date_raw.split('/')
                date_iso = f"{dt[2]}-{dt[1]}-{dt[0]}" if len(dt)==3 else ""
                
                print(f"\nPORTAL REC: {date_raw} | {t_raw} | {prof} | {disc}")
                print(f"KEYS PORTAL: Prof={p_clean}, Disc={d_clean}, Turma={t_clean}, Date={date_iso}")
                
                # Check if this matches anything in Mestre for this date
                # (Conceptual check)
                
    if not carmen_found:
        print("Nenhum registro da CARMEN no history.json")

def c_s_simple(s):
    return re.sub(r'[^A-Z0-9]', '', "".join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn'))

if __name__ == '__main__':
    debug()
