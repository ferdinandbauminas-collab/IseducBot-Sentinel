import os
import sys
import json
import asyncio
import threading
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.async_api import async_playwright

# --- CONFIGURAÇÃO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTA_ROBO = 3001
PORTA_DASHBOARD = 3000
USER_DATA_DIR = os.path.join(BASE_DIR, 'browser_profile')

app = Flask(__name__)
CORS(app)

# Estado compartilhado
shared_state = {"page": None, "loop": None}

@app.route('/trigger_audit', methods=['POST'])
def trigger_audit():
    if not shared_state["page"]:
        return jsonify({"error": "Navegador OFF"}), 500
    try:
        asyncio.run_coroutine_threadsafe(
            shared_state["page"].evaluate("if(window.scout_runAudit) window.scout_runAudit();"), 
            shared_state["loop"]
        )
        return jsonify({"status": "Auditoria Iniciada"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def handle_audit_from_browser(results):
    print(f"[ROBÔ] 🛰️ Auditoria Concluída! Turma: {results.get('turma', 'Desconhecida')}")
    # Opcional: Salvar localmente em JSON para rascunho
    try:
        with open(os.path.join(BASE_DIR, 'history_local.json'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(results, ensure_ascii=False) + "\n")
        print("[ROBÔ] ✅ Dados salvos em history_local.json")
    except: pass

# --- ROBOT JS: VARREDURA INDUSTRIAL 2026 ---
ROBOT_JS = r"""
(function() {
    'use strict';
    async function sleep(ms) { return new Promise(res => setTimeout(res, ms)); }

    const REPORT_STYLE = `
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0e11; color: #e1e1e1; padding: 40px; line-height: 1.6; }
        .container { max-width: 1000px; margin: auto; background: #161b22; padding: 30px; border-radius: 12px; border: 1px solid #30363d; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .header { display: flex; justify-content: space-between; align-items: start; border-bottom: 2px solid #00FBB6; padding-bottom: 20px; margin-bottom: 30px; }
        h1 { margin: 0; color: #00FBB6; font-size: 24px; text-transform: uppercase; letter-spacing: 1px; }
        .meta { font-size: 14px; color: #8b949e; margin-top: 5px; }
        .turma-badge { background: #1f6feb; color: white; padding: 6px 15px; border-radius: 6px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 10px rgba(31, 111, 235, 0.4); }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; table-layout: fixed; }
        th { text-align: left; background: #21262d; color: #58a6ff; padding: 12px; border: 1px solid #30363d; font-size: 13px; }
        td { padding: 10px; border: 1px solid #30363d; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        tr:nth-child(even) { background: #0d1117; }
        tr:hover { background: rgba(0, 251, 182, 0.05); }
        .prof { font-weight: bold; color: #c9d1d9; }
        .comp { color: #f2cc60; }
        .footer { margin-top: 40px; text-align: center; color: #8b949e; font-size: 12px; border-top: 1px solid #30363d; padding-top: 20px; }
        .no-results { text-align: center; padding: 50px; color: #ff7b72; font-weight: bold; }
    `;

    window.SCOUT_REPORT_WIN = null;

    window.scout_generateReport = function(results) {
        if (!window.SCOUT_REPORT_WIN || window.SCOUT_REPORT_WIN.closed) {
            window.SCOUT_REPORT_WIN = window.open("", "ISEDUC_SCOUT_REPORT");
        }
        
        const win = window.SCOUT_REPORT_WIN;
        if (!win) { console.error("🚨 Falha ao abrir janela."); return; }
        
        let rows = "";
        if (results.lancamentos.length === 0) {
            rows = `<tr><td colspan="4" class="no-results">Nenhuma aula encontrada para os critérios de busca.</td></tr>`;
        } else {
            results.lancamentos.forEach(l => {
                rows += `
                    <tr>
                        <td style="width:100px">${l.data}</td>
                        <td style="width:80px">${l.horario}</td>
                        <td class="comp">${l.componente}</td>
                        <td class="prof">${l.professor}</td>
                    </tr>
                `;
            });
        }

        const html = `
            <!DOCTYPE html>
            <html>
                <head>
                    <title>ISEDUC SCOUT: ${results.turma}</title>
                    <style>${REPORT_STYLE}</style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div>
                                <h1>ACOMPANHAMENTO DE LANÇAMENTOS ISEDUC AURISTELA 2026</h1>
                                <div class="meta">Atualização em tempo real: ${new Date().toLocaleTimeString()}</div>
                            </div>
                            <div class="turma-badge">${results.turma}</div>
                        </div>
                        <p>Total de Lançamentos Capturados: <strong>${results.lancamentos.length}</strong> de <strong>${results.totalOficial}</strong> registros detectados.</p>
                        <table>
                            <thead>
                                <tr>
                                    <th style="width:100px">Data</th>
                                    <th style="width:80px">Horário</th>
                                    <th>Disciplina (Componente)</th>
                                    <th>Professor</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${rows}
                            </tbody>
                        </table>
                        <div class="footer">🚀 Auditoria Industrial Estabilizada (v1.0 Stable) 🟢</div>
                    </div>
                </body>
            </html>
        `;
        win.document.open();
        win.document.write(html);
        win.document.close();
    };

    // Estado Global (apenas no Top)
    if (window.self === window.top) {
        window.SCOUT_MASTER_RESULTS = { turma: "NÃO IDENTIFICADA", totalOficial: "0", lancamentos: [] };
        window.SCOUT_UNIQUE_KEYS = new Set();
    }

    async function processTable(doc) {
        if (!doc) return;
        const rows = Array.from(doc.querySelectorAll("tr, [role='row']"));
        if (rows.length < 2) return;

        // Cabeçalhos inteligentes
        const headers = Array.from(doc.querySelectorAll('th, [role="columnheader"]')).map(h => h.innerText.toLowerCase());
        let colComp = headers.findIndex(h => h.includes('comp') || h.includes('disci') || h.includes('matéria'));
        let colProf = headers.findIndex(h => h.includes('prof') || h.includes('docent'));
        if (colComp === -1) colComp = 6; 
        if (colProf === -1) colProf = 7;

        console.log(`[SENSOR] 📡 Lendo Frame: ${window.location.href} (Cols: C:${colComp} P:${colProf})`);
        
        const localResults = { lancamentos: [], totalOficial: "0", turma: "NÃO IDENTIFICADA" };
        const bodyText = doc.body.innerText;
        const m = bodyText.match(/Mostrando\s+\d+\s+a\s+\d+\s+de\s+(\d+)/i);
        localResults.totalOficial = m ? m[1] : "0";

        for (const row of rows) {
            const cells = row.querySelectorAll("td, [role='gridcell']");
            if (cells.length < 5) continue; 
            
            const txt = row.innerText;
            const dateMatch = txt.match(/(\d{2}\/\d{2}\/\d{4})/);
            if (!dateMatch) continue;

            const dt = dateMatch[1];
            const hr = (txt.match(/(\d{2}:\d{2})/) || ["", "--:--"])[1];
            
            // Extração da Turma (Coluna 5)
            if (localResults.turma === "NÃO IDENTIFICADA" && cells[4]) {
                let tRaw = cells[4].innerText.trim();
                localResults.turma = tRaw.replace(/^\d+\s*-\s*/, '');
            }

            let comp = cells[colComp] ? cells[colComp].innerText.trim().replace(/\s+/g, ' ') : "N/D";
            let prof = cells[colProf] ? cells[colProf].innerText.trim().replace(/\s+/g, ' ') : "N/D";

            localResults.lancamentos.push({ data: dt, horario: hr, componente: comp, professor: prof });
            row.style.border = "2px solid #00FBB6";
        }

        if (localResults.lancamentos.length > 0) {
            window.top.postMessage({ type: 'SCOUT_RESULTS', data: localResults }, '*');
        }
    }

    function findNext(docRoot) {
        const nextSelectors = ['button', 'a', 'li a', 'span.next', '[aria-label*="Próxima"]'];
        const candidates = docRoot.querySelectorAll(nextSelectors.join(','));
        for (const c of candidates) {
            const t = (c.innerText + " " + (c.title || "") + " " + (c.getAttribute('aria-label') || "")).toLowerCase();
            if ((t.includes("próxima") || t.includes("next") || t.includes(">")) && c.offsetParent !== null) {
                if (!t.includes("última") && !t.includes("last") && !t.includes(">>")) return c;
            }
        }
        return null;
    }

    window.scout_runAudit = async function() {
        if (window.self === window.top) {
            window.SCOUT_MASTER_RESULTS.lancamentos = [];
            window.SCOUT_UNIQUE_KEYS.clear();
            console.log("[SCOUT] 📣 Iniciando Varredura Global...");
        }
        const broadcast = (win) => {
            try {
                win.postMessage({ type: 'SCOUT_START' }, '*');
                for (let i = 0; i < win.frames.length; i++) broadcast(win.frames[i]);
            } catch(e) {}
        };
        broadcast(window.top);
    };

    window.addEventListener('message', async (event) => {
        if (!event.data) return;
        if (event.data.type === 'SCOUT_START') {
            await processTable(document);
            const btnNext = findNext(document);
            if (btnNext) {
                console.log("[SCOUT] ⏭️ Paginação detectada. Aguardando...");
                btnNext.click();
                setTimeout(() => window.scout_runAudit(), 5000);
            }
        }
        if (event.data.type === 'SCOUT_RESULTS' && window.self === window.top) {
            const incoming = event.data.data;
            incoming.lancamentos.forEach(l => {
                const key = `${l.data}|${l.horario}|${l.componente}|${l.professor}`;
                if (!window.SCOUT_UNIQUE_KEYS.has(key)) {
                    window.SCOUT_UNIQUE_KEYS.add(key);
                    window.SCOUT_MASTER_RESULTS.lancamentos.push(l);
                }
            });
            window.SCOUT_MASTER_RESULTS.totalOficial = incoming.totalOficial;
            if (window.SCOUT_MASTER_RESULTS.turma === "NÃO IDENTIFICADA" && incoming.turma !== "NÃO IDENTIFICADA") {
                window.SCOUT_MASTER_RESULTS.turma = incoming.turma;
            }
            window.scout_generateReport(window.SCOUT_MASTER_RESULTS);
            try { window.scout_bridge(window.SCOUT_MASTER_RESULTS); } catch(e) {}
        }
    });

    function initTrigger() {
        const isTarget = window.location.href.includes("gerenciamento-aulas") || window.top.location.href.includes("gerenciamento-aulas");
        if (!isTarget) {
            const existing = document.getElementById('iseduc-sentinel-parent');
            if (existing) existing.remove();
            return;
        }
        if (window.self !== window.top || document.getElementById('iseduc-sentinel-parent')) return;
        if (!document.body && !document.documentElement) return;
        const host = document.createElement('div');
        host.id = 'iseduc-sentinel-parent';
        (document.body || document.documentElement).appendChild(host);
        const shadow = host.attachShadow({mode: 'open'});
        const container = document.createElement('div');
        container.style.cssText = 'position:fixed; bottom:24px; right:24px; z-index:2147483647; pointer-events:auto;';
        container.innerHTML = `
            <style>
                #btnAudit {
                    width: 150px; height: 55px; 
                    background: linear-gradient(135deg, #00FBB6 0%, #0099ff 100%); 
                    color: white; border: none; border-radius: 14px; 
                    cursor: pointer; display: flex; align-items: center; justify-content: center; 
                    font-weight: bold; box-shadow: 0 6px 20px rgba(0,251,182,0.5); 
                    font-family: 'Segoe UI', sans-serif; font-size: 13px; 
                    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
                }
                #btnAudit:hover { transform: scale(1.05) translateY(-2px); }
            </style>
            <div id="btnAudit">🔍 GERAR RELATÓRIO</div>
        `;
        shadow.appendChild(container);
        container.querySelector('#btnAudit').onclick = () => window.scout_runAudit();
    }

    function startSentinel() {
        initTrigger();
        if(window.MutationObserver) {
            new MutationObserver(() => { if (!document.getElementById('iseduc-sentinel-parent')) initTrigger(); })
            .observe(document.documentElement, { childList: true, subtree: true });
        }
        setInterval(initTrigger, 3000);
        window.addEventListener('hashchange', () => setTimeout(initTrigger, 1000));
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', startSentinel);
    else startSentinel();
})();
"""

async def run_browser():
    try:
        print("[ROBÔ] 🚀 Iniciando Navegador Estável...")
        async with async_playwright() as p:
            try:
                context = await p.chromium.launch_persistent_context(
                    USER_DATA_DIR, headless=False, no_viewport=True,
                    args=['--start-maximized', '--disable-blink-features=AutomationControlled']
                )
            except:
                browser = await p.chromium.launch(headless=False, args=['--start-maximized'])
                context = await browser.new_context(no_viewport=True)

            await context.expose_function("scout_bridge", handle_audit_from_browser)
            await context.add_init_script(ROBOT_JS)
            page = context.pages[0] if context.pages else await context.new_page()
            page.on("console", lambda msg: print(f"[BROWSER] {msg.text}"))
            shared_state["page"] = page
            shared_state["loop"] = asyncio.get_event_loop()
            await page.goto("https://portal.seduc.pi.gov.br/", wait_until="commit")
            while True: await asyncio.sleep(10)
    except Exception as e: print(f"[ERRO] {e}")

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(port=PORTA_ROBO, debug=False, use_reloader=False), daemon=True).start()
    try: asyncio.run(run_browser())
    except KeyboardInterrupt: pass
