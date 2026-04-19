import json
import os
import io
import unicodedata
import re
import urllib.parse
import requests
from flask import Flask, render_template_string, request, jsonify
from collections import defaultdict
from datetime import datetime, timedelta

# Sentinel Premium Cloud v1.0 - Vercel Serverless Edition
app = Flask(__name__)

# Configurações de Ambiente (Segurança de Inicialização)
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://wkmjoeoankucnhhanbqj.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndrbWpvZW9hbmt1Y25oaGFuYnFqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwNzA2OTMsImV4cCI6MjA4NjY0NjY5M30.lCcKfDP-Zv56VtXxXtdaNjspO8FidkqIryd0ssdQYsM')
START_DATE_STR = os.getenv('START_DATE', '2026-02-19')

def get_start_date():
    try:
        return datetime.strptime(START_DATE_STR, '%Y-%m-%d')
    except:
        return datetime(2026, 2, 19)

TURMAS_AUDITADAS = [
    "MOD I A", "MOD I A ALT", "MOD I A MARK",
    "MOD III A", "MOD III B",
    "MOD V A", "MOD V B", "MOD V C", "MOD V D"
]

def sb_fetch(table):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

def clean_str(s):
    if not s: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn').replace(" ", "")

def normalize_discipline(d):
    if not d: return ""
    d_clean = clean_str(d)
    synonyms = {
        "PAI": "PROJETODEAPRENDIZAGEMINTERDISCIPLINAR",
        "ELETIVA": "ELETIVAORIENTADA",
        "TAVDA": "TECNICASAOVIVOEDEVIDEONAOPRESENCIAL",
        "FDA": "FUNDAMENTOSDAADMINISTRACAO",
        "RPMD": "REDACAOPARAOMARKETINGDIGITAL",
        "IAM": "INTRODUCAOAOMARKETING"
    }
    return synonyms.get(d_clean, d_clean)

def get_mandatory_slots():
    # Carregar planejamento do Supabase (tabela ef_schedule)
    schedule_data = sb_fetch('ef_schedule')
    
    # Mapeamento do Supabase para o formato do Auditor
    day_map = {
        'Segunda-feira': 'SEGUNDA-FEIRA',
        'Terça-feira': 'TERÇA-FEIRA',
        'Quarta-feira': 'QUARTA-FEIRA',
        'Quinta-feira': 'QUINTA-FEIRA',
        'Sexta-feira': 'SEXTA-FEIRA'
    }
    
    mandatory = []
    current = get_start_date()
    end_date = datetime.now() + timedelta(days=1)
    
    # Criar um lookup eficiente
    lookup = defaultdict(lambda: defaultdict(dict))
    for item in schedule_data:
        d = day_map.get(item['day_of_week'])
        if d:
            lookup[d][item['class_group']][str(item['slot_number'])] = {
                "teacher": item['teacher_name'],
                "discipline": item['discipline']
            }

    while current <= end_date:
        weekday = current.strftime('%A').lower()
        d_pt = {
            'monday': 'SEGUNDA-FEIRA', 'tuesday': 'TERÇA-FEIRA', 'wednesday': 'QUARTA-FEIRA',
            'thursday': 'QUINTA-FEIRA', 'friday': 'SEXTA-FEIRA'
        }.get(weekday)

        if d_pt and d_pt in lookup:
            for turma in TURMAS_AUDITADAS:
                if turma in lookup[d_pt]:
                    for slot, data in lookup[d_pt][turma].items():
                        mandatory.append({
                            "date": current.strftime("%Y-%m-%d"),
                            "turma": turma,
                            "slot": slot,
                            "teacher": data['teacher'],
                            "discipline": data['discipline']
                        })
        current += timedelta(days=1)
    return mandatory

