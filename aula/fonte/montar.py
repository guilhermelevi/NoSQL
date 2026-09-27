#!/usr/bin/env python3
# Monta o HTML da aula a partir do JSON produzido pelo workflow.
# uso: python3 montar.py aula.json aula.html
import json, sys, html, re

ent, saida = sys.argv[1], sys.argv[2]
d = json.load(open(ent))

def e(t):
    return html.escape(str(t or ''))

def para(t):
    """Texto em paragrafos, respeitando quebras duplas."""
    t = (t or '').strip()
    if not t:
        return ''
    blocos = re.split(r'\n\s*\n', t)
    return ''.join(f'<p>{e(b).replace(chr(10), "<br>")}</p>' for b in blocos)

# cor por sistema, para o leitor localizar o assunto de relance
TEMA = {
    'contexto': 'neutro', 'mongo-documento': 'mongo', 'mongo-agregacao': 'mongo',
    'mongo-indices': 'mongo', 'es-arquitetura': 'elastic', 'es-modelagem': 'elastic',
    'es-vetorial': 'elastic', 'integracao': 'sintese',
}
ORDEM = ['contexto', 'mongo-documento', 'mongo-agregacao', 'mongo-indices',
         'es-arquitetura', 'es-modelagem', 'es-vetorial', 'integracao']

def tema_de(i, m):
    if isinstance(m, dict) and m.get('tema') in CORES:
        return m['tema']
    return TEMA.get(ORDEM[i] if i < len(ORDEM) else '', 'neutro')

