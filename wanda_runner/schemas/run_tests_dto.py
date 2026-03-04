from pydantic import BaseModel
from typing import Any, Optional

class RunTestsRequest(BaseModel):
    code: str
    function_name: str
    test_cases: list[list[Any]]
    timeout_ms_per_case: int
    timeout_ms_total: int


# RESPONSE
class CompileStatus(BaseModel):
    ok: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class LoadStatus(BaseModel):
    ok: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class CaseResult(BaseModel):
    index: int
    ok: bool
    output: Optional[Any] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    runtime_ms: int
    timed_out: bool


class FirstFailure(BaseModel):
    index: int
    error_type: str
    error_message: Optional[str] = None
    timed_out: bool
    runtime_ms: int


class Stats(BaseModel):
    total_cases: int
    executed_cases: int
    ok_cases: int
    failed_cases: int
    timeout_cases: int
    total_runtime_ms: int


class RunTestsResponse(BaseModel):
    suite_error: Optional[str] = None
    suite_error_message: Optional[str] = None
    all_ok: bool
    first_failure: Optional[FirstFailure] = None
    compile: CompileStatus
    load: LoadStatus
    results: Optional[list[CaseResult]] = None
    stats: Optional[Stats] = None