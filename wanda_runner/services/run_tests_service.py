import time
import structlog

from wanda_runner.schemas.run_tests_dto import (RunTestsRequest, RunTestsResponse, CompileStatus, LoadStatus,
    CaseResult, FirstFailure, Stats,)
from wanda_runner.runner.process_runner import run_case
from wanda_runner.settings import settings

logger = structlog.get_logger()

class RunTestsService:
    def run(self, request: RunTestsRequest) -> RunTestsResponse:
        timeout_per_case = min(request.timeout_ms_per_case, settings.max_timeout_ms_per_case)
        timeout_total = min(request.timeout_ms_total, settings.max_timeout_ms_total)

        # COMPILALAÇÃO 
        try:
            compile(request.code, "<student>", "exec")
            compile_status = CompileStatus(ok=True)
        except SyntaxError as e:
            logger.error("compilacao_falhou", erro=str(e))
            return RunTestsResponse(suite_error="compile_error", suite_error_message=str(e), all_ok=False,
                compile=CompileStatus(ok=False, error_type="compile_error", error_message=str(e)),
                load=LoadStatus(ok=False),)

        # LOAD
        try:
            local_env = {}
            exec(request.code, {}, local_env)
            load_status = LoadStatus(ok=True)
        except Exception as e:
            logger.error("carregamento_falhou", erro=str(e))
            return RunTestsResponse(suite_error="load_error", suite_error_message=str(e), all_ok=False,
                compile=compile_status,load=LoadStatus(ok=False, error_type="load_error", error_message=str(e)),
            )

        # FUNCAO EXISTE?
        if request.function_name not in local_env:
            logger.error("funcao_nao_encontrada", nome_funcao=request.function_name)
            return RunTestsResponse(suite_error="function_not_found", suite_error_message=f"Função '{request.function_name}' não encontrada.",
                all_ok=False, compile=compile_status,load=load_status,
            )

        # RUN CASOS DE TESTE
        results: list[CaseResult] = []
        first_failure: FirstFailure | None = None
        suite_start = time.monotonic()
        
        logger.info("execucao_iniciada", nome_funcao=request.function_name, total_casos=len(request.test_cases))
        
        for index, args in enumerate(request.test_cases):

            elapsed_ms = int((time.monotonic() - suite_start) * 1000)
            if elapsed_ms >= timeout_total:
                logger.warning("timeout_total_atingido", tempo_decorrido_ms=elapsed_ms, indice_caso=index)
                return _suite_timeout_response(compile_status, load_status, results, request, elapsed_ms)

            result = run_case(code=request.code, function_name=request.function_name, args=args,
                timeout_ms=timeout_per_case,
            )

            case = CaseResult(
                index=index,
                ok=result["ok"],
                output=result.get("output"),
                error_type="timeout" if result.get("timed_out") else ("runtime_error" if not result["ok"] else None),
                error_message=result.get("error"),
                runtime_ms=result["runtime_ms"],
                timed_out=result.get("timed_out", False),
            )
            results.append(case)

            if not case.ok:
                first_failure = FirstFailure(
                    index=index,
                    error_type=case.error_type,
                    error_message=case.error_message,
                    timed_out=case.timed_out,
                    runtime_ms=case.runtime_ms,
                )
                logger.warning("caso_falhou", indice=index, tipo_erro=case.error_type, mensagem_erro=case.error_message)
                break

        # STATS 
        total_runtime_ms = sum(c.runtime_ms for c in results)
        ok_cases = sum(1 for c in results if c.ok)
        timeout_cases = sum(1 for c in results if c.timed_out)
        failed_cases = len(results) - ok_cases
        all_ok = first_failure is None

        stats = Stats(
            total_cases=len(request.test_cases),
            executed_cases=len(results),
            ok_cases=ok_cases,
            failed_cases=failed_cases,
            timeout_cases=timeout_cases,
            total_runtime_ms=total_runtime_ms,
        )

        logger.info("execucao_concluida", nome_funcao=request.function_name, tudo_ok=all_ok, casos_ok=ok_cases, casos_falhos=failed_cases, tempo_total_ms=total_runtime_ms)
        return RunTestsResponse(
            suite_error=None,
            suite_error_message=None,
            all_ok=all_ok,
            first_failure=first_failure,
            compile=compile_status,
            load=load_status,
            results=results,
            stats=stats,
        )


def _suite_timeout_response(compile_status, load_status, results, request, elapsed_ms) -> RunTestsResponse:
    ok_cases = sum(1 for c in results if c.ok)
    timeout_cases = sum(1 for c in results if c.timed_out)
    return RunTestsResponse(
        suite_error="suite_timeout",
        suite_error_message=f"Timeout total da suite atingido após {elapsed_ms}ms.",
        all_ok=False,
        compile=compile_status,
        load=load_status,
        results=results,
        stats=Stats(
            total_cases=len(request.test_cases),
            executed_cases=len(results),
            ok_cases=ok_cases,
            failed_cases=len(results) - ok_cases,
            timeout_cases=timeout_cases,
            total_runtime_ms=elapsed_ms,
        ),
    )