CSS = """
@page { size: A4; }
* { box-sizing: border-box; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 10.5pt; line-height: 1.55;
       color: #1a1a1a; margin: 0; }
h1, h2, h3, h4, .rotulo, .num, th, .dur { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }

/* ---------- capa ---------- */
.capa { height: 247mm; display: flex; flex-direction: column; justify-content: center;
        page-break-after: always; }
.capa .disciplina { font-family: 'Helvetica Neue', sans-serif; font-size: 9.5pt; letter-spacing: .18em;
        text-transform: uppercase; color: #6b7280; margin-bottom: 10mm; }
.capa h1 { font-size: 30pt; line-height: 1.15; margin: 0 0 6mm; color: #111; font-weight: 700; }
.capa .sub { font-size: 13pt; color: #444; font-style: italic; margin-bottom: 14mm; line-height: 1.5; }
.capa .regua { height: 3px; background: linear-gradient(90deg, #00684A 0%, #00684A 45%, #0B64A0 55%, #0B64A0 100%);
        margin-bottom: 12mm; }
.capa dl { display: grid; grid-template-columns: 32mm 1fr; gap: 2.5mm 6mm; font-size: 10pt; margin: 0; }
.capa dt { font-family: 'Helvetica Neue', sans-serif; font-size: 8.5pt; text-transform: uppercase;
        letter-spacing: .08em; color: #6b7280; padding-top: 1pt; }
.capa dd { margin: 0; }
.capa .rodape-capa { margin-top: 16mm; font-size: 9pt; color: #6b7280; border-top: 1px solid #e5e7eb;
        padding-top: 4mm; }

/* ---------- sumario ---------- */
.sumario { page-break-after: always; }
.sumario h2 { border: 0; margin-bottom: 8mm; }
.toc { list-style: none; padding: 0; margin: 0; }
.toc li { display: flex; align-items: baseline; gap: 3mm; padding: 2.2mm 0;
          border-bottom: 1px dotted #d1d5db; font-size: 10.5pt; }
.toc .n { font-family: 'Helvetica Neue', sans-serif; font-weight: 700; font-size: 9pt;
          min-width: 16mm; color: #9ca3af; }
.toc .t { flex: 1; }
.toc .d { font-family: 'Helvetica Neue', sans-serif; font-size: 8.5pt; color: #6b7280; }
.toc .grupo { font-family: 'Helvetica Neue', sans-serif; font-size: 8pt; text-transform: uppercase;
        letter-spacing: .1em; color: #9ca3af; border: 0; padding-top: 6mm; }

/* ---------- modulos ---------- */
.modulo { page-break-before: always; }
.modulo-head { display: flex; justify-content: space-between; align-items: baseline;
        border-bottom: 2.5pt solid var(--cor); padding-bottom: 2mm; margin-bottom: 5mm; }
.num { font-size: 8.5pt; text-transform: uppercase; letter-spacing: .14em; color: var(--cor); font-weight: 700; }
.dur { font-size: 8.5pt; color: #6b7280; }
.modulo h2 { font-size: 17pt; margin: 0 0 4mm; line-height: 1.2; color: #111; }
.abertura { font-size: 11.5pt; font-style: italic; color: #374151; border-left: 3px solid var(--cor);
        padding: 1mm 0 1mm 5mm; margin: 0 0 6mm; }
h3 { font-size: 8.5pt; text-transform: uppercase; letter-spacing: .13em; color: #6b7280;
     margin: 7mm 0 3mm; padding-bottom: 1.5mm; border-bottom: 1px solid #e5e7eb; }
h4 { font-size: 11pt; margin: 0 0 1.5mm; color: #111; }
p { margin: 0 0 2.8mm; text-align: justify; hyphens: auto; }
ul, ol { margin: 0 0 3mm; padding-left: 5mm; }
li { margin-bottom: 1.5mm; }

.conceito { margin-bottom: 5mm; page-break-inside: avoid; }
.caixa { font-size: 9.5pt; padding: 2.5mm 3.5mm; margin: 2mm 0; border-radius: 2px;
         page-break-inside: avoid; }
.analogia { background: #f8f6f1; border-left: 2.5pt solid #b8a06a; }
.erro { background: #fdf3f3; border-left: 2.5pt solid #c0574f; }
.caixa .rotulo { font-size: 7.5pt; text-transform: uppercase; letter-spacing: .1em;
        display: block; margin-bottom: 1mm; font-weight: 700; }
.analogia .rotulo { color: #8a7333; }
.erro .rotulo { color: #a63d35; }
.caixa p { margin: 0; text-align: left; }

.demo { margin-bottom: 5mm; page-break-inside: avoid; }
pre { font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 8pt; line-height: 1.45;
      white-space: pre-wrap; word-break: break-word; margin: 0 0 1.5mm; padding: 2.5mm 3mm;
      page-break-inside: avoid; }
pre.codigo { background: #f6f8fa; border-left: 2.5pt solid var(--cor); color: #111; }
pre.saida { background: #fafafa; border-left: 2.5pt solid #d1d5db; color: #4b5563; }
.rot-saida { font-family: 'Helvetica Neue', sans-serif; font-size: 7pt; text-transform: uppercase;
        letter-spacing: .1em; color: #9ca3af; margin: 0 0 .8mm; }
.explica { font-size: 10pt; }
.fonte { font-size: 8pt; color: #9ca3af; font-style: italic; text-align: right; margin: 0; }
code { font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 9pt;
       background: #f3f4f6; padding: 0 1mm; border-radius: 2px; }

.fechamento { background: #f9fafb; border-left: 3px solid var(--cor); padding: 3mm 4mm;
        margin: 6mm 0 0; font-size: 10pt; page-break-inside: avoid; }
.fechamento .rotulo { font-family: 'Helvetica Neue', sans-serif; font-size: 7.5pt;
        text-transform: uppercase; letter-spacing: .1em; color: var(--cor); font-weight: 700;
        display: block; margin-bottom: 1.5mm; }
.perguntas { margin-top: 5mm; }
.perguntas ol { font-size: 10pt; }

/* ---------- tabelas ---------- */
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 0 0 4mm;
        page-break-inside: avoid; }
th { background: #f3f4f6; text-align: left; font-size: 8pt; text-transform: uppercase;
     letter-spacing: .06em; color: #374151; }
th, td { border: 1px solid #e5e7eb; padding: 2mm 2.5mm; vertical-align: top; }
tr:nth-child(even) td { background: #fcfcfc; }

/* ---------- secoes finais ---------- */
.secao { page-break-before: always; }
.secao > h2 { font-size: 17pt; border-bottom: 2.5pt solid #374151; padding-bottom: 2mm;
        margin: 0 0 3mm; }
.secao .intro { font-style: italic; color: #4b5563; margin-bottom: 6mm; }

.armadilha { page-break-inside: avoid; margin-bottom: 6mm; border: 1px solid #e5e7eb;
        border-left: 3px solid #c0574f; padding: 3.5mm 4mm; }
.armadilha h4 { margin-bottom: 2mm; }
.armadilha .tag { font-family: 'Helvetica Neue', sans-serif; font-size: 7.5pt; text-transform: uppercase;
        letter-spacing: .08em; color: #6b7280; background: #f3f4f6; padding: .5mm 2mm; border-radius: 2px; }
.armadilha dl { margin: 2mm 0 0; display: grid; grid-template-columns: 26mm 1fr; gap: 1.5mm 4mm;
        font-size: 9.5pt; }
.armadilha dt { font-family: 'Helvetica Neue', sans-serif; font-size: 7.5pt; text-transform: uppercase;
        letter-spacing: .08em; color: #9ca3af; padding-top: .7mm; }
.armadilha dd { margin: 0; }
.armadilha .licao { background: #f9fafb; border-left: 2.5pt solid #b8a06a; padding: 2mm 3mm;
        margin-top: 2.5mm; font-size: 9.5pt; }

.exercicio { page-break-inside: avoid; margin-bottom: 6mm; }
.ex-head { display: flex; align-items: baseline; gap: 3mm; margin-bottom: 2mm; }
.ex-num { font-family: 'Helvetica Neue', sans-serif; font-weight: 700; font-size: 13pt; color: #d1d5db; }
.ex-titulo { font-family: 'Helvetica Neue', sans-serif; font-weight: 700; font-size: 11pt; flex: 1; }
.selo { font-family: 'Helvetica Neue', sans-serif; font-size: 7.5pt; text-transform: uppercase;
        letter-spacing: .08em; padding: .6mm 2mm; border-radius: 2px; white-space: nowrap; }
.selo.mongodb { background: #e6f2ee; color: #00684A; }
.selo.elasticsearch { background: #e5eff7; color: #0B64A0; }
.selo.integrador { background: #f0ecf7; color: #5b4a8a; }
.selo.vetorial { background: #f7efe6; color: #8a6034; }
.selo.basico { background: #f3f4f6; color: #6b7280; }
.selo.intermediario { background: #fdf6e3; color: #8a7333; }
.selo.desafio { background: #fdf0ef; color: #a63d35; }
.solucao { background: #f9fafb; border: 1px solid #e5e7eb; padding: 3mm 3.5mm; margin-top: 2.5mm; }
.solucao .rotulo { font-family: 'Helvetica Neue', sans-serif; font-size: 7.5pt; text-transform: uppercase;
        letter-spacing: .1em; color: #6b7280; font-weight: 700; display: block; margin-bottom: 1.5mm; }

.questao { page-break-inside: avoid; margin-bottom: 4.5mm; }
.questao .enunciado { font-weight: 600; margin-bottom: 1.5mm; }
.questao ol { list-style: upper-alpha; font-size: 10pt; margin-bottom: 1.5mm; }
.gabarito { font-size: 9pt; background: #f9fafb; border-left: 2.5pt solid #6b7280;
        padding: 2mm 3mm; }
.gabarito b { color: #111; }

.glossario { column-count: 2; column-gap: 8mm; font-size: 9.5pt; }
.glossario dt { font-family: 'Helvetica Neue', sans-serif; font-weight: 700; font-size: 9pt; }
.glossario dd { margin: 0; }
.glossario dl { margin: 0; }
.verbete { break-inside: avoid; page-break-inside: avoid; margin-bottom: 2.5mm; }
"""

