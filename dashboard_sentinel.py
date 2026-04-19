import json
import os
import sys
import io
import io
import unicodedata
import re
import urllib.parse
from flask import Flask, render_template_string, request, jsonify
from collections import defaultdict
from datetime import datetime, timedelta

# Sentinel Premium v4.14.0 - Inteligência de Feriados Edition
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
MESTRE_FILE = os.path.join(BASE_DIR, 'planejamento_mestre_2026.json')
CALENDARIO_FILE = os.path.join(BASE_DIR, 'calendario_letivo_2026.json')
CONTACTS_FILE = os.path.join(BASE_DIR, 'teacher_contacts.json')
START_DATE = datetime(2026, 2, 19)

TURMAS_AUDITADAS = [
    "MOD I A", "MOD I A ALT", "MOD I A MARK",
    "MOD III A", "MOD III B",
    "MOD V A", "MOD V B", "MOD V C", "MOD V D"
]

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar {path}: {e}")
            return [] if 'history' in path else {}
    return [] if 'history' in path else {}

def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def normalize_turma(s):
    if not s: return ""
    s = str(s).upper().strip()
    portal_map = {
        "EMTEJAMARKMODULOIINA": "MOD I A MARK",
        "EMTEJAMARK-DIG-MODULO I-N-A": "MOD I A MARK",
        "EMTEJAALTE-MODULO I-N-A": "MOD I A ALT",
        "EMTEJAINFO-MODULO I-N-A": "MOD I A",
        "EMTEJAINFO-MODULO III-N-A": "MOD III A",
        "EMTEJAINFO-MODULO III-N-B": "MOD III B",
        "EMTEJAINFO-MODULO V-N-A": "MOD V A",
        "EMTEJAINFO-MODULO V-N-B": "MOD V B",
        "EMTEJAINFO-MODULO V-N-C": "MOD V C",
        "EMTEJAINFO-MODULO V-N-D": "MOD V D",
        "VII ETAPA": "VII ETAPA"
    }
    if s in portal_map: return portal_map[s]
    
    # Limpeza de prefixos comuns do portal
    s_alt = s.replace("EMEJA", "EMTEJA").replace("EMTEJAINFO-", "").replace("EMTEJAMARK-DIG-", "")
    if s_alt in portal_map: return portal_map[s_alt]

    # Regex inteligente: Procura MODULO + Romano + Qualquer coisa + Letra Final (A-D)
    # Ex: MODULO III-N-B -> Group1: III, Group2: B
    # Identificação de Módulo e Letra
    m = re.search(r'MODULO\s*([IVX]+).*?([A-D])', s)
    if not m: return s.strip().upper()
    
    level = m.group(1)
    letter = m.group(2)
    
    # Identificação de Sufixos (ALT, MARK, DIG)
    suffix = ""
    if "MARK" in s: suffix = " MARK"
    elif "ALT" in s: suffix = " ALT"
    elif "DIG" in s: suffix = " DIG"
    
    return f"MOD {level} {letter}{suffix}"

