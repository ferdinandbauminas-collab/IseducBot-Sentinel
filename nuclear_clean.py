import os

path = r'c:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\planejamento_mestre_2026.json'

def nuclear_purge():
    if not os.path.exists(path):
        print("Arquivo não encontrado.")
        return
    
    # Lê os bytes brutos para garantir que pegamos TUDO
    with open(path, 'rb') as f:
        raw_data = f.read()
    
    # Remove bytes de controle e o específico \x8d (141 decimal)
    # Mantém apenas caracteres imprimíveis e espaços/quebras de linha padrão
    clean_bytes = bytearray()
    for b in raw_data:
        # Permite ASCII imprimível (32-126) + acentuados UTF-8 comuns (>=128)
        # exceto o byte 141 (\x8d) e controles (0-31 exceto 10, 13)
        if b == 141: continue 
        if b < 32 and b not in [10, 13]: continue
        clean_bytes.append(b)
    
    # Salva como UTF-8 limpo
    with open(path, 'wb') as f:
        f.write(clean_bytes)
    
    # Verificação adicional via decode/encode
    try:
        content = clean_bytes.decode('utf-8', errors='ignore')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Purga Nuclear realizada com sucesso! Arquivo reconstruído.")
    except Exception as e:
        print(f"Erro na reconstrução: {e}")

if __name__ == '__main__':
    nuclear_purge()
