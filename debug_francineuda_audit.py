import json, unicodedata, re
from datetime import datetime, timedelta
from collections import defaultdict

def normalize_turma(s):
    if not s: return ''
    s = str(s).upper().strip()
    portal_map = {
        'EMTEJAMARKMODULOIINA': 'MOD I A MARK',
        'EMTEJAMARK-DIG-MODULO I-N-A': 'MOD I A MARK',
        'EMTEJAALTE-MODULO I-N-A': 'MOD I A ALT',
        'EMTEJAINFO-MODULO I-N-A': 'MOD I A',
        'EMTEJAINFO-MODULO III-N-A': 'MOD III A',
        'EMTEJAINFO-MODULO III-N-B': 'MOD III B',
        'EMTEJAINFO-MODULO V-N-A': 'MOD V A',
        'EMTEJAINFO-MODULO V-N-B': 'MOD V B',
        'EMTEJAINFO-MODULO V-N-C': 'MOD V C',
        'EMTEJAINFO-MODULO V-N-D': 'MOD V D',
    }
    if s in portal_map: return portal_map[s]
    s_alt = s.replace('EMEJA', 'EMTEJA')
    if s_alt in portal_map: return portal_map[s_alt]
    m = re.search(r'MODULO\s*([IVX]+)[^A-Z]*([A-Z])', s)
    if m:
        t = f'MOD {m.group(1)} {m.group(2)}'
        if 'MARK' in s: t += ' MARK'
        elif 'ALT' in s: t += ' ALT'
        return t
    return s

def normalize_discipline(s):
    if not s: return ''
    s = str(s).upper().strip()
    mapping = {
        'PROJETO DE APRENDIZAGEM INTERDISCIPLINAR': 'PAI',
        'PROJETO DE DESENVOLVIMENTO DE SISTEMAS': 'PDS',
        'EMPREENDEDORISMO PARA TI': 'EMP. TI',
        'EMPREENDEDORISMO PARA TECNOLOGIA DA INFORMACAO': 'EMP. TI',
        'REDES DE COMPUTADORES': 'REDES',
        'BANCO DE DADOS': 'BD',
        'PROGRAMACAO PARA COMPUTADORES': 'PROG. COMP',
        'INGLES INSTRUMENTAL': 'INGLES INST.',
        'LINGUA PORTUGUESA': 'PORTUGUES',
        'FUNDAMENTOS DA ADMINISTRACAO': 'FDA',
        'ED. FISICA A': 'ED. FISICA',
        'EDUCACAO FISICA': 'ED. FISICA'
    }
    s_clean = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    for key, sigla in mapping.items():
        if key in s_clean: return sigla
    if 'ESPANHOL' in s_clean: return 'LE'
    if 'INGLES' in s_clean or 'INGLES' in s_clean: return 'LINGUA INGLESA'
    if 'PORTUGU' in s_clean: return 'PORTUGUES'
    if 'ELETIVA' in s: return 'ELETIVA'
    return s

def normalize_teacher(s):
    if not s: return ''
    s = str(s).upper().strip()
    mapping = {
        'ALEXSANDRA MARIA LINARD PAES LANDIM RIBAMAR': 'ALEXSANDRA MARIA LINARD PAES LANDIM',
        'FRANCISCO DAS CHAGAS MENDES DA SILVA JUNIOR': 'FRANCISCO JR',
        'ELLYDA FERNANDA DE SOUSA OLIVEIRA': 'ELLYDA',
        'JARBAS FERNANDES DE OLIVEIRA': 'JARBAS',
        'JOANA DARC DE SOUSA CARDOSO': 'JOANA DARC',
        'SALOMAO DA SILVA FERREIRA': 'SALOMAO',
        'CARMEN SILVIA NUNES DE MOURA SANTOS': 'CARMEN',
        'EDNARDO LUIZ AMARANTE DOS SANTOS': 'EDNARDO FERREIRA DE SOUSA',
        'LINDELVÂNIA DE SOUSA ALMEIDA': 'LINDELVÂNIA',
        'GEMILSON JOSE DE SOUSA': 'GEMILSON',
        'GEMILSON': 'GEMILSON',
        'GEMILSOM': 'GEMILSON',
        'CARLOS AUGUSTO VIANA DOS SANTOS': 'CARLOS AUGUSTO',
        'CARLOS AUGUSTO': 'CARLOS AUGUSTO',
        'MARIA EUNICE LIRA TEIXEIRA ANDRADE': 'MARIA EUNICE',
        'JOSE DE ASSUNCAO SOUSA BARBOSA': 'JOSE DE ASSUNCAO',
        'WILSILENE DOS SANTOS OLIVEIRA BRANDAO': 'WILSILENE'
    }
    name_clean = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    for key, target in mapping.items():
        key_clean = ''.join(c for c in unicodedata.normalize('NFD', key.upper()) if unicodedata.category(c) != 'Mn')
        if key_clean in name_clean or name_clean in key_clean:
            return target
    return s

