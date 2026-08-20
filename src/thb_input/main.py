from fastapi import FastAPI

from thb_input import __version__
from thb_input.api.v1.thb import router as thb_router
from thb_input.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version=__version__)
app.include_router(thb_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
