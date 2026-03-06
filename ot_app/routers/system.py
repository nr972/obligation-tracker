"""System endpoints: health check, config, demo data, shutdown."""

import logging
import os
import signal
import threading

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ot_app import __version__
from ot_app.config import settings
from ot_app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get("/health")
def health_check():
    return {"status": "ok", "version": __version__}


@router.get("/config/mode")
def get_mode():
    return {
        "ai_enabled": settings.ai_enabled,
        "demo_mode": settings.DEMO_MODE,
    }


@router.post("/demo/load")
def load_demo_data(db: Session = Depends(get_db)):
    from ot_app.services.demo_service import load_sample_data

    count = load_sample_data(db)
    return {"loaded": count}


@router.post("/demo/reset")
def reset_demo_data(db: Session = Depends(get_db)):
    from ot_app.services.demo_service import clear_sample_data

    count = clear_sample_data(db)
    return {"cleared": count}


@router.post("/shutdown")
def shutdown():
    """Initiate graceful shutdown of the server process group.

    Sends SIGTERM to the process group after a short delay so the HTTP
    response is returned to the caller first. The startup script's trap
    handler takes care of cleaning up all child processes.
    """
    def _shutdown():
        import time
        time.sleep(0.5)
        logger.info("Shutdown requested via API — sending SIGTERM to process group")
        try:
            # Send SIGTERM to the entire process group so the startup
            # script's trap fires and cleans up both API and frontend.
            os.killpg(os.getpgid(os.getpid()), signal.SIGTERM)
        except ProcessLookupError:
            pass
        except OSError:
            # Fallback: terminate just this process
            os.kill(os.getpid(), signal.SIGTERM)

    threading.Thread(target=_shutdown, daemon=True).start()
    return {"status": "shutting_down"}