def get_compliance_stats():
    try:
        # Fetch data from Supabase
        mandatory = get_mandatory_slots()
        history_raw = sb_fetch('ef_history')
        
        # Agrupar histórico
        history_lookup = defaultdict(list)
        for h in history_raw:
            try:
                dt_str = h.get('data', '')
                if not dt_str: continue
                if '/' in dt_str:
                    parts = dt_str.split('/')
                    dt_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
                    
                key = (dt_str, clean_str(h.get('turma', '')))
                history_lookup[key].append({
                    "horario": h.get('horario', ''),
                    "professor": clean_str(h.get('professor', '')),
                    "discipline": clean_str(h.get('componente', ''))
                })
            except: continue

        stats = defaultdict(lambda: {"total": 0, "done": 0, "gaps": []})
        realized_slots = set()
        temp_gaps = defaultdict(lambda: defaultdict(lambda: {"count": 0}))

        for m in mandatory:
            try:
                name_display = m.get('teacher', 'PROFESSOR DESCONHECIDO')
                p_norm = clean_str(name_display)
                disc_norm = normalize_discipline(m.get('discipline', ''))
                stats[name_display]["total"] += 1
                
                hist_key = (m['date'], clean_str(m['turma']))
                matches = history_lookup.get(hist_key, [])
                
                is_done = False
                for h in matches:
                    if h['professor'] == p_norm:
                        if normalize_discipline(h['discipline']) == disc_norm:
                            is_done = True
                            realized_slots.add(f"{m['date']}-{m['turma']}-{m.get('slot', '0')}")
                            break
                
                if is_done:
                    stats[name_display]["done"] += 1
                else:
                    try:
                        date_fmt = datetime.strptime(m['date'], "%Y-%m-%d").strftime("%d/%m")
                    except:
                        date_fmt = "??/??"
                    gap_key = (date_fmt, m['turma'], m['discipline'])
                    temp_gaps[name_display][gap_key]["count"] += 1
                    temp_gaps[name_display][gap_key]["turma"] = m['turma']
                    temp_gaps[name_display][gap_key]["discipline"] = m['discipline']
            except Exception as e:
                print(f"ERRO NO SLOT {m}: {e}")
                continue

        for prof in stats:
            for (date_fmt, turma, disc), data in temp_gaps[prof].items():
                stats[prof]["gaps"].append({"date": date_fmt, "turma": turma, "discipline": disc, "count": data["count"]})
            stats[prof]["gaps"].sort(key=lambda x: (x['date'].split('/')[1] if '/' in x['date'] else '0', x['date'].split('/')[0] if '/' in x['date'] else '0'))

        g_total = sum(d['total'] for d in stats.values())
        g_done = sum(d['done'] for d in stats.values())
        global_efficiency = round((g_done / g_total * 100), 1) if g_total > 0 else 0

        return stats, len(realized_slots), global_efficiency
    except Exception as e:
        print(f"CRITICAL ERROR IN STATS: {e}")
        return {}, 0, 0

@app.route('/debug')
def debug_info():
    schedule = sb_fetch('ef_schedule')
    history = sb_fetch('ef_history')
    return jsonify({
        "status": "online",
        "env_url": SUPABASE_URL[:15] + "...",
        "schedule_count": len(schedule),
        "history_count": len(history),
        "start_date": START_DATE_STR
    })

@app.route('/')
def dashboard():
    try:
        stats, realized_count, global_eff = get_compliance_stats()
        # Se stats estiver vazio, talvez o banco não tenha retornado nada
        if not stats: 
            return "<h1>Aguardando dados do Supabase...</h1><p>Verifique se as tabelas ef_schedule e ef_history possuem dados.</p>"
            
        return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8"><title>SENTINEL PREMIUM | CLOUD</title>
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
            .gap-list { margin-top: 15px; background: rgba(0,0,0,0.2); border-radius: 8px; padding: 10px; max-height: 120px; overflow-y: auto; }
            .gap-item { font-size: 10px; font-family: 'JetBrains Mono'; margin-bottom: 4px; color: var(--warning); display: flex; justify-content: space-between; }
            .gap-title { font-size: 10px; font-weight: 800; opacity: 0.5; margin-bottom: 5px; text-transform: uppercase; }
            .hero-section { background: radial-gradient(circle at center, rgba(0, 243, 255, 0.05) 0%, transparent 70%); padding: 30px 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 30px; }
            .hero-value { font-size: 64px; font-weight: 900; background: linear-gradient(180deg, #fff 30%, var(--primary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1; letter-spacing: -2px; filter: drop-shadow(0 0 20px rgba(0,243,255,0.2)); }
            .hero-label { text-transform: uppercase; letter-spacing: 5px; font-size: 12px; font-weight: 800; color: var(--primary); margin-top: 10px; opacity: 0.8; }
        </style>
    </head>
    <body class="container">
        <div class="hero-section">
            <div class="hero-label">Eficiência Global da Escola</div>
            <div class="hero-value">{{ global_eff }}%</div>
            <div style="max-width: 400px; margin: 15px auto 0; height: 4px; background: rgba(255,255,255,0.05); border-radius: 2px; overflow: hidden;">
                <div style="width:{{ global_eff }}%; height:100%; background:linear-gradient(90deg, var(--primary), var(--success)); box-shadow: 0 0 15px rgba(0,253,255,0.3)"></div>
            </div>
        </div>
        <div class="header">
            <h1>SENTINEL <span style="color:var(--primary)">PREMIUM</span> | <span style="font-size:14px; opacity:0.7">CLOUD EDITION</span></h1>
            <div class="badge">AUDITORIA: {{ realized_count }} AULAS</div>
        </div>
        <div class="grid">
            {% for prof, data in stats|dictsort %}
            <div class="card">
                <div class="prof-name">{{ prof }}</div>
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
                    <div class="gap-title">Pendências</div>
                    {% for gap in data.gaps[:10] %}
                    <div class="gap-item">
                        <span>● {{ gap.date }} - {{ gap.turma }}</span>
                        <span style="opacity:0.8">{{ gap.discipline }}</span>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </body></html>""", stats=stats, realized_count=realized_count, global_eff=global_eff)

if __name__ == '__main__':
    app.run(port=3000, host='0.0.0.0', debug=False)
