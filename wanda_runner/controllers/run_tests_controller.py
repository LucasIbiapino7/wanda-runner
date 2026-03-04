from fastapi import APIRouter
from wanda_runner.schemas.run_tests_dto import RunTestsRequest, RunTestsResponse
from wanda_runner.services.run_tests_service import RunTestsService

router = APIRouter()
service = RunTestsService()

@router.post("/run-tests", response_model=RunTestsResponse)
def run_tests(request: RunTestsRequest) -> RunTestsResponse:
    return service.run(request)