CORES = {'mongo': '#00684A', 'elastic': '#0B64A0', 'sintese': '#5b4a8a', 'neutro': '#374151'}

out = []
A = out.append

A('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">')
A('<title>NoSQL na prática: do documento ao índice invertido</title>')
A(f'<style>{CSS}</style></head><body>')

# ---------------- capa ----------------
mods = d.get('modulos', [])
total_min = d.get('duracao_total_min', 0)
n_ex = len(d.get('exercicios', []))
n_arm = len(d.get('armadilhas', []))
n_quiz = len(d.get('avaliacao', {}).get('quiz', []))

A('<div class="capa">')
A('<div class="disciplina">Bancos de Dados N&atilde;o Relacionais &middot; CEUB</div>')
A('<h1>NoSQL na pr&aacute;tica:<br>do documento ao<br>&iacute;ndice invertido</h1>')
A('<div class="sub">Uma aula construída sobre dois laboratórios &mdash;<br>MongoDB como sistema de registro, Elastic Stack como camada de busca.</div>')
A('<div class="regua"></div>')
A('<dl>')
A('<dt>Disciplina</dt><dd>Bancos de Dados N&atilde;o Relacionais</dd>')
A('<dt>Professor</dt><dd>Raul Carvalho de Souza</dd>')
A('<dt>Aluno</dt><dd>Guilherme Levi</dd>')
A(f'<dt>Dura&ccedil;&atilde;o</dt><dd>{total_min} minutos &middot; {len(mods)} m&oacute;dulos</dd>')
A('<dt>Base</dt><dd>Lab 1 &mdash; MongoDB 8.2 &middot; Lab 2 &mdash; Elasticsearch 8.15, Kibana e Logstash</dd>')
A('</dl>')
A(f'<div class="rodape-capa">Todo comando e toda sa&iacute;da deste material foram executados de verdade '
  f'nos dois laborat&oacute;rios. Inclui {n_ex} exerc&iacute;cios, {n_arm} armadilhas reais de ambiente '
  f'e {n_quiz} quest&otilde;es de avalia&ccedil;&atilde;o.</div>')
