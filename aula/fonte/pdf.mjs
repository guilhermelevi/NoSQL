// Converte HTML -> PDF via Chrome DevTools Protocol, com rodape proprio.
// uso: node pdf.mjs <entrada.html> <saida.pdf>
import { spawn } from 'node:child_process'
import { writeFileSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const [input, output] = process.argv.slice(2)
if (!input || !output) { console.error('uso: node pdf.mjs entrada.html saida.pdf'); process.exit(1) }

const PORT = 9333
const profile = mkdtempSync(join(tmpdir(), 'chrome-pdf-'))

const chrome = spawn(CHROME, [
  '--headless', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', '--hide-scrollbars',
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${profile}`,
  'about:blank',
], { stdio: ['ignore', 'ignore', 'pipe'] })

const sleep = (ms) => new Promise(r => setTimeout(r, ms))

async function esperarChrome() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`)
      if (r.ok) return await r.json()
    } catch {}
    await sleep(250)
  }
  throw new Error('Chrome nao respondeu na porta de debug')
}

class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pend = new Map(); this.ev = new Map()
    ws.addEventListener('message', (m) => {
      const msg = JSON.parse(m.data)
      if (msg.id && this.pend.has(msg.id)) {
        const { ok, bad } = this.pend.get(msg.id); this.pend.delete(msg.id)
        msg.error ? bad(new Error(JSON.stringify(msg.error))) : ok(msg.result)
      } else if (msg.method && this.ev.has(msg.method)) {
        this.ev.get(msg.method).forEach(f => f(msg.params)); this.ev.delete(msg.method)
      }
    })
  }
  send(method, params = {}) {
    const id = ++this.id
    return new Promise((ok, bad) => { this.pend.set(id, { ok, bad }); this.ws.send(JSON.stringify({ id, method, params })) })
  }
  once(method) { return new Promise(ok => { this.ev.set(method, [...(this.ev.get(method) || []), ok]) }) }
}

try {
  await esperarChrome()

  // cria uma aba nova (Chrome moderno exige PUT em /json/new)
  const novaAba = await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })
  const aba = await novaAba.json()

  const ws = new WebSocket(aba.webSocketDebuggerUrl)
  await new Promise((ok, bad) => { ws.addEventListener('open', ok); ws.addEventListener('error', bad) })
  const cdp = new CDP(ws)

  await cdp.send('Page.enable')
  const carregou = cdp.once('Page.loadEventFired')
  await cdp.send('Page.navigate', { url: 'file://' + resolve(input) })
  await carregou
  // garante que as fontes terminaram de carregar antes de paginar
  await cdp.send('Runtime.evaluate', { expression: 'document.fonts.ready', awaitPromise: true })
  await sleep(400)

  const rodape = `<div style="font-family:Georgia,'Times New Roman',serif;font-size:8pt;color:#8a8a8a;
      width:100%;padding:0 16mm;display:flex;justify-content:space-between;">
      <span>Bancos de Dados N&atilde;o Relacionais &middot; CEUB</span>
      <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
    </div>`

  const { data } = await cdp.send('Page.printToPDF', {
    printBackground: true,
    preferCSSPageSize: false,
    paperWidth: 8.27, paperHeight: 11.69,          // A4
    marginTop: 0.75, marginBottom: 0.72,
    marginLeft: 0.63, marginRight: 0.63,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: rodape,
  })

  writeFileSync(output, Buffer.from(data, 'base64'))
  const kb = (Buffer.from(data, 'base64').length / 1024).toFixed(0)
  console.log(`PDF gerado: ${output} (${kb} KB)`)
  ws.close()
} finally {
  chrome.kill()
}
