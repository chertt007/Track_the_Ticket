from aws_xray_sdk.core import xray_recorder, patch_all

from app.logging_config import get_logger

logger = get_logger(__name__)


def setup_tracing(environment: str = "local") -> None:
    """
    Configure AWS X-Ray tracing.

    In local/test environments X-Ray is disabled — no daemon is running locally.

    In production, Lambda automatically creates the root X-Ray segment for each
    invocation (because tracing_config { mode = "Active" } is set in Terraform).
    We only need patch_all() to add subsegments for AWS SDK and DB calls.

    How it works in Lambda:
      1. API Gateway → Lambda: Lambda runtime opens the root segment automatically
      2. patch_all() patches boto3, httpx, SQLAlchemy — their calls become
         subsegments automatically
      3. Lambda daemon batches segments and sends them to X-Ray service
      4. AWS Console → X-Ray → Service Map shows the full call graph:
           API Gateway → Lambda (FastAPI) → RDS / S3

    IAM requirement (set in TF-API-01):
      Lambda execution role must have:
        - xray:PutTraceSegments
        - xray:PutTelemetryRecords
    """
    if environment == "local":
        logger.info("X-Ray tracing disabled in local environment")
        return

    xray_recorder.configure(
        service="tracktheticket-api",
        # LOG_ERROR: if a segment is missing in async context, log instead of raising
        context_missing="LOG_ERROR",
    )

    # patch_all() monkey-patches boto3, httpx, SQLAlchemy so their calls
    # automatically appear as X-Ray subsegments — no manual instrumentation needed
    patch_all()

    logger.info(
        "X-Ray tracing enabled",
        extra={"service": "tracktheticket-api", "environment": environment},
    )
