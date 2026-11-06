import logging
from decimal import Decimal

from .models import AIRequestLog, ModelPricing

logger = logging.getLogger(__name__)


def _usage_value(usage, *names):
    for name in names:
        if isinstance(usage, dict) and name in usage:
            return usage[name] or 0
        value = getattr(usage, name, None)
        if value is not None:
            return value
    return 0


def extract_usage(provider, response):
    """Return normalized input/output token counts from a provider response."""
    if provider == "groq":
        usage = getattr(response, "usage", None)
        return (
            int(_usage_value(usage, "prompt_tokens")),
            int(_usage_value(usage, "completion_tokens")),
        )

    return (
        int(_usage_value(response, "prompt_eval_count", "prompt_tokens")),
        int(_usage_value(response, "eval_count", "completion_tokens")),
    )


def record_request(
    *,
    provider,
    model,
    use_case,
    started_at,
    response=None,
    error=None,
    user=None,
    session=None,
):
    input_tokens = output_tokens = 0
    if response is not None:
        input_tokens, output_tokens = extract_usage(provider, response)

    total_tokens = input_tokens + output_tokens
    estimated_cost = None
    pricing = ModelPricing.objects.filter(provider=provider, model=model).first()
    if pricing:
        estimated_cost = (
            Decimal(input_tokens) * pricing.input_cost_per_million_tokens
            + Decimal(output_tokens) * pricing.output_cost_per_million_tokens
        ) / Decimal(1_000_000)

    duration_ms = max(0, int((__import__("time").perf_counter() - started_at) * 1000))
    try:
        return AIRequestLog.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            session=session,
            provider=provider,
            model=model,
            use_case=use_case,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            response_time_ms=duration_ms,
            success=error is None,
            error_message=str(error) if error else "",
        )
    except Exception:
        logger.exception("Unable to persist AI request log")
        return None
