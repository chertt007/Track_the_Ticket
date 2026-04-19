"""
Agent: given an airline display name, find the official website URL online.

Used as a fallback when the `airlines` DB table doesn't yet know about an
airline. The result is cached in the DB by the caller so the agent runs
at most once per airline.
"""
import logging
import os
from typing import Optional

from langfuse import observe
from pydantic import BaseModel

from browser_use import Agent, Browser
from browser_use.llm import ChatOpenRouter

logger = logging.getLogger(__name__)

# Toggle browser visibility here. Flip to True when we want to run on a
# server without a display; keep False in local dev to watch the agent work.
HEADLESS = False

# OpenRouter model. Format: "<provider>/<model>". Catalog: https://openrouter.ai/models
# Suggested:
#   "google/gemini-2.5-flash"     — cheap + fast + vision, good default
#   "anthropic/claude-sonnet-4-6" — best quality, higher cost
#   "openai/gpt-4o"               — balanced
LLM_MODEL = "google/gemini-2.5-flash"


class _AirlineUrlResult(BaseModel):
    """Structured output — forces the agent to return a clean URL string."""
    url: Optional[str] = None


@observe(name="find_airline_url_online")
async def find_airline_url_online(airline_name: str) -> Optional[str]:
    """
    Run a browser-use agent to find the airline's official website URL.

    Returns:
        The root URL (e.g. "https://pobeda.aero") or None if the agent could
        not find it or the run failed.
    """
    logger.info(f"[agent:airline_url_finder] starting for '{airline_name}'")

    task = (
        f"Find the official website URL of the airline '{airline_name}'. "
        f"Return only the root URL of the airline's official site "
        f"(e.g. https://pobeda.aero, not a search result page). "
        f"(e.g. https://www.elal.com, not a search result page). "
        f"If you cannot find it with confidence, return null."
    )

    try:
        agent = Agent(
            task=task,
            llm=ChatOpenRouter(
                model=LLM_MODEL,
                api_key=os.environ.get("OPENROUTER_API_KEY"),
            ),
            browser=Browser(is_local=True, headless=HEADLESS),
            output_model_schema=_AirlineUrlResult,
            max_actions_per_step=3,
            max_failures=2,
        )
        history = await agent.run()
    except Exception as exc:
        logger.error(f"[agent:airline_url_finder] agent run failed: {exc}", exc_info=True)
        return None

    # With output_model_schema set, final_result is a Pydantic instance (or JSON string).
    result = history.final_result()
    if result is None:
        logger.warning(f"[agent:airline_url_finder] no result for '{airline_name}'")
        return None

    # final_result may be a string (JSON) or already parsed — handle both.
    if isinstance(result, str):
        try:
            parsed = _AirlineUrlResult.model_validate_json(result)
        except Exception as exc:
            logger.warning(f"[agent:airline_url_finder] could not parse result: {result!r} ({exc})")
            return None
        url = parsed.url
    elif isinstance(result, _AirlineUrlResult):
        url = result.url
    else:
        logger.warning(f"[agent:airline_url_finder] unexpected result type {type(result).__name__}: {result!r}")
        return None

    if url:
        logger.info(f"[agent:airline_url_finder] found URL for '{airline_name}': {url}")
    else:
        logger.info(f"[agent:airline_url_finder] agent returned no URL for '{airline_name}'")

    return url
