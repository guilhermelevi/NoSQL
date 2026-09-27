#!/bin/bash
# Regenera a aula em PDF a partir do conteudo em Python.
#   ./gerar.sh   ->  ../AULA-NoSQL.pdf
#
# Ordem dos modulos:
#   conteudo_a  contexto + MongoDB (4)
#   conteudo_b  Elasticsearch (3)
#   conteudo_d  Redis (3)
#   conteudo_e  sintese dos tres sistemas (1)
# Anexos: conteudo_c (Mongo/Elastic) + conteudo_f (Redis)
set -e
cd "$(dirname "$0")"
python3 - <<'PY'
import json, importlib.util
def carrega(n):
    s = importlib.util.spec_from_file_location(n, f"{n}.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

a, b, c = carrega('conteudo_a'), carrega('conteudo_b'), carrega('conteudo_c')
d, e, f = carrega('conteudo_d'), carrega('conteudo_e'), carrega('conteudo_f')

mods = a.MODULOS + b.MODULOS + d.MODULOS + e.MODULOS

json.dump({
    'modulos': mods,
    'duracao_total_min': sum(m['duracao_min'] for m in mods),
    'armadilhas': c.ARMADILHAS + f.ARMADILHAS,
    'exercicios': c.EXERCICIOS + f.EXERCICIOS,
    'avaliacao': {
        'quiz': c.QUIZ + f.QUIZ,
        'tabela_decisao': c.TABELA_DECISAO + f.TABELA_DECISAO,
        'glossario': c.GLOSSARIO + f.GLOSSARIO,
        'leituras': c.LEITURAS + f.LEITURAS,
    },
}, open('aula.json', 'w'), ensure_ascii=False, indent=1)

print(f"{len(mods)} modulos, {sum(m['duracao_min'] for m in mods)} min")
for i, m in enumerate(mods, 1):
    print(f"  {i:>2}. [{m.get('tema','?'):<7}] {m['titulo'][:52]:<52} {m['duracao_min']:>3} min")
PY
python3 montar.py aula.json aula.html
node pdf.mjs aula.html ../AULA-NoSQL.pdf
