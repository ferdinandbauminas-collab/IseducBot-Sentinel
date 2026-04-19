import json

with open('planejamento_mestre_2026.json', 'r', encoding='utf-8', errors='replace') as f:
    mestre = json.load(f)

targets = ['MOD III A', 'MOD I A MARK']
print('=== PESQUISA DE SLOTS PARA ÍTALA ===\n')

for dia, turmas in mestre.items():
    for turma in targets:
        if turma in turmas:
            for slot, info in turmas[turma].items():
                disc = info.get('discipline', '').upper()
                teacher = info.get('teacher', '').upper()
                # Verificar se a disciplina bate com PAI, ELETIVA ou REDAÇÃO
                if any(x in disc for x in ['PAI', 'PROJETO', 'ELETIVA', 'REDAÇÃO', 'REDACAO']):
                    print(f'Dia: {dia}')
                    print(f'Turma: {turma}')
                    print(f'  Slot: {slot}')
                    print(f'  Professor Atual: {info.get("teacher")}')
                    print(f'  Disciplina Atual: {info.get("discipline")}')
                    print('-' * 40)