A('</div>')

# ---------------- sumario ----------------
A('<div class="sumario"><h2>Sum&aacute;rio</h2><ul class="toc">')
for i, m in enumerate(mods):
    A(f'<li><span class="n">M&oacute;d. {i+1}</span><span class="t">{e(m.get("titulo"))}</span>'
      f'<span class="d">{m.get("duracao_min", 0)} min</span></li>')
A('<li class="grupo">Material complementar</li>')
A(f'<li><span class="n">A</span><span class="t">O que o roteiro n&atilde;o conta: armadilhas reais</span><span class="d">{n_arm} casos</span></li>')
A(f'<li><span class="n">B</span><span class="t">Exerc&iacute;cios com solu&ccedil;&atilde;o comentada</span><span class="d">{n_ex} exerc&iacute;cios</span></li>')
A(f'<li><span class="n">C</span><span class="t">Avalia&ccedil;&atilde;o, tabela de decis&atilde;o e gloss&aacute;rio</span><span class="d">{n_quiz} quest&otilde;es</span></li>')
A('</ul></div>')

# ---------------- modulos ----------------
for i, m in enumerate(mods):
    t = tema_de(i, m)
    A(f'<section class="modulo" style="--cor:{CORES[t]}">')
    A('<div class="modulo-head">')
    A(f'<span class="num">M&oacute;dulo {i+1}</span><span class="dur">{m.get("duracao_min", 0)} minutos</span>')
    A('</div>')
    A(f'<h2>{e(m.get("titulo"))}</h2>')
    if m.get('abertura'):
        A(f'<div class="abertura">{e(m["abertura"])}</div>')
    if m.get('objetivos'):
        A('<h3>Objetivos de aprendizagem</h3><ul>')
        for o in m['objetivos']:
            A(f'<li>{e(o)}</li>')
        A('</ul>')
    if m.get('conceitos'):
        A('<h3>Conceitos</h3>')
        for c in m['conceitos']:
            A('<div class="conceito">')
            A(f'<h4>{e(c.get("nome"))}</h4>')
            A(para(c.get('explicacao')))
            if c.get('analogia'):
                A(f'<div class="caixa analogia"><span class="rotulo">Analogia</span><p>{e(c["analogia"])}</p></div>')
            if c.get('erro_comum'):
                A(f'<div class="caixa erro"><span class="rotulo">Erro comum</span><p>{e(c["erro_comum"])}</p></div>')
            A('</div>')
    if m.get('demos'):
        A('<h3>Na pr&aacute;tica</h3>')
        for dm in m['demos']:
            A('<div class="demo">')
            A(f'<h4>{e(dm.get("titulo"))}</h4>')
            A(f'<pre class="codigo">{e(dm.get("codigo"))}</pre>')
            if dm.get('saida'):
                A('<p class="rot-saida">Sa&iacute;da real</p>')
                A(f'<pre class="saida">{e(dm["saida"])}</pre>')
            A(f'<p class="explica">{e(dm.get("explicacao"))}</p>')
            if dm.get('fonte'):
                A(f'<p class="fonte">{e(dm["fonte"])}</p>')
            A('</div>')
    if m.get('fechamento'):
        A(f'<div class="fechamento"><span class="rotulo">Fechamento</span>{para(m["fechamento"])}</div>')
    if m.get('perguntas'):
        A('<div class="perguntas"><h3>Para discutir em sala</h3><ol>')
        for p in m['perguntas']:
            A(f'<li>{e(p)}</li>')
        A('</ol></div>')
    A('</section>')

