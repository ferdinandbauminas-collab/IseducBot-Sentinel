import json
import re
import os

path = r'c:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\planejamento_mestre_2026.json'

def clean_content():
    if not os.path.exists(path):
        print("Arquivo não encontrado.")
        return

    # Lendo com tratamento de erros para ignorar bytes corrompidos
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Padrão para pegar qualquer coisa que lembre "AD...LIA" (corrompido ou não)
    content = re.sub(r'AD[^\"]*LIA\s*(MARIA)?', 'CARLOS AUGUSTO', content)
    
    # Consertando Mojibakes comuns detectados
    content = content.replace('FÃØSICA', 'FÍSICA')
    
    # Escrevendo de volta em UTF-8 limpo
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Higienização concluída com sucesso.")

if __name__ == '__main__':
    clean_content()