def normalize_teacher(s):
    if not s: return ""
    s = str(s).upper().strip()
    mapping = {
        "ALEXSANDRA MARIA LINARD PAES LANDIM RIBAMAR": "ALEXSANDRA MARIA LINARD PAES LANDIM",
        "FRANCISCO DAS CHAGAS MENDES DA SILVA JUNIOR": "FRANCISCO JR",
        "ELLYDA FERNANDA DE SOUSA OLIVEIRA": "ELLYDA",
        "JARBAS FERNANDES DE OLIVEIRA": "JARBAS",
        "JOANA DARC DE SOUSA CARDOSO": "JOANA DARC",
        "SALOMAO DA SILVA FERREIRA": "SALOMÃO",
        "CARMEN SILVIA NUNES DE MOURA SANTOS": "CARMEN",
        "EDNARDO LUIZ AMARANTE DOS SANTOS": "EDNARDO FERREIRA DE SOUSA",
        "LINDELVÂNIA DE SOUSA ALMEIDA": "LINDELVÂNIA",
        "GEMILSON JOSE DE SOUSA": "GEMILSON",
        "GEMILSON": "GEMILSON",
        "GEMILSOM": "GEMILSON",
        "CARLOS AUGUSTO VIANA DOS SANTOS": "CARLOS AUGUSTO",
        "CARLOS AUGUSTO": "CARLOS AUGUSTO",
        "MARIA EUNICE LIRA TEIXEIRA ANDRADE": "MARIA EUNICE",
        "JOSE DE ASSUNCAO SOUSA BARBOSA": "JOSE DE ASSUNCAO",
        "WILSILENE DOS SANTOS OLIVEIRA BRANDÃO": "WILSILENE",
        "FRANCINEUDA DA SILVA SOUSA": "FRANCINEUDA DA SILVA SOUSA"
    }
    # Normalização ultra-flexível para Francineuda e Gerson (Fuzzy Match)
    if not s: return ""
    name_clean = "".join(c for c in unicodedata.normalize('NFD', s.upper()) if unicodedata.category(c) != 'Mn')
    if "FRANCINEUDA" in name_clean:
        return "FRANCINEUDA DA SILVA SOUSA"
    if "GERSON" in name_clean:
        return "GERSON DOS SANTOS"
        
    for key, target in mapping.items():
        key_clean = "".join(c for c in unicodedata.normalize('NFD', key.upper()) if unicodedata.category(c) != 'Mn')
        if key_clean in name_clean or name_clean in key_clean:
            return target
    return s

def normalize_discipline(s):
    if not s: return ""
    s = str(s).upper().strip()
    # Mapeamento do Padrão Seletivo v4.9 (Longos e Compostos)
    mapping = {
        "PROJETO DE APRENDIZAGEM INTERDISCIPLINAR": "PAI",
        "PROJETO DE DESENVOLVIMENTO DE SISTEMAS": "PDS",
        "EMPREENDEDORISMO PARA TI": "EMP. TI",
        "EMPREENDEDORISMO PARA TECNOLOGIA DA INFORMAÇÃO": "EMP. TI",
        "REDES DE COMPUTADORES": "REDES",
        "BANCO DE DADOS": "BD",
        "PROGRAMAÇÃO PARA COMPUTADORES": "PROG. COMP",
        "INGLÊS INSTRUMENTAL": "INGLÊS INST.",
        "LÍNGUA PORTUGUESA": "PORTUGUÊS",
        "FUNDAMENTOS DA ADMINISTRAÇÃO": "FDA",
        "ED. FISICA A": "ED. FÍSICA",
        "ED. FÍSICA A": "ED. FÍSICA",
        "EDUCAÇÃO FÍSICA": "ED. FÍSICA"
    }
    # Checagem por substring para capturar nomes extremamente longos com variavel
    for key, sigla in mapping.items():
        if key in s: return sigla

    # Disciplinas Técnicas Adicionais (ITINERÁRIO)
    tech_map = {
        "TECNOLOGIAS EMERGENTES": "TEM",
        "DESENVOLVIMENTO DE SOFTWARE": "DS",
        "APLICATIVOS PARA DISPOSITIVOS MÓVEIS": "ADM",
        "BANCO DE DADOS": "BD",
        "REDES DE COMPUTADORES": "REDES",
        "EMPREENDEDORISMO PARA TI": "EMP. TI"
    }
    for key, sigla in tech_map.items():
        if key in s: return sigla

    if s in ["LÍNGUA ESPANHOLA", "LINGUA ESPANHOLA", "ESPANHOL", "SPAN"]: return "LE"
    if any(x in s for x in ["INGLES", "LÍNGUA INGLESA", "LINGUA INGLESA"]): return "LÍNGUA INGLESA"
    # Normalização flexível para Português
    if any(x in s for x in ["PORTUGU", "LINGUA PORTUGUESA", "PORT"]): return "PORTUGUÊS"
    # Limpeza profunda para comparação (sem acentos e em maiúsculas)
    s_clean = "".join(c for c in unicodedata.normalize('NFD', s.upper()) if unicodedata.category(c) != 'Mn')
    
    # Mapeamento de Siglas Técnicas (Portal -> Planejamento)
    if any(x in s_clean for x in ["PROJETO DE APRENDIZAGEM INTERDISCIPLINAR", "PAI"]): return "PAI"
    if any(x in s_clean for x in ["TECNOLOGIAS E AMBIENTES VIRTUAIS", "TAVDA"]): return "TAVDA"
    if any(x in s_clean for x in ["FUNDAMENTOS DA ADMIN", "FDA"]): return "FDA"
    if any(x in s_clean for x in ["REDACAO PARA O MARKETING DIGITAL", "RPMD"]): return "RPMD"
    if any(x in s_clean for x in ["INTRODUCAO AO MARKETING", "IAM"]): return "IAM"
    if any(x in s_clean for x in ["ELETIVA ORIENTADA", "ELETIVA"]): return "ELETIVA"
    
    if "INFORMATICA APLICADA" in s_clean: return "INFORMÁTICA APLICADA A"
    return s

