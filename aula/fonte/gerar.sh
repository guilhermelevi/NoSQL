#!/bin/bash
# Regenera a aula em PDF a partir do conteudo em Python.
#   ./gerar.sh   ->  ../AULA-NoSQL.pdf
set -e
cd "$(dirname "$0")"
python3 - <<'PY'
import json, importlib.util
def carrega(n):
    s = importlib.util.spec_from_file_location(n, f"{n}.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
a, b, c = carrega('conteudo_a'), carrega('conteudo_b'), carrega('conteudo_c')
mods = a.MODULOS + b.MODULOS
json.dump({'modulos': mods,
           'duracao_total_min': sum(m['duracao_min'] for m in mods),
           'armadilhas': c.ARMADILHAS, 'exercicios': c.EXERCICIOS,
           'avaliacao': {'quiz': c.QUIZ, 'tabela_decisao': c.TABELA_DECISAO,
                         'glossario': c.GLOSSARIO, 'leituras': c.LEITURAS}},
          open('aula.json','w'), ensure_ascii=False, indent=1)
PY
python3 montar.py aula.json aula.html
node pdf.mjs aula.html ../AULA-NoSQL.pdf
