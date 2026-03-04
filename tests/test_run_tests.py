import pytest
from fastapi.testclient import TestClient
from wanda_runner.app import app
from wanda_runner.schemas.run_tests_dto import RunTestsRequest
from wanda_runner.services.run_tests_service import RunTestsService

client = TestClient(app)
service = RunTestsService()


# HELPERS

def make_request(**kwargs) -> RunTestsRequest:
    defaults = {
        "code": "def strategy(a, b, c): return a",
        "function_name": "strategy",
        "test_cases": [["pedra", "papel", "tesoura"]],
        "timeout_ms_per_case": 1000,
        "timeout_ms_total": 5000,
    }
    defaults.update(kwargs)
    return RunTestsRequest(**defaults)


# CENÁRIO 1: SUCESSO 

class TestSucesso:

    def test_all_ok_true(self):
        req = make_request(
            test_cases=[
                ["pedra", "papel", "tesoura"],
                ["papel", "pedra", "tesoura"],
            ]
        )
        res = service.run(req)
        assert res.all_ok is True

    def test_suite_error_nulo(self):
        req = make_request()
        res = service.run(req)
        assert res.suite_error is None
        assert res.suite_error_message is None

    def test_first_failure_nulo(self):
        req = make_request()
        res = service.run(req)
        assert res.first_failure is None

    def test_compile_e_load_ok(self):
        req = make_request()
        res = service.run(req)
        assert res.compile.ok is True
        assert res.load.ok is True

    def test_results_com_outputs_corretos(self):
        req = make_request(
            test_cases=[
                ["pedra", "papel", "tesoura"],
                ["papel", "pedra", "tesoura"],
            ]
        )
        res = service.run(req)
        assert len(res.results) == 2
        assert res.results[0].output == "pedra"
        assert res.results[1].output == "papel"

    def test_stats_corretos(self):
        req = make_request(
            test_cases=[
                ["pedra", "papel", "tesoura"],
                ["papel", "pedra", "tesoura"],
            ]
        )
        res = service.run(req)
        assert res.stats.total_cases == 2
        assert res.stats.executed_cases == 2
        assert res.stats.ok_cases == 2
        assert res.stats.failed_cases == 0
        assert res.stats.timeout_cases == 0

    def test_todos_casos_ok_true(self):
        req = make_request(
            test_cases=[
                ["pedra", "papel", "tesoura"],
                ["papel", "pedra", "tesoura"],
            ]
        )
        res = service.run(req)
        for case in res.results:
            assert case.ok is True
            assert case.timed_out is False
            assert case.error_type is None
            assert case.error_message is None


# CENÁRIO 2: COMPILE ERROR 

class TestCompileError:

    def test_suite_error_compile_error(self):
        req = make_request(code="def strategy(a, b, c) return a")
        res = service.run(req)
        assert res.suite_error == "compile_error"

    def test_all_ok_false(self):
        req = make_request(code="def strategy(a, b, c) return a")
        res = service.run(req)
        assert res.all_ok is False

    def test_compile_not_ok(self):
        req = make_request(code="def strategy(a, b, c) return a")
        res = service.run(req)
        assert res.compile.ok is False
        assert res.compile.error_type == "compile_error"
        assert res.compile.error_message is not None

    def test_results_nulo(self):
        req = make_request(code="def strategy(a, b, c) return a")
        res = service.run(req)
        assert res.results is None

    def test_stats_nulo(self):
        req = make_request(code="def strategy(a, b, c) return a")
        res = service.run(req)
        assert res.stats is None


# CENÁRIO 3: LOAD ERROR

class TestLoadError:

    def test_suite_error_load_error(self):
        code = "print(variavel_inexistente)\ndef strategy(a, b, c): return a"
        req = make_request(code=code)
        res = service.run(req)
        assert res.suite_error == "load_error"

    def test_all_ok_false(self):
        code = "print(variavel_inexistente)\ndef strategy(a, b, c): return a"
        req = make_request(code=code)
        res = service.run(req)
        assert res.all_ok is False

    def test_compile_ok_mas_load_falhou(self):
        code = "print(variavel_inexistente)\ndef strategy(a, b, c): return a"
        req = make_request(code=code)
        res = service.run(req)
        assert res.compile.ok is True
        assert res.load.ok is False
        assert res.load.error_type == "load_error"

    def test_results_nulo(self):
        code = "print(variavel_inexistente)\ndef strategy(a, b, c): return a"
        req = make_request(code=code)
        res = service.run(req)
        assert res.results is None


# CENÁRIO 4: FUNÇÃO NÃO ENCONTRADA 

class TestFuncaoNaoEncontrada:

    def test_suite_error_function_not_found(self):
        req = make_request(
            code="def outra_funcao(a, b, c): return a",
            function_name="strategy"
        )
        res = service.run(req)
        assert res.suite_error == "function_not_found"

    def test_all_ok_false(self):
        req = make_request(
            code="def outra_funcao(a, b, c): return a",
            function_name="strategy"
        )
        res = service.run(req)
        assert res.all_ok is False

    def test_compile_e_load_ok(self):
        req = make_request(
            code="def outra_funcao(a, b, c): return a",
            function_name="strategy"
        )
        res = service.run(req)
        assert res.compile.ok is True
        assert res.load.ok is True

    def test_suite_error_message_contem_nome_funcao(self):
        req = make_request(
            code="def outra_funcao(a, b, c): return a",
            function_name="strategy"
        )
        res = service.run(req)
        assert "strategy" in res.suite_error_message


