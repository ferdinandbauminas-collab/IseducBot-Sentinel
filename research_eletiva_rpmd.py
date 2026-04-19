import json
import os

MESTRE_FILE = r'C:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\planejamento_mestre_2026.json'

def research_allocations():
    if not os.path.exists(MESTRE_FILE):
        return

    with open(MESTRE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print("\n--- BUSCA POR ELETIVA ---")
    for day, ts in data.items():
        for turma, slots in ts.items():
            for slot, info in slots.items():
                if "ELETIVA" in info.get('discipline', '').upper():
                    print(f"{day} | {turma} | Slot {slot} | Prof: {info.get('teacher')}")

    print("\n--- BUSCA POR RPMD ---")
    for day, ts in data.items():
        for turma, slots in ts.items():
            for slot, info in slots.items():
                if "RPMD" in info.get('discipline', '').upper():
                    print(f"{day} | {turma} | Slot {slot} | Prof: {info.get('teacher')}")

if __name__ == "__main__":
    research_allocations()
