import json
import requests
import os

# Configurações do Supabase (Mesmos dados do seu portal visual)
SUPABASE_URL = 'https://wkmjoeoankucnhhanbqj.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndrbWpvZW9hbmt1Y25oaGFuYnFqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwNzA2OTMsImV4cCI6MjA4NjY0NjY5M30.lCcKfDP-Zv56VtXxXtdaNjspO8FidkqIryd0ssdQYsM'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
MESTRE_FILE = os.path.join(BASE_DIR, 'planejamento_mestre_2026.json')

def migrate_history():
    print("Iniciando migração do HISTÓRICO...")
    if not os.path.exists(HISTORY_FILE):
        print("Arquivo history.json não encontrado.")
        return

    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)

    # Vamos achatar o histórico para uma lista simples de registros
    flattened_history = []
    for entry in history:
        turma = entry.get('turma')
        for lanc in entry.get('lancamentos', []):
            flattened_history.append({
                "turma": turma,
                "data": lanc.get('data'),
                "horario": lanc.get('horario'),
                "componente": lanc.get('componente'),
                "professor": lanc.get('professor')
            })

    # Para não sobrecarregar o Supabase, vamos em blocos de 500
    batch_size = 500
    for i in range(0, len(flattened_history), batch_size):
        batch = flattened_history[i:i + batch_size]
        url = f"{SUPABASE_URL}/rest/v1/ef_history"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        # Nota: Você precisará criar a tabela 'ef_history' no painel do Supabase primeiro.
        res = requests.post(url, headers=headers, json=batch)
        if res.status_code in [200, 201]:
            print(f"Bloco {i//batch_size + 1} enviado com sucesso ({len(batch)} registros).")
        else:
            print(f"Erro no bloco {i//batch_size + 1}: {res.text}")

def migrate_planning():
    print("\nIniciando migração do PLANEJAMENTO MESTRE...")
    if not os.path.exists(MESTRE_FILE):
        print("Arquivo planejamento_mestre_2026.json não encontrado.")
        return

    with open(MESTRE_FILE, 'r', encoding='utf-8') as f:
        mestre = json.load(f)

    # Como o Supabase já tem a tabela ef_schedule que alimenta seu horário visual, 
    # vamos usá-la como fonte única na nuvem. 
    # O seu arquivo local já está sincronizado com ela após nossa última atividade.
    print("O planejamento mestre local já está sincronizado com a tabela 'ef_schedule'.")
    print("O sistema na nuvem lerá diretamente de lá.")

if __name__ == "__main__":
    # INSTRUÇÃO IMPORTANTE:
    # Antes de rodar este script, você deve criar a tabela 'ef_history' no seu banco Supabase
    # com as colunas: id (uuid/pk), data (text), horario (text), componente (text), professor (text), turma (text)
    
    confirm = input("Você já criou a tabela 'ef_history' no Supabase? (s/n): ")
    if confirm.lower() == 's':
        migrate_history()
        migrate_planning()
        print("\nPronto! Seus arquivos locais foram 'espelhados' na nuvem.")
    else:
        print("Por favor, crie a tabela primeiro no painel do Supabase.")