def clean_str(s, type="general"):
    if not s: return ""
    if type == "turma": s = normalize_turma(s)
    elif type == "teacher": s = normalize_teacher(s)
    elif type == "discipline": s = normalize_discipline(s)
    s = "".join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^A-Z0-9]', '', s)

def map_time_to_slot(time_str):
    if not time_str: return None
    h = time_str[:2]
    if h == "18": return "1"
    if h == "19": return "2"
    if h == "20": return "3"
    if h == "21": return "4"
    if h in ["13", "14", "15", "16"]: return str(int(h) - 8)
    return None

def get_mandatory_slots():
    mestre = load_json(MESTRE_FILE)
    cal_data = load_json(CALENDARIO_FILE)
    sabados = cal_data.get("SABADOS_LETIVOS_2026", {})
    feriados = cal_data.get("FERIADOS_2026", [])
    today = datetime.now()
    current = START_DATE
    mandatory = []
    dias_map = {0: "SEGUNDA-FEIRA", 1: "TERÇA-FEIRA", 2: "QUARTA-FEIRA", 3: "QUINTA-FEIRA", 4: "SEXTA-FEIRA"}
    while current <= today:
        date_str = current.strftime("%Y-%m-%d")
        if date_str in feriados:
            current += timedelta(days=1)
            continue
        day_type = sabados.get(date_str) or dias_map.get(current.weekday())
        if day_type and day_type in mestre:
            for turma, slots in mestre[day_type].items():
                if turma in TURMAS_AUDITADAS:
                    for slot_idx, info in slots.items():
                        if "SEM PROFESSOR" not in info['teacher'].upper():
                            mandatory.append({"date": date_str, "turma": turma, "slot": str(slot_idx), "teacher": info['teacher'], "discipline": info['discipline']})
        current += timedelta(days=1)
    return mandatory

