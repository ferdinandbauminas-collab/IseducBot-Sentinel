import json

with open('planejamento_mestre_2026.json', 'r', encoding='utf-8', errors='replace') as f:
    mestre = json.load(f)

print('=== DISCIPLINAS DO PROFESSOR GERSON NA SEGUNDA-FEIRA ===\n')

# Procurar em todas as turmas da Segunda-Feira
segunda = mestre.get('SEGUNDA-FEIRA', {})
for turma in sorted(segunda.keys()):
    slots = segunda[turma]
    for slot in sorted(slots.keys()):
        info = slots[slot]
        if 'GERSON' in info.get('teacher', '').upper():
            hora = {'1': '18:00', '2': '19:00', '3': '20:00', '4': '21:00'}.get(slot, '?')
            print(f'Turma: {turma}')
            print(f'  Horário: {hora} (Slot {slot})')
            print(f'  Disciplina: {info.get("discipline")}')
            print('-' * 40)
