import json, os, sys, unicodedata
from collections import defaultdict
from datetime import datetime, timedelta

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def clean_str(s):
    if not s: return ""
    s = s.upper().strip()
    # Remove acentos
    s = "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    # Remove caracteres especiais e espaços
    for char in ['-', ' ', '.', '_', '(', ')', '/']:
        s = s.replace(char, '')
    return s

# --- TESTE ---
BASE_DIR = os.getcwd() # Ou o caminho absoluto se preferir
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
MESTRE_FILE = os.path.join(BASE_DIR, 'planejamento_mestre_2026.json')

history = load_json(HISTORY_FILE)
mestre = load_json(MESTRE_FILE)

print(f"DEBUG: Itens no historico: {len(history)}")

# Popula mapa do que foi realizado
realized = set()
for entry in history:
    # Simula normalize_turma
    t_raw = entry.get('turma', '').upper().replace('MODULO', 'MOD').replace('-', ' ').strip()
    if 'MOD III N A' in t_raw: t_raw = 'MOD III A'
    
    t_clean = clean_str(t_raw)
    
    for lanc in entry.get('lancamentos', []):
        prof = clean_str(lanc.get('professor', ''))
        disc = clean_str(lanc.get('disciplina', lanc.get('componente', '')))
        d, m, y = lanc.get('data', '').split('/')
        date = f"{y}-{m}-{d}"
        
        key = (prof, disc, t_clean, date)
        realized.add(key)
        if "DANIEL" in prof:
             print(f"MATCH REALIZADO: {key}")

# Verifica um exemplo mandatorio (sexta 20/02)
# No mestre: MOD III A -> DANIEL MAGALHAES CHAVES / FILOSOFIA
prof_m = clean_str("DANIEL MAGALHAES CHAVES")
disc_m = clean_str("FILOSOFIA")
turma_m = clean_str("MOD III A")
date_m = "2026-02-20"
key_m = (prof_m, disc_m, turma_m, date_m)

print(f"\nCHAVE BUSCADA (Mestre): {key_m}")
if key_m in realized:
    print(">>> SUCESSO! CHAVE ENCONTRADA!")
else:
    print(">>> FALHA! CHAVE NAO ENCONTRADA!")
    # Mostra parecidos
    for r in realized:
        if r[0] == prof_m and r[3] == date_m:
             print(f"Sugerido no historico: {r}")
