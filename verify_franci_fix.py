import json

with open('planejamento_mestre_2026.json', 'r', encoding='utf-8') as f:
    mestre = json.load(f)

slot_to_hora = {'1': '18:00', '2': '19:00', '3': '20:00', '4': '21:00'}

terca_key = None
for k in mestre.keys():
    if 'TER' in k.upper() and 'FEIRA' in k.upper():
        terca_key = k
        break

print('VERIFICACAO - TERCA | MOD III B:')
for slot_idx in sorted(mestre[terca_key]['MOD III B'].keys()):
    info = mestre[terca_key]['MOD III B'][slot_idx]
    hora = slot_to_hora.get(slot_idx, '?')
    print(f'  slot {slot_idx} ({hora}) | {info["teacher"]} | {info["discipline"]}')

print()
print('TODOS OS SLOTS DA FRANCINEUDA NO MESTRE:')
dias_ordem = ['SEGUNDA-FEIRA', terca_key, 'QUARTA-FEIRA', 'QUINTA-FEIRA', 'SEXTA-FEIRA']
total = 0
for dia in dias_ordem:
    if dia not in mestre:
        continue
    for turma, slots in mestre[dia].items():
        for slot_idx, info in slots.items():
            if 'FRANCINEUDA' in info.get('teacher', '').upper():
                hora = slot_to_hora.get(slot_idx, '?')
                print(f'  {dia} | {turma} | slot {slot_idx} ({hora}) | {info["discipline"]}')
                total += 1

print()
print(f'TOTAL DE SLOTS NO MESTRE: {total}')
