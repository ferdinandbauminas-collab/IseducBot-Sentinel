import json

# Ler o arquivo raw para ver as chaves reais
with open('planejamento_mestre_2026.json', 'r', encoding='utf-8', errors='replace') as f:
    mestre = json.load(f)

print('Chaves reais do mestre (repr):')
for k in mestre.keys():
    print(f'  {repr(k)}')

# Tentar encontrar a chave correta para Terca
for k in mestre.keys():
    if 'TER' in k.upper():
        print(f'\nChave Terça encontrada: {repr(k)}')
        iiib = mestre[k].get('MOD III B', {})
        print(f'MOD III B tem {len(iiib)} slots')
        for slot_idx in sorted(iiib.keys()):
            info = iiib[slot_idx]
            print(f'  slot {slot_idx} | {info["teacher"]} | {info["discipline"]}')
        
        vb = mestre[k].get('MOD V B', {})
        print(f'\nMOD V B tem {len(vb)} slots')
        for slot_idx in sorted(vb.keys()):
            info = vb[slot_idx]
            print(f'  slot {slot_idx} | {info["teacher"]} | {info["discipline"]}')