def clean_str(s, type_='general'):
    if not s: return ''
    if type_ == 'turma': s = normalize_turma(s)
    elif type_ == 'teacher': s = normalize_teacher(s)
    elif type_ == 'discipline': s = normalize_discipline(s)
    s = ''.join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^A-Z0-9]', '', s)

def map_time_to_slot(time_str):
    if not time_str: return None
    h = time_str[:2]
    if h == '18': return '1'
    if h == '19': return '2'
    if h == '20': return '3'
    if h == '21': return '4'
    if h in ['13', '14', '15', '16']: return str(int(h) - 8)
    return None

with open('history.json', 'r', encoding='utf-8', errors='replace') as f:
    history = json.load(f)
with open('planejamento_mestre_2026.json', 'r', encoding='utf-8', errors='replace') as f:
    mestre = json.load(f)

START_DATE = datetime(2026, 2, 19)
TURMAS_AUDITADAS = ['MOD I A', 'MOD I A ALT', 'MOD I A MARK', 'MOD III A', 'MOD III B', 'MOD V A', 'MOD V B', 'MOD V C', 'MOD V D']

# Construir mandatory slots para Francineuda
dias_map = {0: 'SEGUNDA-FEIRA', 1: 'TERÇA-FEIRA', 2: 'QUARTA-FEIRA', 3: 'QUINTA-FEIRA', 4: 'SEXTA-FEIRA'}
mandatory = []
today = datetime.now()
current = START_DATE

while current <= today:
    date_str = current.strftime('%Y-%m-%d')
    day_type = dias_map.get(current.weekday())
    if day_type and day_type in mestre:
        for turma, slots in mestre[day_type].items():
            if turma in TURMAS_AUDITADAS:
                for slot_idx, info in slots.items():
                    if 'SEM PROFESSOR' not in info['teacher'].upper():
                        if 'FRANCINEUDA' in info['teacher'].upper():
                            mandatory.append({
                                'date': date_str, 'turma': turma, 'slot': str(slot_idx),
                                'teacher': info['teacher'], 'discipline': info['discipline']
                            })
    current += timedelta(days=1)

print(f'=== SLOTS OBRIGATORIOS FRANCINEUDA: {len(mandatory)} ===')

# Construir pending_slots
pending_slots = defaultdict(list)
for m in mandatory:
    p_clean = clean_str(m['teacher'], 'teacher')
    d_clean = clean_str(m['discipline'], 'discipline')
    t_clean = clean_str(m['turma'], 'turma')
    pending_slots[(p_clean, d_clean, t_clean, m['date'])].append(m['slot'])

# Extrair historico
unique_hist = set()
for entry in history:
    t_clean = clean_str(entry.get('turma', ''), 'turma')
    for lanc in entry.get('lancamentos', []):
        p = lanc.get('professor', '')
        if 'FRANCINEUDA' not in p.upper(): continue
        p_clean = clean_str(p, 'teacher')
        d_clean = clean_str(lanc.get('componente', ''), 'discipline')
        dt_raw = lanc.get('data', '').split('/')
        if len(dt_raw) == 3:
            lesson_date = f'{dt_raw[2]}-{dt_raw[1]}-{dt_raw[0]}'
            horario = lanc.get('horario', '')
            unique_hist.add((t_clean, lesson_date, horario, p_clean, d_clean))

print(f'=== SLOTS NO HISTORICO FRANCINEUDA: {len(unique_hist)} ===')

# Processar matches
realized = set()
missed = []
for t_clean, lesson_date, horario, p_clean, d_clean in unique_hist:
    slot_id = map_time_to_slot(horario)
    day_key = (p_clean, d_clean, t_clean, lesson_date)
    if slot_id and slot_id in pending_slots[day_key]:
        realized.add((p_clean, d_clean, t_clean, lesson_date, slot_id))
        pending_slots[day_key].remove(slot_id)
    elif pending_slots[day_key]:
        any_slot = pending_slots[day_key].pop(0)
        realized.add((p_clean, d_clean, t_clean, lesson_date, any_slot))
    else:
        missed.append({'turma': t_clean, 'data': lesson_date, 'horario': horario, 'disc': d_clean, 'day_key': day_key})

print(f'=== REALIZADOS: {len(realized)} ===')
print(f'=== NAO BATERAM: {len(missed)} ===')
for m in missed[:10]:
    print(f'  NAO BATEU: {m}')

print()
# Verificar pendências restantes
remaining = [(k, v) for k, v in pending_slots.items() if v]
print(f'=== SLOTS PENDENTES (nao realizados): {sum(len(v) for _, v in remaining)} ===')
for k, v in remaining[:10]:
    print(f'  Pendente: key={k}, slots={v}')