@app.route('/audit', methods=['POST'])
def receive_audit():
    data = request.json
    if not data or 'turma' not in data:
        return jsonify({"status": "error", "message": "Dados inválidos"}), 400
    
    t_incoming_raw = data.get('turma')
    t_incoming_clean = clean_str(t_incoming_raw, type="turma")
    
    print(f"\n[SERVER] 📥 Dados recebidos para: {t_incoming_raw} (Normalizado: {t_incoming_clean})")
    print(f"[SERVER] 📊 Total de lançamentos no pacote: {len(data.get('lancamentos', []))}")
    
    history = load_json(HISTORY_FILE)
    if not isinstance(history, list): history = []
    
    # Gerar assinaturas normalizadas dos registros existentes para evitar duplicatas físicas
    existing_sigs = set()
    for entry in history:
        t_hist_clean = clean_str(entry.get('turma'), type="turma")
        # Só comparamos assinaturas se for a mesma turma para manter performance
        if t_hist_clean == t_incoming_clean:
            for l in entry.get('lancamentos', []):
                p_clean = clean_str(l.get('professor'), type="teacher")
                d_clean = clean_str(l.get('componente', l.get('discipline')), type="discipline")
                # Assinatura agora inclui a turma para segurança extra
                sig = (t_hist_clean, l.get('data'), l.get('horario'), p_clean, d_clean)
                existing_sigs.add(sig)

    new_lancamentos = []
    for l in data.get('lancamentos', []):
        p_clean = clean_str(l.get('professor'), type="teacher")
        d_clean = clean_str(l.get('componente', l.get('discipline')), type="discipline")
        sig = (t_incoming_clean, l.get('data'), l.get('horario'), p_clean, d_clean)
        
        if sig not in existing_sigs:
            new_lancamentos.append(l)
            if "FRAN" in p_clean:
                print(f"  [DEBUG] Nova aula Detectada: {l.get('data')} {l.get('horario')} | {p_clean}")
            existing_sigs.add(sig)
            
    if new_lancamentos:
        new_data = data.copy()
        new_data['lancamentos'] = new_lancamentos
        new_data['timestamp'] = datetime.now().isoformat()
        history.append(new_data)
        
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
            print(f"[SERVER] ✅ SUCESSO: {len(new_lancamentos)} novos lançamentos salvos em {HISTORY_FILE}")
            return jsonify({"status": "success", "added": len(new_lancamentos)})
        except Exception as e:
            print(f"[SERVER] ❌ ERRO AO SALVAR ARQUIVO: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    print(f"[SERVER] ℹ️ INFORMAÇÃO: Todos os registros já existem no histórico.")
    return jsonify({"status": "success", "message": "Nenhum registro novo encontrado"})

def get_compliance_stats():
    mandatory = get_mandatory_slots()
    history = load_json(HISTORY_FILE)
    if not isinstance(history, list): history = []
    
    realized_slots = set()
    pending_slots = defaultdict(list)
    
    # 1. Mapear slots obrigatórios
    for m in mandatory:
        p_clean = clean_str(m['teacher'], type="teacher")
        d_clean = clean_str(m['discipline'], type="discipline")
        t_clean = clean_str(m['turma'], type="turma")
        pending_slots[(p_clean, d_clean, t_clean, m['date'])].append(m['slot'])
        
        # LOG DE DIAGNÓSTICO
        if "FRANCINEUDA" in p_clean and m['date'] == "2026-03-24":
             print(f"[AUDIT-PLAN] Esperado: {m['date']} | {m['turma']} ({t_clean}) | Slot: {m['slot']} | Prof: {p_clean}")

    # 2. Extrair Lançamentos Únicos Normalizados para evitar dupla contagem por variações de nome
    unique_history_entries = set()
    for entry in history:
        t_clean = clean_str(entry.get('turma', ''), type="turma")
        for lanc in entry.get('lancamentos', []):
            p_clean = clean_str(lanc.get('professor', ''), type="teacher")
            d_clean = clean_str(lanc.get('discipline', lanc.get('componente', '')), type="discipline")
            dt_raw = lanc.get('data', '').split('/')
            if len(dt_raw) == 3:
                lesson_date = f"{dt_raw[2]}-{dt_raw[1]}-{dt_raw[0]}"
                horario = lanc.get('horario', '')
                # A assinatura única considera: Turma + Data + Horário + Professor + Disciplina (Tudo Limpo)
                unique_history_entries.add((t_clean, lesson_date, horario, p_clean, d_clean))
                
                # LOG DE DIAGNÓSTICO
                if "FRANCINEUDA" in p_clean and lesson_date == "2026-03-24":
                    print(f"[AUDIT-HIST] Encontrado no Histórico: {lesson_date} | {horario} | Prof: {p_clean} | Turma: {t_clean}")

    # 3. Processar Lançamentos Únicos contra a Grade
    for t_clean, lesson_date, horario, p_clean, d_clean in unique_history_entries:
        slot_id = map_time_to_slot(horario)
        day_key = (p_clean, d_clean, t_clean, lesson_date)
        
        if slot_id and slot_id in pending_slots[day_key]:
            realized_slots.add((p_clean, d_clean, t_clean, lesson_date, slot_id))
            pending_slots[day_key].remove(slot_id)
        elif pending_slots[day_key]:
            # Alocação flexível para registros sem horário batendo exatamente
            any_slot = pending_slots[day_key].pop(0)
            realized_slots.add((p_clean, d_clean, t_clean, lesson_date, any_slot))
    
    stats = defaultdict(lambda: {"done": 0, "total": 0, "gaps": []})
    # Dicionário temporário para agrupar e contar pendências visuais
    temp_gaps = defaultdict(lambda: defaultdict(lambda: {"count": 0, "turma": "", "discipline": ""}))

    for m in mandatory:
        p_match = clean_str(m['teacher'], type="teacher")
        d_match = clean_str(m['discipline'], type="discipline")
        t_match = clean_str(m['turma'], type="turma")
        # Unificação por Nome Normalizado (Apelido)
        name_display = normalize_teacher(m['teacher']).upper()
        
        stats[name_display]["total"] += 1
        
        if (p_match, d_match, t_match, m['date'], m['slot']) in realized_slots:
            stats[name_display]["done"] += 1
        else:
            # Agrupar por data, turma e disciplina normalizada
            d_fmt = datetime.strptime(m['date'], "%Y-%m-%d").strftime("%d/%m")
            disc_norm = normalize_discipline(m['discipline'])
            gap_key = (d_fmt, m['turma'], disc_norm)
            
            temp_gaps[name_display][gap_key]["count"] += 1
            temp_gaps[name_display][gap_key]["turma"] = m['turma']
            temp_gaps[name_display][gap_key]["discipline"] = disc_norm

    # Converter o grupo temporário para a lista final de gaps do professor
    contacts = load_contacts()
    for prof in stats:
        for (date_fmt, turma, disc), data in temp_gaps[prof].items():
            stats[prof]["gaps"].append({
                "date": date_fmt,
                "turma": turma,
                "discipline": disc,
                "count": data["count"]
            })
        # Ordenar pendências por data
        stats[prof]["gaps"].sort(key=lambda x: (x['date'].split('/')[1], x['date'].split('/')[0]))
        
        # Gerar Link de WhatsApp com Elastic Match
        prof_clean = clean_str(prof)
        match_phone = None
        match_name = None
        
        for c_name, c_phone in contacts.items():
            c_clean = clean_str(c_name)
            if c_clean in prof_clean or prof_clean in c_clean:
                match_phone = c_phone
                match_name = c_name
                break
        
        if match_phone:
            total_gaps = sum(g['count'] for g in stats[prof]['gaps'])
            if total_gaps > 0:
                # Construir lista COMPLETA de pendências
                gap_details = []
                for g in stats[prof]['gaps']:
                    gap_details.append(f"• {g['date']} ({g['turma']}) - {g['discipline']}")
                
                list_str = "\n".join(gap_details)
                
                msg = f"Olá {prof}, identifiquei {total_gaps} aulas pendentes no ISEDUC de 2026:\n{list_str}\n\nPor favor, regularize assim que possível.\n\nCaso ja tenha atualizado, desconsidere essa mensagem.\nAtenciosamente.\nCOORDENAÇÃO PEDAGÓGICA."
            else:
                msg = f"Olá {prof}, parabéns! Seus lançamentos no portal do EJATEC 2026 estão 100% em dia. Obrigado pelo compromisso!"
            
            stats[prof]["wa_link"] = f"https://wa.me/{match_phone}?text={urllib.parse.quote(msg)}"
        else:
            stats[prof]["wa_link"] = None

    # Calcular Eficiência Global
    g_total = sum(d['total'] for d in stats.values())
    g_done = sum(d['done'] for d in stats.values())
    global_efficiency = round((g_done / g_total * 100), 1) if g_total > 0 else 0

    return stats, len(realized_slots), global_efficiency

@app.route('/')
def dashboard():
    stats, realized_count, global_eff = get_compliance_stats()
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8"><title>SENTINEL PREMIUM | AUDITORIA 2026</title>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Inter:wght@400;800&display=swap" rel="stylesheet">
        <style>
            :root { --bg: #0b0f19; --surface: #121a26; --primary: #00f3ff; --success: #00ff88; --warning: #ffb347; --text: #e2e8f0; }
            body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); padding: 30px; margin: 0; }
            .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 30px; }
            .badge { padding: 6px 12px; border-radius: 6px; background: rgba(0,243,255,0.1); border: 1px solid var(--primary); font-family: 'JetBrains Mono'; font-size: 11px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
            .card { background: var(--surface); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }
            .prof-name { font-weight: 800; font-size: 13px; margin-bottom: 5px; color: var(--primary); }
            .progress-container { height: 4px; background: rgba(255,255,255,0.05); border-radius: 2px; margin: 10px 0; }
            .progress-bar { height: 100%; transition: 0.5s; }
            .stats-text { display: flex; justify-content: space-between; font-size: 11px; font-weight: 700; opacity: 0.8; }
            .report-btn { padding: 4px 8px; font-size: 9px; background: var(--primary); color: var(--bg); border: none; border-radius: 4px; font-weight: 800; cursor: pointer; text-decoration: none; }
            .report-btn:hover { filter: brightness(1.2); }
            .gap-list { margin-top: 15px; background: rgba(0,0,0,0.2); border-radius: 8px; padding: 10px; max-height: 120px; overflow-y: auto; }
            .gap-item { font-size: 10px; font-family: 'JetBrains Mono'; margin-bottom: 4px; color: var(--warning); display: flex; justify-content: space-between; }
            .gap-title { font-size: 10px; font-weight: 800; opacity: 0.5; margin-bottom: 5px; text-transform: uppercase; }
            .hero-section { background: radial-gradient(circle at center, rgba(0, 243, 255, 0.05) 0%, transparent 70%); padding: 30px 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 30px; }
            .hero-value { font-size: 64px; font-weight: 900; background: linear-gradient(180deg, #fff 30%, var(--primary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1; letter-spacing: -2px; filter: drop-shadow(0 0 20px rgba(0,243,255,0.2)); }
            .hero-label { text-transform: uppercase; letter-spacing: 5px; font-size: 12px; font-weight: 800; color: var(--primary); margin-top: 10px; opacity: 0.8; }
            .hero-sub { font-size: 11px; opacity: 0.5; margin-top: 5px; font-family: 'JetBrains Mono'; }
        </style>
    </head>
    <body class="container">
        <!-- Hero Section: Eficiência Global Centralizada (Topo Absoluto) -->
        <div class="hero-section">
            <div class="hero-label">Eficiência Global da Escola</div>
            <div class="hero-value">{{ global_eff }}%</div>
            <div class="hero-sub">Índice Geral de Lançamentos Sincronizados</div>
            <div style="max-width: 400px; margin: 15px auto 0; height: 4px; background: rgba(255,255,255,0.05); border-radius: 2px; overflow: hidden;">
                <div style="width:{{ global_eff }}%; height:100%; background:linear-gradient(90deg, var(--primary), var(--success)); box-shadow: 0 0 15px rgba(0,253,255,0.3)"></div>
            </div>
        </div>

        <div class="header">
            <h1>SENTINEL <span style="color:var(--primary)">PREMIUM</span> | <span style="font-size:18px; opacity:0.7">AUDITORIA 2026</span></h1>
            <div class="badge">AUDITORIA ATIVA: {{ realized_count }} AULAS</div>
        </div>
        <div class="grid">
            {% for prof, data in stats|dictsort %}
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div class="prof-name">{{ prof }}</div>
                    <div style="display:flex; gap:5px;">
                        {% if data.wa_link %}
                        <a href="{{ data.wa_link }}" target="_blank" class="report-btn" style="background:#25D366; color:#fff; display:flex; align-items:center; gap:3px;">
                            <svg style="width:10px; height:10px" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>
                            ZAP
                        </a>
                        {% endif %}
                        <a href="/report/{{ prof }}" class="report-btn">📄 RELATÓRIO</a>
                    </div>
                </div>
                {% set perc = (data.done/data.total*100)|round if data.total > 0 else 0 %}
                <div class="stats-text">
                    <span style="color:{{ 'var(--success)' if perc >= 100 else 'var(--primary)' if perc > 0 else '#666' }}">{{ perc }}% CONFORMIDADE</span>
                    <span>{{ data.done }}/{{ data.total }}</span>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {{ perc }}%; background: {{ 'var(--success)' if perc >= 100 else 'var(--primary)' }}"></div>
                </div>
                {% if data.gaps %}
                <div class="gap-list">
                    <div class="gap-title">Pendências (Aulas não lançadas)</div>
                    {% for gap in data.gaps[:20] %}
                    <div class="gap-item">
                        <span>● {{ gap.date }} - {{ gap.turma }}</span>
                        <span style="opacity:0.8">{{ gap.discipline }} <b style="color:var(--primary); font-size:9px">(x{{ gap.count }})</b></span>
                    </div>
                    {% endfor %}
                    {% if data.gaps|length > 20 %}
                    <div style="font-size:9px; opacity:0.5; text-align:center">+ {{ data.gaps|length - 20 }} pendências</div>
                    {% endif %}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </body></html>""", stats=stats, realized_count=realized_count, global_eff=global_eff)

@app.route('/report/<teacher_name>')
def report(teacher_name):
    stats, _, _ = get_compliance_stats()
    if teacher_name not in stats: return "Professor não encontrado", 404
    data = stats[teacher_name]
    perc = round(data['done']/data['total']*100) if data['total'] > 0 else 0
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8"><title>Relatório Individual - {{ name }}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Inter', sans-serif; color: #1a202c; padding: 40px; line-height: 1.6; background: #fff; }
            .header { border-bottom: 2px solid #edf2f7; padding-bottom: 20px; margin-bottom: 30px; }
            .title { font-size: 24px; font-weight: 700; color: #2d3748; }
            .subtitle { font-size: 14px; color: #718096; text-transform: uppercase; letter-spacing: 1px; }
            .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
            .stat-card { border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; }
            .stat-value { font-size: 32px; font-weight: 700; color: #3182ce; }
            .stat-label { font-size: 12px; color: #718096; font-weight: 700; text-transform: uppercase; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { text-align: left; background: #f7fafc; padding: 12px; font-size: 11px; text-transform: uppercase; color: #4a5568; }
            td { padding: 12px; border-bottom: 1px solid #edf2f7; font-size: 13px; }
            .btn-print { background: #3182ce; color: #fff; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-weight: 700; margin-bottom: 20px; }
            @media print { .btn-print { display: none; } body { padding: 0; } }
            .footer { margin-top: 50px; border-top: 1px dashed #cbd5e0; padding-top: 20px; font-size: 11px; text-align: center; color: #a0aec0; }
        </style>
    </head>
    <body>
        <button class="btn-print" onclick="window.print()">🖨️ IMPRIMIR / SALVAR PDF</button>
        <div class="header">
            <div class="subtitle">Relatório de Conformidade de Lançamentos 2026</div>
            <div class="title">{{ name }}</div>
        </div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Índice de Conformidade</div>
                <div class="stat-value">{{ perc }}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Aulas Auditadas</div>
                <div class="stat-value">{{ data.done }} / {{ data.total }}</div>
            </div>
        </div>
        <h3 style="font-size:14px; text-transform:uppercase; margin-bottom:10px;">Detalhamento de Pendências</h3>
        {% if data.gaps %}
        <table>
            <thead><tr><th>DATA</th><th>TURMA</th><th>DISCIPLINA</th><th>QTD</th><th>STATUS</th></tr></thead>
            <tbody>
                {% for gap in data.gaps %}
                <tr>
                    <td>{{ gap.date }} / 2026</td>
                    <td>{{ gap.turma }}</td>
                    <td>{{ gap.discipline }}</td>
                    <td style="font-weight:700">{{ gap.count }} aula(s)</td>
                    <td style="color:#e53e3e; font-weight:700;">NÃO LANÇADO</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p style="color:#2f855a; font-weight:700;">✅ Parabéns! Não há pendências registradas para este professor.</p>
        {% endif %}
        <div class="footer">Gerado automaticamente pelo Sistema GESTÃO ISEDUC em {{ now }}</div>
        <div style="margin-top:80px; display:flex; justify-content:space-around;">
            <div style="border-top:1px solid #000; width:200px; text-align:center; font-size:11px; padding-top:5px;">Assinatura Coordenador(a)</div>
            <div style="border-top:1px solid #000; width:200px; text-align:center; font-size:11px; padding-top:5px;">Assinatura Professor(a)</div>
        </div>
    </body></html>""", name=teacher_name, data=data, perc=perc, now=datetime.now().strftime("%d/%m/%Y %H:%M"))

if __name__ == '__main__':
    app.run(port=3000, host='0.0.0.0', debug=False)
