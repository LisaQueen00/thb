from fastapi import APIRouter, status

from thb_input.schemas.input import InputRecord, TextInputRequest
from thb_input.services.text_input import build_text_input_record

router = APIRouter(prefix="/input", tags=["input"])


@router.post("/text", response_model=InputRecord, status_code=status.HTTP_201_CREATED)
def create_text_input(payload: TextInputRequest) -> InputRecord:
    """Convert pasted communication text into THB's standard input contract."""
    return build_text_input_record(payload)
