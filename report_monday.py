import json
import os

MESTRE_FILE = r'C:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\planejamento_mestre_2026.json'

def print_monday_schedule():
    if not os.path.exists(MESTRE_FILE):
        print("Arquivo mestre não encontrado.")
        return

    with open(MESTRE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    monday = data.get('SEGUNDA-FEIRA', {})
    
    print("\n" + "="*80)
    print("HORÁRIOS DO PLANEJAMENTO - SEGUNDA-FEIRA")
    print("="*80)
    
    for turma in sorted(monday.keys()):
        print(f"\nTURMA: {turma}")
        print("-" * 30)
        slots = monday[turma]
        for slot in sorted(slots.keys(), key=int):
            info = slots[slot]
            teacher = info.get('teacher', '---')
            discipline = info.get('discipline', '---')
            print(f"  Slot {slot} (H{int(slot)+17}:00): {teacher:40} | {discipline}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    print_monday_schedule()
