import json
import os

path = r'c:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\planejamento_mestre_2026.json'

def mestre_rebuilder():
    if not os.path.exists(path):
        print("Mestre não encontrado.")
        return

    # Lê os dados brutos com substituição de erros para evitar crashes
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # DICIONÁRIO DE RESTAURAÇÃO ORTOGRÁFICA (v4.11)
    corrections = {
        "ANAL. LÃ“G.": "ANAL. LÓG.",
        "ED. FÃSICA A": "ED. FÍSICA A",
        "FÃSICA": "FÍSICA",
        "HISTÃ“RIA": "HISTÓRIA",
        "INFORMÃ\x81TICA APLICADA A": "INFORMÁTICA APLICADA A",
        "INGLÃŠS INST.": "INGLÊS INST.",
        "MATEMÃ\x81TICA": "MATEMÁTICA",
        "QUÃMICA": "QUÍMICA",
        "INGLÃ\x8a S": "INGLÊS",
        "JORGE LUÃS SÃ\x81 BEZERRA": "JORGE LUÍS SÁ BEZERRA",
        "LINART": "LINARD",
        "ESPANHOLA": "ESPANHOLA"
    }

    original_len = len(content)
    for bad, good in corrections.items():
        content = content.replace(bad, good)
    
    # Limpeza extra de caracteres residuais ()
    content = content.replace("\ufffd", "")

    # Salva em UTF-8 puro
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Cirurgia v4.11 Concluída! {original_len} -> {len(content)} bytes.")

if __name__ == '__main__':
    mestre_rebuilder()
