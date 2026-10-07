"""Panel local de ejecución real: consola visual interactiva para auditoría del core COOPAC."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import subprocess, json, datetime, html

ROOT = Path(__file__).resolve().parents[1]

PROCEDURES = [
    {"id": "P0", "title": "P0 · Preparación y Verificación del Servidor", "desc": "Docker version, imagen postgres:16 y política de seguridad"},
    {"id": "P1", "title": "P1 · Regla R1 · Exposición de Puertos", "desc": "Verificación de puertos publicados (0.0.0.0 / ::)"},
    {"id": "P2", "title": "P2 · Regla R2 · Contraseñas en Texto Plano", "desc": "Búsqueda de contraseñas y conteo de caracteres en docker-compose.yml"},
    {"id": "P3", "title": "P3 · Regla R3 · Cuentas Superusuario", "desc": "Listado de roles con atributo Superuser en PostgreSQL"},
    {"id": "P4", "title": "P4 · Regla R4 · Cuentas Cesadas y Genéricas", "desc": "Cuentas activas con fecha_cese y cuentas sin documento"},
    {"id": "P5", "title": "P5 · Regla R5 · Segregación de Funciones", "desc": "Desembolsos con monto > umbral y autorregistrados/aprobados"},
    {"id": "P6", "title": "P6 · Regla R6 · Registro de Eventos (Logs)", "desc": "Parámetros log_connections y log_statement"},
    {"id": "P7", "title": "P7 · Regla R7 · Respaldo y Restauración", "desc": "Restauración en BD restauracion y verificación de tablas"},
    {"id": "P8", "title": "P8 · Validación de Causas Complementarias", "desc": "Conteo total de desembolsos, días sin respaldo e inspección de scripts"},
    {"id": "P9", "title": "P9 · Sellado de Evidencias SHA-256", "desc": "Generación y verificación de checksums SHA256SUMS.txt"}
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>COOPAC Santa Rosa · Auditoría del Core Financiero</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --code-bg: #090d16;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
    body { background-color: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
    .header {
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .header h1 { font-size: 24px; font-weight: 700; color: #38bdf8; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; }
    .header .subtitle { font-size: 14px; color: var(--text-muted); margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px; }
    .metadata-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      padding-top: 12px;
      border-top: 1px solid var(--card-border);
    }
    .meta-item { display: flex; flex-direction: column; }
    .meta-label { font-size: 12px; color: var(--text-muted); }
    .meta-value { font-size: 14px; font-weight: 600; color: #e2e8f0; }
    .main-grid {
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 24px;
    }
    @media (max-width: 900px) { .main-grid { grid-template-columns: 1fr; } }
    .procedures-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-height: 80vh;
      overflow-y: auto;
    }
    .proc-btn {
      background: #0f172a;
      border: 1px solid var(--card-border);
      color: var(--text);
      padding: 12px 14px;
      border-radius: 8px;
      cursor: pointer;
      text-align: left;
      transition: all 0.2s ease;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .proc-btn:hover:not(:disabled) {
      background: #334155;
      border-color: var(--primary);
      transform: translateY(-1px);
    }
    .proc-btn.active {
      border-color: var(--primary);
      background: #1e3a5f;
    }
    .proc-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .proc-title { font-size: 14px; font-weight: 600; color: #38bdf8; }
    .proc-desc { font-size: 12px; color: var(--text-muted); }
    .output-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .output-header {
      padding: 16px 20px;
      background: #131c2e;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .status-badge {
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      background: #334155;
      color: var(--text);
    }
    .status-badge.success { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #059669; }
    .status-badge.running { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #d97706; }
    .status-badge.error { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #dc2626; }
    .output-body {
      flex: 1;
      padding: 16px;
      background: var(--code-bg);
      overflow-y: auto;
      max-height: 70vh;
    }
    pre {
      font-family: 'Consolas', 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.6;
      color: #38bdf8;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .action-bar {
      margin-top: 12px;
      display: flex;
      gap: 10px;
    }
    .btn-action {
      background: var(--primary);
      color: #0f172a;
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn-action:hover { background: var(--primary-hover); }
  </style>
</head>
<body>

  <header class="header">
    <div class="subtitle">Universidad Privada de Tacna · Facultad de Ingeniería · E.P. Ingeniería de Sistemas</div>
    <h1>🛡️ COOPAC Santa Rosa · Consola Visual de Auditoría del Core</h1>
    <div class="metadata-grid">
      <div class="meta-item">
        <span class="meta-label">Estudiante / Auditor</span>
        <span class="meta-value">Akhtar Oviedo Ahmed Hasan</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Código</span>
        <span class="meta-value">2022074261</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Curso / Docente</span>
        <span class="meta-value">SI-084 · Dr. Oscar Juan Jimenez Flores</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Corte Auditado</span>
        <span class="meta-value">31/12/2025 (Ejecución: 07/10/2026)</span>
      </div>
    </div>
  </header>

  <main class="main-grid">
    <nav class="procedures-panel" id="proc-list">
      <!-- Buttons will be injected here -->
    </nav>

    <section class="output-panel">
      <div class="output-header">
        <div>
          <h2 id="current-proc-title" style="font-size: 16px; font-weight: 600;">Seleccione un Procedimiento</h2>
          <span id="current-proc-desc" style="font-size: 13px; color: var(--text-muted);">Haga clic en cualquiera de los procedimientos para ejecutar y visualizar la evidencia.</span>
        </div>
        <div id="status-badge" class="status-badge">Listo</div>
      </div>
      <div class="output-body">
        <pre id="output-content">Las salidas de ejecución real y las evidencias en disco se mostrarán aquí...</pre>
      </div>
    </section>
  </main>

  <script>
    const procs = __PROCEDURES_JSON__;
    const procList = document.getElementById('proc-list');
    const outTitle = document.getElementById('current-proc-title');
    const outDesc = document.getElementById('current-proc-desc');
    const outBadge = document.getElementById('status-badge');
    const outContent = document.getElementById('output-content');

    procs.forEach(p => {
      const btn = document.createElement('button');
      btn.className = 'proc-btn';
      btn.id = 'btn-' + p.id;
      btn.innerHTML = `<span class="proc-title">${p.title}</span><span class="proc-desc">${p.desc}</span>`;
      btn.onclick = () => runProcedure(p);
      procList.appendChild(btn);
    });

    async function runProcedure(proc) {
      document.querySelectorAll('.proc-btn').forEach(b => {
        b.disabled = true;
        b.classList.remove('active');
      });
      document.getElementById('btn-' + proc.id).classList.add('active');

      outTitle.textContent = proc.title;
      outDesc.textContent = proc.desc;
      outBadge.className = 'status-badge running';
      outBadge.textContent = 'Ejecutando...';
      outContent.textContent = 'Ejecutando procedimiento ' + proc.id + ' en Git Bash contra el contenedor sr_bd...';

      try {
        const res = await fetch('/run/' + proc.id, { method: 'POST' });
        const data = await res.json();

        outContent.textContent = data.output || 'Sin salida.';
        if (data.returncode === 0) {
          outBadge.className = 'status-badge success';
          outBadge.textContent = 'Completado (Código 0) · ' + (data.time || '');
        } else {
          outBadge.className = 'status-badge error';
          outBadge.textContent = 'Error (Código ' + data.returncode + ')';
        }
      } catch (err) {
        outBadge.className = 'status-badge error';
        outBadge.textContent = 'Error de conexión';
        outContent.textContent = String(err);
      } finally {
        document.querySelectorAll('.proc-btn').forEach(b => b.disabled = false);
      }
    }
  </script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            page = HTML_TEMPLATE.replace('__PROCEDURES_JSON__', json.dumps(PROCEDURES))
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(page.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        key = self.path.removeprefix('/run/')
        valid_keys = [p['id'] for p in PROCEDURES]
        if key not in valid_keys:
            self.send_error(400)
            return

        p = subprocess.run(
            ['C:/Program Files/Git/bin/bash.exe', '-x', 'scripts/auditoria.sh', key],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8',
            errors='replace',
            timeout=240
        )
        result = {
            'output': p.stdout,
            'returncode': p.returncode,
            'time': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5))).strftime('%d/%m/%Y %H:%M:%S')
        }
        (ROOT / 'evidencias' / f'{key}_ejecucion.log').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode('utf-8'))

if __name__ == '__main__':
    print("Iniciando servidor de auditoria en http://127.0.0.1:8765 ...")
    ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
