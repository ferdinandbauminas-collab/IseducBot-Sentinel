import json

with open('planejamento_mestre_2026.json', 'r', encoding='utf-8', errors='replace') as f:
    mestre = json.load(f)

print('RESULTADOS PARA GERSON NO MOD I A MARK (ÚLTIMO SLOT):')
for dia, turmas in mestre.items():
    if 'MOD I A MARK' in turmas:
        slots = turmas['MOD I A MARK']
        if '4' in slots:
            info = slots['4']
            if 'GERSON' in info.get('teacher', '').upper():
                print(f'Dia: {dia}')
                print(f'Professor: {info.get("teacher")}')
                print(f'Disciplina: {info.get("discipline")}')
                print('---')
