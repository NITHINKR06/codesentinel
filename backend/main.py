from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
import asyncio
import signal

from api.routes import scan, report, github, ws
from db.database import init_db

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("CodeSentinel API starting up")
    await init_db()

    # Handle termination signals gracefully
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(app.shutdown()))
        except NotImplementedError:
            # Fallback for Windows or systems where add_signal_handler is not available
            pass

    yield
    log.info("CodeSentinel API shutting down")


async def shutdown():
    """Cleanup logic on process termination"""
    log.info("Graceful shutdown initiated")
    # Add any specific cleanup here (e.g. closing background tasks)


app = FastAPI(
    title="CodeSentinel API",
    description="Automated security analysis — find vulns, prove them, fix them.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix="/api/scan", tags=["scan"])
app.include_router(report.router, prefix="/api/report", tags=["report"])
app.include_router(github.router, prefix="/api/github", tags=["github"])
app.include_router(ws.router, tags=["websocket"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "CodeSentinel"}
