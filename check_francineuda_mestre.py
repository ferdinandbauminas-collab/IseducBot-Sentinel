import json
with open('planejamento_mestre_2026.json', 'r', encoding='utf-8', errors='replace') as f:
    mestre = json.load(f)

print('=== FRANCINEUDA NO MESTRE (todos os dias) ===')
for dia, turmas in mestre.items():
    for turma, slots in turmas.items():
        for slot_idx, info in slots.items():
            if 'FRANCINEUDA' in info.get('teacher', '').upper():
                disc = info.get('discipline', '')
                print(f'{dia} | {turma} | slot {slot_idx} | {disc}')
