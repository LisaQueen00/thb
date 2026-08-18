from fastapi import FastAPI

from thb_input import __version__
from thb_input.api.v1.extract import router as extract_router
from thb_input.api.v1.input import router as input_router
from thb_input.api.v1.strip import router as strip_router
from thb_input.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
)

app.include_router(input_router, prefix="/api/v1")
app.include_router(strip_router, prefix="/api/v1")
app.include_router(extract_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
