import json

with open('planejamento_mestre_2026.json', 'r', encoding='utf-8', errors='replace') as f:
    mestre = json.load(f)

print('=== PESQUISA PAI EM MOD III A ===')
for dia, turmas in mestre.items():
    if 'MOD III A' in turmas:
        for slot, info in turmas['MOD III A'].items():
            if 'PAI' in info.get('discipline', '').upper() or 'PROJETO' in info.get('discipline', '').upper():
                print(f'{dia} | Slot {slot} | Prof: {info.get("teacher")} | Disc: {info.get("discipline")}')

print('\n=== PESQUISA ELETIVA (TODOS PROFESSORES) ===')
for dia, turmas in mestre.items():
    for turma, slots in turmas.items():
        for slot, info in slots.items():
            if 'ELETIVA' in info.get('discipline', '').upper():
                 print(f'{dia} | {turma} | Slot {slot} | Prof: {info.get("teacher")} | Disc: {info.get("discipline")}')
