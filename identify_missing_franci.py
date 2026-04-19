import json, unicodedata, re
from datetime import datetime, timedelta
from collections import defaultdict

def normalize_turma(s):
    if not s: return ''
    s = str(s).upper().strip()
    portal_map = {
        'EMTEJAINFO-MODULO I-N-A': 'MOD I A',
        'EMTEJAINFO-MODULO III-N-A': 'MOD III A',
        'EMTEJAINFO-MODULO III-N-B': 'MOD III B',
        'EMTEJAINFO-MODULO V-N-A': 'MOD V A',
        'EMTEJAINFO-MODULO V-N-B': 'MOD V B',
        'EMTEJAINFO-MODULO V-N-C': 'MOD V C',
        'EMTEJAINFO-MODULO V-N-D': 'MOD V D',
    }
    if s in portal_map: return portal_map[s]
    s_alt = s.replace('EMEJA', 'EMTEJA')
    if s_alt in portal_map: return portal_map[s_alt]
    m = re.search(r'MODULO\s*([IVX]+)[^A-Z]*([A-Z])', s)
    if m:
        t = f'MOD {m.group(1)} {m.group(2)}'
        if 'MARK' in s: t += ' MARK'
        elif 'ALT' in s: t += ' ALT'
        return t
    return s

def map_time_to_slot(time_str):
    if not time_str: return None
    h = time_str[:2]
    if h == '18': return '1'
    if h == '19': return '2'
    if h == '20': return '3'
    if h == '21': return '4'
    if h in ['13', '14', '15', '16']: return str(int(h) - 8)
    return None

dias_semana = {0: 'SEGUNDA-FEIRA', 1: 'TERÇA-FEIRA', 2: 'QUARTA-FEIRA',
               3: 'QUINTA-FEIRA', 4: 'SEXTA-FEIRA', 5: 'SÁBADO', 6: 'DOMINGO'}

with open('history.json', 'r', encoding='utf-8', errors='replace') as f:
    history = json.load(f)

START_DATE = datetime(2026, 2, 19)
today = datetime.now()

# Mapear data -> dia da semana
date_to_weekday = {}
current = START_DATE
while current <= today:
    date_to_weekday[current.strftime('%Y-%m-%d')] = dias_semana.get(current.weekday(), '')
    current += timedelta(days=1)

# Coletar todos os lançamentos da Francineuda (únicos por dia/slot/turma)
franci_slots = defaultdict(set)  # (dia_semana, turma) -> set de slots

for entry in history:
    turma_raw = entry.get('turma', '')
    turma = normalize_turma(turma_raw)
    for l in entry.get('lancamentos', []):
        if 'FRANCINEUDA' not in l.get('professor', '').upper():
            continue
        data = l.get('data', '')
        dt_parts = data.split('/')
        if len(dt_parts) != 3:
            continue
        date_iso = f'{dt_parts[2]}-{dt_parts[1]}-{dt_parts[0]}'
        dia_semana = date_to_weekday.get(date_iso, '')
        if not dia_semana:
            continue
        horario = l.get('horario', '')
        slot = map_time_to_slot(horario)
        if slot and turma and dia_semana not in ['SÁBADO', 'DOMINGO']:
            franci_slots[(dia_semana, turma)].add(slot)

print('=== SLOTS DA FRANCINEUDA CONFIRMADOS PELO HISTÓRICO ===')
print()
dias_ordem = ['SEGUNDA-FEIRA', 'TERÇA-FEIRA', 'QUARTA-FEIRA', 'QUINTA-FEIRA', 'SEXTA-FEIRA']
slot_to_hora = {'1': '18:00', '2': '19:00', '3': '20:00', '4': '21:00'}

for dia in dias_ordem:
    entradas = [(t, s) for (d, t), slots in franci_slots.items() if d == dia for s in sorted(slots)]
    if entradas:
        print(f'{dia}:')
        for turma, slot in sorted(entradas):
            print(f'  {turma} | slot {slot} ({slot_to_hora.get(slot,"?")}) | PORTUGUÊS')
        print()

# Agora comparar com o mestre
with open('planejamento_mestre_2026.json', 'r', encoding='utf-8', errors='replace') as f:
    mestre = json.load(f)

print('=== SLOTS DA FRANCINEUDA NO MESTRE ATUAL ===')
for dia in dias_ordem:
    if dia not in mestre:
        continue
    encontrou = False
    for turma, slots in mestre[dia].items():
        for slot_idx, info in slots.items():
            if 'FRANCINEUDA' in info.get('teacher', '').upper():
                if not encontrou:
                    print(f'{dia}:')
                    encontrou = True
                print(f'  {turma} | slot {slot_idx} ({slot_to_hora.get(slot_idx,"?")}) | {info["discipline"]}')
    if encontrou:
        print()

# Identificar slots ausentes no mestre
print('=== SLOTS AUSENTES NO MESTRE (precisa adicionar) ===')
ausentes = []
for dia in dias_ordem:
    if dia not in mestre:
        continue
    for (d, turma), slots in franci_slots.items():
        if d != dia:
            continue
        for slot in sorted(slots):
            # verificar se existe no mestre
            slots_mestre = mestre[dia].get(turma, {})
            if slot not in slots_mestre or 'FRANCINEUDA' not in slots_mestre[slot].get('teacher', '').upper():
                ausentes.append({'dia': dia, 'turma': turma, 'slot': slot, 'hora': slot_to_hora.get(slot,'?')})
                print(f'FALTANDO: {dia} | {turma} | slot {slot} ({slot_to_hora.get(slot,"?")}) | PORTUGUÊS')

if not ausentes:
    print('Nenhum slot ausente encontrado!')
