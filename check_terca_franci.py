import json

with open('planejamento_mestre_2026.json', 'r', encoding='utf-8', errors='replace') as f:
    mestre = json.load(f)

slot_to_hora = {'1': '18:00', '2': '19:00', '3': '20:00', '4': '21:00'}

# Verificar TERCA-FEIRA completa
print('=== TERÇA-FEIRA - MOD III B (completo) ===')
terca_iiib = mestre.get('TERÇA-FEIRA', {}).get('MOD III B', {})
for slot_idx in sorted(terca_iiib.keys()):
    info = terca_iiib[slot_idx]
    print(f'  slot {slot_idx} ({slot_to_hora.get(slot_idx,"?")}) | {info["teacher"]} | {info["discipline"]}')

print()
print('=== TERÇA-FEIRA - MOD V B (completo) ===')
terca_vb = mestre.get('TERÇA-FEIRA', {}).get('MOD V B', {})
for slot_idx in sorted(terca_vb.keys()):
    info = terca_vb[slot_idx]
    print(f'  slot {slot_idx} ({slot_to_hora.get(slot_idx,"?")}) | {info["teacher"]} | {info["discipline"]}')

print()
# Verificar se slot 2 da Terça MOD III B é Francineuda
slot2_prof = terca_iiib.get('2', {}).get('teacher', 'N/A')
print(f'Slot 2 (19:00) de TERÇA MOD III B está com: {slot2_prof}')
print(f'É FRANCINEUDA? {"SIM" if "FRANCINEUDA" in slot2_prof.upper() else "NÃO - precisa corrigir!"}')
