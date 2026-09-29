#!/bin/bash
# Funcoes de captura de evidencia do laboratorio Redis.
# Cada comando e executado de verdade no container e a saida vai para o markdown.

R="docker exec -i redis redis-cli"
OUT="${OUT:?defina OUT com o arquivo de saida}"

sec()  { { echo ""; echo "## $1"; } >> "$OUT"; }
sub()  { { echo ""; echo "### $1"; } >> "$OUT"; }
txt()  { { echo ""; echo "$1"; } >> "$OUT"; }
nota() { { echo ""; echo "> $1"; } >> "$OUT"; }

# cmd "COMANDO"  -> um comando, conexao propria
cmd() {
  local c="$1"
  { echo ""; echo '```'; echo "$c"; echo '```'; echo ""; echo "**Saída:**"; echo ""; echo '```'
    echo "$c" | $R 2>&1
    echo '```'; } >> "$OUT"
  echo "  . $c"
}

# cmds "CMD1" "CMD2" ...  -> varios comandos independentes, um bloco so no markdown
cmds() {
  local saida="" c
  { echo ""; echo '```'; for c in "$@"; do echo "$c"; done; echo '```'; echo ""; echo "**Saída:**"; echo ""; echo '```'; } >> "$OUT"
  for c in "$@"; do
    saida="$(echo "$c" | $R 2>&1)"
    printf '%s\n' "$saida" >> "$OUT"
  done
  echo '```' >> "$OUT"
  echo "  . (${#@} comandos)"
}

# sessao "CMD1" "CMD2" ...  -> TODOS na MESMA conexao (obrigatorio para MULTI/EXEC e SELECT)
sessao() {
  local c
  { echo ""; echo '```'; for c in "$@"; do echo "$c"; done; echo '```'; echo ""
    echo "**Saída (uma única conexão):**"; echo ""; echo '```'; } >> "$OUT"
  printf '%s\n' "$@" | $R 2>&1 >> "$OUT"
  echo '```' >> "$OUT"
  echo "  . sessao com ${#@} comandos"
}

# shell "comando de shell"  -> executa no host, para docker restart etc.
shell() {
  local c="$1"
  { echo ""; echo '```bash'; echo "$ $c"; echo '```'; echo ""; echo "**Saída:**"; echo ""; echo '```'
    eval "$c" 2>&1
    echo '```'; } >> "$OUT"
  echo "  \$ $c"
}

# info "secao" "regex dos campos"  -> INFO filtrado, porque a saida crua e enorme
info() {
  local s="$1" campos="$2"
  { echo ""; echo '```'; echo "INFO $s"; echo '```'; echo ""
    echo "**Saída (só os campos que interessam, o INFO completo traz dezenas de linhas):**"; echo ""; echo '```'
    echo "INFO $s" | $R 2>&1 | grep -E "$campos" | tr -d '\r'
    echo '```'; } >> "$OUT"
  echo "  . INFO $s"
}
