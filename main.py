import os
import sys
import json
import asyncio
import threading
import requests
import webbrowser
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.async_api import async_playwright

# Configuração de Encoding para o Terminal Windows
if sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

print("[SISTEMA] 🚀 Ativando IseducBot Scout v4.0 (Modal Edition)...", flush=True)

# --- CONFIGURAÇÃO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTA_ROBO = 3001
PORTA_DASHBOARD = 3000
USER_DATA_DIR = os.path.join(BASE_DIR, 'browser_profile')

app = Flask(__name__)
CORS(app)

shared_state = {"page": None, "loop": None}

@app.route('/trigger_audit', methods=['POST'])
def trigger_audit():
    if not shared_state["page"]:
        return jsonify({"error": "Navegador OFF"}), 500
    try:
        shared_state["loop"].call_soon_threadsafe(
            lambda: asyncio.create_task(shared_state["page"].evaluate("if(window.scout_runAudit) window.scout_runAudit();"))
        )
        return jsonify({"status": "Auditoria Iniciada"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def handle_audit_from_browser(results):
    turma = results.get('turma', '?')
    n_aulas = len(results.get('lancamentos', []))
    print(f"[ROBO] 📡 Enviando {n_aulas} aulas da turma {turma} para a Dashboard...", flush=True)
    
    try:
        url = f"http://localhost:{PORTA_DASHBOARD}/audit"
        # Desativar proxies para evitar WinError 10061 no Windows
        response = requests.post(url, json=results, timeout=15, proxies={"http": None, "https": None})
        if response.status_code == 200:
            print(f"[ROBO] ✅ Sincronizado com sucesso! (Portal -> Dashboard)", flush=True)
            # Abrir dashboard automaticamente ao sincronizar
            webbrowser.open(f"http://localhost:{PORTA_DASHBOARD}")
        else:
            print(f"[ROBO] ⚠️ Erro na sincronização: Status {response.status_code} - {response.text}", flush=True)
    except Exception as e:
        print(f"[ROBO] ❌ FALHA CRÍTICA DE CONEXÃO: {e}", flush=True)

ROBOT_JS = r"""
(function() {
    console.log("[SCOUT] 🤖 Robô Assistant v4.0 Injetado.");

    window.scout_bridge = window.scout_bridge || function(d){};

    // --- SISTEMA DE MODAL (OVERLAY NEON) ---
    window.scout_showModal = function(results) {
        let modal = document.getElementById('scout-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'scout-modal';
            modal.style = 'position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); width:90%; max-width:800px; height:80vh; background:#0b0e14; border:2px solid #00f3ff; border-radius:15px; z-index:100000; display:flex; flex-direction:column; box-shadow:0 0 50px rgba(0,243,255,0.3); color:#e2e8f0; font-family:sans-serif; overflow:hidden; transition: 0.3s;';
            document.body.appendChild(modal);
        }
        
        let rows = results.lancamentos.map((l, i) => `
            <tr>
                <td style="color:#64748b; font-size:10px">${i+1}</td>
                <td>${l.data}</td>
                <td style="color:#00f3ff; font-weight:bold">${l.horario}</td>
                <td>${l.componente}</td>
                <td style="font-size:11px">${l.professor}</td>
            </tr>
        `).join('');

        modal.innerHTML = `
            <div style="background:#151921; padding:20px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b">
                <div>
                    <h3 style="margin:0; color:#00f3ff">💎 RELATÓRIO DE AUDITORIA</h3>
                    <small>Turma: <b>${results.turma}</b> | <b>${results.lancamentos.length}</b> registros acumulados</small>
                </div>
                <div style="display:flex; gap:10px">
                    <button id="scout-btn-export" style="background:#00f3ff; color:#000; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer;">🚀 EXPORTAR TUDO</button>
                    <button onclick="document.getElementById('scout-modal').remove()" style="background:#ff4757; color:#fff; border:none; padding:10px; border-radius:5px; cursor:pointer;">FECHAR</button>
                </div>
            </div>
            <div style="flex:1; overflow-y:auto; padding:20px;">
                <table style="width:100%; border-collapse:collapse; font-size:12px">
                    <thead>
                        <tr style="text-align:left; color:#94a3b8; text-transform:uppercase; font-size:10px;">
                            <th style="padding:10px">#</th>
                            <th>Data</th>
                            <th>Hora</th>
                            <th>Componente</th>
                            <th>Professor</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
            <div style="background:#151921; padding:10px; font-size:10px; text-align:center; color:#475569">
                AUDITORIA INDUSTRIAL EM TEMPO REAL - ISEDUC BOT 2026
            </div>
        `;

        document.getElementById('scout-btn-export').onclick = function() {
            this.innerText = 'ENVIANDO...';
            this.style.opacity = '0.5';
            window.scout_bridge(window.SCOUT_MASTER_RESULTS);
            setTimeout(() => {
                this.innerText = 'Sincronizado!';
                this.style.background = '#00ff88';
            }, 1000);
        };
    };

    if (window.self === window.top) {
        window.SCOUT_MASTER_RESULTS = { turma: "IDENTIFICANDO...", lancamentos: [] };
        window.SCOUT_UNIQUE_KEYS = new Set();
    }

    async function processTable(doc) {
        const rows = Array.from(doc.querySelectorAll("tr, [role='row']"));
        if (rows.length < 2) return;
        const results = { lancamentos: [], turma: "N/D" };
        
        const headers = Array.from(doc.querySelectorAll('th')).map(h => h.innerText.toLowerCase());
        let colComp = headers.findIndex(h => h.includes('comp') || h.includes('di'));
        let colProf = headers.findIndex(h => h.includes('prof') || h.includes('docen'));
        if (colComp === -1) colComp = 6;
        if (colProf === -1) colProf = 7;

        for (const r of rows) {
            const cells = r.querySelectorAll("td");
            if (cells.length < 5) continue;
            const dt = (r.innerText.match(/(\d{2}\/\d{2}\/\d{4})/) || [])[1];
            if (!dt) continue;
            const hr = (r.innerText.match(/(\d{2}:\d{2})/) || ["", "00:00"])[1];
            
            if (results.turma === "N/D" && cells[4]) {
                results.turma = cells[4].innerText.trim().replace(/^\d+\s*-\s*/, '');
            }

            results.lancamentos.push({
                data: dt, 
                horario: hr, 
                componente: cells[colComp]?.innerText.trim() || 'N/D', 
                professor: cells[colProf]?.innerText.trim() || 'N/D'
            });
            r.style.borderLeft = "4px solid #00f3ff";
        }
        if (results.lancamentos.length > 0) window.top.postMessage({ type: 'SCOUT_RESULTS', data: results }, '*');
    }

    function findNext(docRoot) {
        const sel = ['button', 'a', '[aria-label*="Próxima"]'];
        const candidates = docRoot.querySelectorAll(sel.join(','));
        for (const c of candidates) {
            const t = (c.innerText + " " + (c.getAttribute('aria-label') || "")).toLowerCase();
            if ((t.includes("próxima") || t.includes("next") || t.includes(">")) && c.offsetParent !== null) {
                if (!t.includes("última")) return c;
            }
        }
        return null;
    }

    window.scout_runAudit = async function(isPagination = false) {
        if (window.self === window.top && !isPagination) {
            window.SCOUT_MASTER_RESULTS.lancamentos = [];
            window.SCOUT_UNIQUE_KEYS.clear();
        }
        
        // Identificar Turma no Topo
        if (window.self === window.top) {
            const head = document.querySelector('h1, h2, .breadcrumb');
            if (head) window.SCOUT_MASTER_RESULTS.turma = head.innerText.trim();
        }

        const broadcast = (win) => {
            win.postMessage({ type: 'SCOUT_START' }, '*');
            for (let i = 0; i < win.frames.length; i++) try { broadcast(win.frames[i]); } catch(e){}
        };
        broadcast(window.top);
    };

    window.addEventListener('message', async (e) => {
        if (!e.data) return;
        if (e.data.type === 'SCOUT_START') {
            await processTable(document);
            const btn = findNext(document);
            if (btn) {
                console.log("[SCOUT] Próxima página...");
                btn.click();
                setTimeout(() => window.scout_runAudit(true), 5000);
            }
        }
        if (e.data.type === 'SCOUT_RESULTS' && window.self === window.top) {
            e.data.data.lancamentos.forEach(l => {
                // Voltando para a chave baseada em conteúdo para evitar duplicatas
                const key = `${l.data}|${l.horario}|${l.componente}|${l.professor}`;
                if (!window.SCOUT_UNIQUE_KEYS.has(key)) {
                    window.SCOUT_UNIQUE_KEYS.add(key);
                    window.SCOUT_MASTER_RESULTS.lancamentos.push(l);
                }
            });
            if (e.data.data.turma !== "N/D") window.SCOUT_MASTER_RESULTS.turma = e.data.data.turma;
            window.scout_showModal(window.SCOUT_MASTER_RESULTS);
        }
    });

    setInterval(() => {
        if (document.getElementById('scout-trigger') || !window.location.href.includes("gerenciamento-aulas")) return;
        const btn = document.createElement('div');
        btn.id = 'scout-trigger'; btn.innerHTML = '💎 AUDITORIA';
        btn.style = 'position:fixed;bottom:20px;right:20px;z-index:99999;background:#00f3ff;color:#000;padding:15px 25px;border-radius:50px;font-weight:900;cursor:pointer;box-shadow:0 0 20px rgba(0,243,255,0.5);';
        btn.onclick = () => window.scout_runAudit();
        document.body.appendChild(btn);
    }, 3000);
})();
"""

async def run_browser():
    async with async_playwright() as p:
        print("[ROBO] Iniciando Navegador Inteligente...", flush=True)
        try:
            context = await p.chromium.launch_persistent_context(USER_DATA_DIR, headless=False, no_viewport=True, args=['--start-maximized'])
        except:
            print("[AVISO] Perfil em uso ou travado. Abrindo sessão isolada.", flush=True)
            browser = await p.chromium.launch(headless=False, args=['--start-maximized'])
            context = await browser.new_context(no_viewport=True)

        await context.expose_function("scout_bridge", handle_audit_from_browser)
        await context.add_init_script(ROBOT_JS)
        page = context.pages[0] if context.pages else await context.new_page()
        shared_state["page"] = page
        shared_state["loop"] = asyncio.get_event_loop()
        
        print("[ROBO] ✅ Pronto! Aguardando o portal...", flush=True)
        await page.goto("https://portal.seduc.pi.gov.br/", wait_until="domcontentloaded")
        while True: await asyncio.sleep(1)

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(port=PORTA_ROBO, host='0.0.0.0', debug=False, use_reloader=False), daemon=True).start()
    try:
        asyncio.run(run_browser())
    except KeyboardInterrupt:
        print("[SISTEMA] Encerrando...", flush=True)
