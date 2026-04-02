from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware

from app.logging_config import get_logger

logger = get_logger(__name__)


def setup_tracing(app, environment: str = "local") -> None:
    """
    Configure AWS X-Ray tracing and attach middleware to the FastAPI app.

    In local/test environments, X-Ray is disabled — no daemon is running locally
    and we don't want to crash the app if the X-Ray daemon is unreachable.

    In prod/staging, X-Ray sends trace segments to the daemon running as a
    sidecar in Lambda (AWS manages it automatically when active tracing is on).

    How it works end-to-end:
      1. A request hits API Gateway → Lambda
      2. XRayMiddleware opens a new segment for each HTTP request
      3. patch_all() patches boto3, httpx, SQLAlchemy — their calls become
         X-Ray subsegments automatically
      4. Lambda daemon batches segments and sends to X-Ray service
      5. AWS Console → X-Ray → Service Map shows the full call graph:
           API Gateway → Lambda (FastAPI) → RDS

    IAM requirement (set in TF-API-01):
      Lambda execution role must have:
        - xray:PutTraceSegments
        - xray:PutTelemetryRecords
    """
    if environment == "local":
        logger.info("X-Ray tracing disabled in local environment")
        return

    # Configure the recorder before patching libraries
    xray_recorder.configure(
        service="tracktheticket-api",
        # In Lambda, the daemon address is set automatically via
        # AWS_XRAY_DAEMON_ADDRESS env var — no need to configure manually.
        # context_missing="LOG_ERROR" means: if a segment is missing (can
        # happen in async contexts), log an error instead of raising an exception.
        context_missing="LOG_ERROR",
    )

    # patch_all() monkey-patches supported libraries so their calls automatically
    # become X-Ray subsegments. Patches: boto3, requests, httpx, SQLAlchemy, etc.
    patch_all()

    # Attach the X-Ray middleware — wraps every request in a trace segment
    app.add_middleware(XRayMiddleware, recorder=xray_recorder)

    logger.info(
        "X-Ray tracing enabled",
        extra={"service": "tracktheticket-api", "environment": environment},
    )
