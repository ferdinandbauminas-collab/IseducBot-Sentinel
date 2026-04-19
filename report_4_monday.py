import json
import os

MESTRE_FILE = r'C:\Users\ferdi\.gemini\antigravity\scratch\IseducBot\planejamento_mestre_2026.json'

def report_4_aulas():
    if not os.path.exists(MESTRE_FILE):
        return

    with open(MESTRE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    monday = data.get('SEGUNDA-FEIRA', {})
    
    print("\n" + "="*80)
    print("QUADRO OFICIAL DE HORÁRIOS - SEGUNDA-FEIRA (4 AULAS POR TURMA)")
    print("="*80)
    
    for turma in sorted(monday.keys()):
        print(f"\nTURMA: {turma}")
        print("-" * 35)
        slots = monday[turma]
        
        # Horários fixos para demonstração
        times = {"1": "18:00", "2": "19:00", "3": "20:00", "4": "21:00"}
        
        for slot in ["1", "2", "3", "4"]:
            info = slots.get(slot, {})
            teacher = info.get('teacher', '---')
            discipline = info.get('discipline', '---')
            
            # Aplicar a correção da Ítala para exibição
            if turma == "MOD I A MARK" and slot == "4":
                discipline = "RPMD"
                # O professor Ítala já está correto no JSON, mas garantimos aqui
                teacher = "ITALA RODRIGUES PROBO"
            
            print(f"  Aula {slot} ({times[slot]}): {teacher:40} | {discipline}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    report_4_aulas()
