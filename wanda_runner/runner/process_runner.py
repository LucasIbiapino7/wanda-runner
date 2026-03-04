import multiprocessing
import time
from typing import Any


def _worker(code: str, function_name: str, args: list, result_queue: multiprocessing.Queue):
    try:
        local_env = {}
        exec(code, {}, local_env)
        fn = local_env[function_name]
        output = fn(*args)
        result_queue.put({"ok": True, "output": output})
    except Exception as e:
        result_queue.put({"ok": False, "error": str(e)})


def run_case(code: str, function_name: str, args: list, timeout_ms: int) -> dict[str, Any]:
    timeout_sec = timeout_ms / 1000
    queue = multiprocessing.Queue()

    process = multiprocessing.Process(target=_worker, args=(code, function_name, args, queue))

    start = time.monotonic()
    process.start()
    process.join(timeout=timeout_sec)
    runtime_ms = int((time.monotonic() - start) * 1000)

    if process.is_alive():
        process.kill()
        process.join()
        return {"ok": False, "timed_out": True, "error": "Tempo limite de execução atingido.","runtime_ms": runtime_ms
        }

    if queue.empty():
        return {
            "ok": False, "timed_out": False, "error": "Processo encerrou sem retornar resultado.","runtime_ms": runtime_ms
        }

    result = queue.get()
    return {"ok": result["ok"], "timed_out": False, "output": result.get("output"), "error": result.get("error"),
        "runtime_ms": runtime_ms
    }