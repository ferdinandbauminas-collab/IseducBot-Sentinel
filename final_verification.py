import json

with open('planejamento_mestre_2026.json', 'r', encoding='utf-8', errors='replace') as f:
    mestre = json.load(f)

print('=== HORÁRIO FINAL: ÍTALA RODRIGUES PROBO ===')
for dia, turmas in mestre.items():
    for turma, slots in turmas.items():
        for slot, info in slots.items():
            if 'ITALA' in info.get('teacher', ''):
                print(f'{dia} | {turma} | Slot {slot} | {info.get("discipline")}')

print('\n=== HORÁRIO FINAL: FRANCINEUDA (TERÇA) ===')
if 'TERÇA-FEIRA' in mestre and 'MOD III B' in mestre['TERÇA-FEIRA']:
    slots = mestre['TERÇA-FEIRA']['MOD III B']
    for slot in sorted(slots.keys()):
        if 'FRANCINEUDA' in slots[slot].get('teacher', ''):
             print(f'TERÇA-FEIRA | MOD III B | Slot {slot} | {slots[slot].get("discipline")}')

print('\n=== VERIFICAÇÃO DENILSON (MOD I A) ===')
if 'SEXTA-FEIRA' in mestre and 'MOD I A' in mestre['SEXTA-FEIRA']:
    slots = mestre['SEXTA-FEIRA']['MOD I A']
    if '3' in slots:
        print(f'SEXTA-FEIRA | MOD I A | Slot 3 | Prof: {slots["3"].get("teacher")} | Disc: {slots["3"].get("discipline")}')