# CENÁRIO 5: TIMEOUT POR CASO 

class TestTimeoutPorCaso:

    def test_all_ok_false(self):
        req = make_request(
            code="def strategy(a, b, c):\n    while True: pass",
            timeout_ms_per_case=500,
        )
        res = service.run(req)
        assert res.all_ok is False

    def test_first_failure_preenchido(self):
        req = make_request(
            code="def strategy(a, b, c):\n    while True: pass",
            timeout_ms_per_case=500,
        )
        res = service.run(req)
        assert res.first_failure is not None
        assert res.first_failure.timed_out is True
        assert res.first_failure.error_type == "timeout"
        assert res.first_failure.index == 0

    def test_caso_marcado_como_timeout(self):
        req = make_request(
            code="def strategy(a, b, c):\n    while True: pass",
            timeout_ms_per_case=500,
        )
        res = service.run(req)
        assert res.results[0].timed_out is True
        assert res.results[0].error_type == "timeout"
        assert res.results[0].ok is False

    def test_fail_fast_para_no_primeiro_erro(self):
        req = make_request(
            code="def strategy(a, b, c):\n    while True: pass",
            test_cases=[
                ["pedra", "papel", "tesoura"],
                ["papel", "pedra", "tesoura"],
                ["tesoura", "pedra", "papel"],
            ],
            timeout_ms_per_case=500,
        )
        res = service.run(req)
        assert len(res.results) == 1
        assert res.stats.executed_cases == 1

    def test_suite_error_nulo_em_timeout_de_caso(self):
        # timeout de caso individual não é suite_error
        req = make_request(
            code="def strategy(a, b, c):\n    while True: pass",
            timeout_ms_per_case=500,
        )
        res = service.run(req)
        assert res.suite_error is None


# CENÁRIO 6: RUNTIME ERROR 

class TestRuntimeError:

    def test_all_ok_false(self):
        req = make_request(
            code="def strategy(a, b, c):\n    raise ValueError('erro proposital')",
        )
        res = service.run(req)
        assert res.all_ok is False

    def test_first_failure_preenchido(self):
        req = make_request(
            code="def strategy(a, b, c):\n    raise ValueError('erro proposital')",
        )
        res = service.run(req)
        assert res.first_failure is not None
        assert res.first_failure.timed_out is False
        assert res.first_failure.error_type == "runtime_error"
        assert "erro proposital" in res.first_failure.error_message

    def test_caso_marcado_como_runtime_error(self):
        req = make_request(
            code="def strategy(a, b, c):\n    raise ValueError('erro proposital')",
        )
        res = service.run(req)
        assert res.results[0].ok is False
        assert res.results[0].error_type == "runtime_error"
        assert res.results[0].timed_out is False

    def test_suite_error_nulo_em_runtime_error(self):
        req = make_request(
            code="def strategy(a, b, c):\n    raise ValueError('erro proposital')",
        )
        res = service.run(req)
        assert res.suite_error is None


# CENÁRIO 7: CAP DE TIMEOUT

class TestCapDeTimeout:

    def test_cap_por_caso_e_respeitado(self):
        # pede 99999ms mas o settings limita a 2000ms
        req = make_request(
            code="def strategy(a, b, c):\n    while True: pass",
            timeout_ms_per_case=99999,
        )
        res = service.run(req)
        # deve ter terminado em no máximo ~2500ms (2000 + margem)
        assert res.results[0].runtime_ms <= 2500


# CENÁRIO 8: ENDPOINT HTTP
class TestEndpointHttp:

    def test_health(self):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

    def test_run_tests_sucesso(self):
        body = {
            "code": "def strategy(a, b, c): return a",
            "function_name": "strategy",
            "test_cases": [["pedra", "papel", "tesoura"]],
            "timeout_ms_per_case": 1000,
            "timeout_ms_total": 5000,
        }
        res = client.post("/run-tests", json=body)
        assert res.status_code == 200
        assert res.json()["all_ok"] is True

    def test_run_tests_compile_error(self):
        body = {
            "code": "def strategy(a, b, c) return a",
            "function_name": "strategy",
            "test_cases": [["pedra", "papel", "tesoura"]],
            "timeout_ms_per_case": 1000,
            "timeout_ms_total": 5000,
        }
        res = client.post("/run-tests", json=body)
        assert res.status_code == 200
        assert res.json()["suite_error"] == "compile_error"

    def test_request_invalido_retorna_422(self):
        # falta o campo function_name
        body = {
            "code": "def strategy(a): return a",
            "test_cases": [["pedra"]],
            "timeout_ms_per_case": 1000,
            "timeout_ms_total": 5000,
        }
        res = client.post("/run-tests", json=body)
        assert res.status_code == 422