# ---------------- armadilhas ----------------
arms = d.get('armadilhas', [])
if arms:
    A('<section class="secao"><h2>Anexo A &mdash; O que o roteiro n&atilde;o conta</h2>')
    A('<p class="intro">Problemas que aconteceram de verdade ao executar os dois laborat&oacute;rios nesta '
      'm&aacute;quina. Cada um traz o sintoma, a causa raiz e a li&ccedil;&atilde;o generaliz&aacute;vel.</p>')
    for a in arms:
        A('<div class="armadilha">')
        A(f'<h4>{e(a.get("titulo"))} <span class="tag">{e(a.get("sistema"))}</span></h4>')
        A('<dl>')
        A(f'<dt>Sintoma</dt><dd>{e(a.get("sintoma"))}</dd>')
        A(f'<dt>Causa raiz</dt><dd>{e(a.get("causa_raiz"))}</dd>')
        if a.get('diagnostico'):
            A(f'<dt>Diagn&oacute;stico</dt><dd>{e(a["diagnostico"])}</dd>')
        A(f'<dt>Corre&ccedil;&atilde;o</dt><dd>{e(a.get("correcao"))}</dd>')
        A('</dl>')
        if a.get('evidencia'):
            A(f'<pre class="saida">{e(a["evidencia"])}</pre>')
        A(f'<div class="licao"><b>Li&ccedil;&atilde;o:</b> {e(a.get("licao"))}</div>')
        A('</div>')
    A('</section>')

