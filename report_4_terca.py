import json
import os

MESTRE_FILE = r'C:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\planejamento_mestre_2026.json'

def report_4_terca():
    if not os.path.exists(MESTRE_FILE):
        return

    with open(MESTRE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    day_key = 'TERÇA-FEIRA'
    terca = data.get(day_key, {})
    
    print("\n" + "="*80)
    print("QUADRO DE HORÁRIOS - TERÇA-FEIRA (CONFERÊNCIA)")
    print("="*80)
    
    for turma in sorted(terca.keys()):
        print(f"\nTURMA: {turma}")
        print("-" * 35)
        slots = terca[turma]
        
        # Horários fixos para demonstração
        times = {"1": "18:00", "2": "19:00", "3": "20:00", "4": "21:00"}
        
        for slot in ["1", "2", "3", "4"]:
            info = slots.get(slot, {})
            teacher = info.get('teacher', '---')
            discipline = info.get('discipline', '---')
            print(f"  Aula {slot} ({times[slot]}): {teacher:40} | {discipline}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    report_4_terca()
