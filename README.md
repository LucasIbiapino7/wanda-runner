# wanda-runner

Serviço responsável por executar código Python de alunos de forma isolada e segura. Cada execução roda em um processo filho separado com timeout duro — se o código travar, o processo é morto e o servidor continua vivo.

---

## Rodando localmente

**Pré-requisitos:** Docker instalado.

```bash
# 1. Clone o projeto
git clone <url-do-repo>
cd wanda-runner

# 2. Copie o arquivo de configuração
cp .env.example .env

# 3. Suba o container
docker-compose up --build
```

O serviço estará disponível em `http://localhost:8001`.

---

## Endpoints

### `GET /health`
Verifica se o serviço está no ar.

```bash
curl http://localhost:8001/health
```

Resposta:
```json
{"status": "ok"}
```

---

### `POST /run-tests`
Executa uma função Python contra uma lista de casos de teste.

**Body:**
| Campo | Tipo | Descrição |
|---|---|---|
| `code` | string | Código Python completo do aluno |
| `function_name` | string | Nome da função a ser chamada |
| `test_cases` | array de arrays | Cada item é a lista de argumentos de um caso |
| `timeout_ms_per_case` | int | Timeout por caso (ms) |
| `timeout_ms_total` | int | Timeout total da suite (ms) |

---

## Exemplos no Postman

Configure o Postman com:
- Method: `POST`
- URL: `http://localhost:8001/run-tests`
- Body: `raw` → `JSON`

---

###  Código real que derrubou o servidor na última vez

```json
{
    "code": "def strategy(bit8, bit16, bit32, firewall, opp_last):\n    x=\"true\"\n    y=\"false\"\n    while x==\"true\" and y==\"false\":\n        print(x or x)\n        print(x or y)\n        print(y or x)\n        print(y or y)\n        if x==\"true\" and y==\"false\":\n            del(x,y)\n            break\n        else:\n            print(x and x)\n            print(x and y)",
    "function_name": "strategy",
    "test_cases": [[1, 0, 1, 0, "BIT32"]],
    "timeout_ms_per_case": 1000,
    "timeout_ms_total": 5000
}
```

Resposta esperada: `all_ok: true`, `output: null`. O código termina por causa do `break`, mas não retorna nada — no jogo isso vira fallback.

---

### Variação sem o break — loop infinito real

A versão sem o `break` é o loop infinito que realmente derrubaria o servidor.

```json
{
    "code": "def strategy(bit8, bit16, bit32, firewall, opp_last):\n    x=\"true\"\n    y=\"false\"\n    while x==\"true\" and y==\"false\":\n        print(x or x)",
    "function_name": "strategy",
    "test_cases": [[1, 0, 1, 0, "BIT32"]],
    "timeout_ms_per_case": 1000,
    "timeout_ms_total": 5000
}
```

Resposta esperada: `all_ok: false`, `first_failure.timed_out: true`. O processo filho é morto após 1 segundo e o servidor continua vivo normalmente.

---

## Rodando os testes

```bash
poetry shell
pytest tests/ -v
```

---

## Variáveis de ambiente

Copie `.env.example` para `.env` e ajuste se necessário.

| Variável | Padrão | Descrição |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `MAX_TIMEOUT_MS_PER_CASE` | `2000` | Timeout máximo por caso (ms) |
| `MAX_TIMEOUT_MS_TOTAL` | `10000` | Timeout máximo total da suite (ms) |