# ---------------- exercicios ----------------
exs = d.get('exercicios', [])
if exs:
    A('<section class="secao"><h2>Anexo B &mdash; Exerc&iacute;cios</h2>')
    A('<p class="intro">N&atilde;o repetem o passo a passo dos laborat&oacute;rios: exigem transferir o que '
      'foi aprendido para um problema novo. As solu&ccedil;&otilde;es rodam nos ambientes dos labs.</p>')
    for x in exs:
        A('<div class="exercicio">')
        A('<div class="ex-head">')
        A(f'<span class="ex-num">{x.get("numero", "")}</span>')
        A(f'<span class="ex-titulo">{e(x.get("titulo"))}</span>')
        sis = (x.get('sistema') or '').lower()
        dif = (x.get('dificuldade') or '').lower()
        A(f'<span class="selo {sis}">{e(x.get("sistema"))}</span>')
        A(f'<span class="selo {dif}">{e(x.get("dificuldade"))}</span>')
        if x.get('tempo_min'):
            A(f'<span class="selo basico">{x["tempo_min"]} min</span>')
        A('</div>')
        A(para(x.get('enunciado')))
        if x.get('esperado'):
            A(f'<p><b>Espera-se:</b> {e(x["esperado"])}</p>')
        A('<div class="solucao"><span class="rotulo">Solu&ccedil;&atilde;o</span>')
        A(f'<pre class="codigo">{e(x.get("solucao_codigo"))}</pre>')
        A(para(x.get('solucao_comentario')))
        if x.get('criterio_correcao'):
            A(f'<p style="font-size:9pt;color:#6b7280;margin:0"><b>Crit&eacute;rio de corre&ccedil;&atilde;o:</b> {e(x["criterio_correcao"])}</p>')
        A('</div></div>')
    A('</section>')

# ---------------- avaliacao ----------------
av = d.get('avaliacao', {})
if av.get('quiz'):
    A('<section class="secao"><h2>Anexo C &mdash; Avalia&ccedil;&atilde;o</h2>')
    A('<p class="intro">Quest&otilde;es de racioc&iacute;nio, n&atilde;o de memoriza&ccedil;&atilde;o de sintaxe. '
      'O gabarito explica por que cada alternativa errada &eacute; tentadora.</p>')
    for q in av['quiz']:
        A('<div class="questao">')
        A(f'<p class="enunciado">{q.get("numero", "")}. {e(q.get("pergunta"))}</p>')
        A('<ol>')
        for alt in q.get('alternativas', []):
            A(f'<li>{e(re.sub(r"^[A-D][)., ]+", "", str(alt)))}</li>')
        A('</ol>')
        A(f'<div class="gabarito"><b>Resposta: {e(q.get("correta"))}</b> &mdash; {e(q.get("justificativa"))}</div>')
        A('</div>')

if av.get('tabela_decisao'):
    A('<h3 style="margin-top:8mm">Tabela de decis&atilde;o</h3>')
    A('<table><tr><th style="width:42%">Requisito</th><th style="width:16%">Sistema</th><th>Por qu&ecirc;</th></tr>')
    for r in av['tabela_decisao']:
        A(f'<tr><td>{e(r.get("requisito"))}</td><td>{e(r.get("sistema"))}</td><td>{e(r.get("porque"))}</td></tr>')
    A('</table>')

if av.get('glossario'):
    A('<h3 style="margin-top:8mm">Gloss&aacute;rio</h3><div class="glossario"><dl>')
    for g in av['glossario']:
        A(f'<div class="verbete"><dt>{e(g.get("termo"))}</dt>'
          f'<dd>{e(g.get("definicao"))}</dd></div>')
    A('</dl></div>')

if av.get('leituras'):
    A('<h3 style="margin-top:8mm">Para ir al&eacute;m</h3><ul>')
    for l in av['leituras']:
        A(f'<li>{e(l)}</li>')
    A('</ul>')

if av.get('quiz'):
    A('</section>')

A('</body></html>')

open(saida, 'w').write('\n'.join(out))
print(f'HTML montado: {saida} ({len(chr(10).join(out))//1024} KB)')
print(f'modulos={len(mods)} exercicios={n_ex} armadilhas={n_arm} quiz={n_quiz} duracao={total_min}min')
