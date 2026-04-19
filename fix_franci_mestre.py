import json
import shutil
import os
from datetime import datetime

# Fazer backup antes de alterar
src = 'planejamento_mestre_2026.json'
backup = f'backups/planejamento_mestre_2026_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
os.makedirs('backups', exist_ok=True)
shutil.copy2(src, backup)
print(f'Backup criado: {backup}')

# Ler o mestre
with open(src, 'r', encoding='utf-8') as f:
    mestre = json.load(f)

# Localizar a chave Terca
terca_key = None
for k in mestre.keys():
    if 'TER' in k.upper() and 'FEIRA' in k.upper():
        terca_key = k
        break

if not terca_key:
    print('ERRO: Chave Terça-feira não encontrada!')
    exit(1)

print(f'Chave Terca-feira: {repr(terca_key)}')

# =============================================
# CORREÇÃO: Terça-feira | MOD III B | slot 2
# Trocar GERSON DOS SANTOS (PAI) -> FRANCINEUDA DA SILVA SOUSA (PORTUGUÊS)
# O histórico confirma que Francineuda lança 2 aulas seguidas (18h e 19h) no MOD III B na Terça
# =============================================

antes = mestre[terca_key]['MOD III B']['2']
print(f'\nSlot 2 ANTES: {antes}')

mestre[terca_key]['MOD III B']['2'] = {
    "teacher": "FRANCINEUDA DA SILVA SOUSA",
    "discipline": "PORTUGUÊS"
}

depois = mestre[terca_key]['MOD III B']['2']
print(f'Slot 2 DEPOIS: {depois}')

# Salvar
with open(src, 'w', encoding='utf-8') as f:
    json.dump(mestre, f, ensure_ascii=False, indent=4)

print('\n✅ planejamento_mestre_2026.json corrigido com sucesso!')

# Verificar resultado final
print('\n=== TERÇA-FEIRA | MOD III B (resultado final) ===')
slot_to_hora = {'1': '18:00', '2': '19:00', '3': '20:00', '4': '21:00'}
for slot_idx in sorted(mestre[terca_key]['MOD III B'].keys()):
    info = mestre[terca_key]['MOD III B'][slot_idx]
    print(f'  slot {slot_idx} ({slot_to_hora.get(slot_idx,"?")}) | {info["teacher"]} | {info["discipline"]}')

print('\n=== TERÇA-FEIRA | MOD V B (sem alteração) ===')
for slot_idx in sorted(mestre[terca_key]['MOD V B'].keys()):
    info = mestre[terca_key]['MOD V B'][slot_idx]
    print(f'  slot {slot_idx} ({slot_to_hora.get(slot_idx,"?")}) | {info["teacher"]} | {info["discipline"]}')

print('\n=== SLOTS COMPLETOS DA FRANCINEUDA NO MESTRE (pós-correção) ===')
dias_ordem = ['SEGUNDA-FEIRA', terca_key, 'QUARTA-FEIRA', 'QUINTA-FEIRA', 'SEXTA-FEIRA']
for dia in dias_ordem:
    if dia not in mestre:
        continue
    encontrou = False
    for turma, slots in mestre[dia].items():
        for slot_idx, info in slots.items():
            if 'FRANCINEUDA' in info.get('teacher', '').upper():
                if not encontrou:
                    print(f'\n{dia}:')
                    encontrou = True
                print(f'  {turma} | slot {slot_idx} ({slot_to_hora.get(slot_idx,"?")}) | {info["discipline"]}')
