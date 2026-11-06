from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Avg, Count, Max, Q, Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import AIRequestLog, AIUseCaseConfig, ModelPricing


def require_superuser(request):
    if not request.user.is_active or not request.user.is_superuser:
        raise PermissionDenied("Superuser access required.")


def _period_logs(request):
    try:
        days = min(max(int(request.GET.get("days", 30)), 1), 365)
    except (TypeError, ValueError):
        days = 30
    return AIRequestLog.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=days)
    )


def _serialize(value):
    return float(value) if isinstance(value, Decimal) else value


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def analytics_summary(request):
    require_superuser(request)
    logs = _period_logs(request)
    totals = logs.aggregate(
        requests=Count("id"),
        input_tokens=Sum("input_tokens"),
        output_tokens=Sum("output_tokens"),
        total_tokens=Sum("total_tokens"),
        estimated_cost=Sum("estimated_cost"),
        average_response_time_ms=Avg("response_time_ms"),
        failed_requests=Count("id", filter=Q(success=False)),
    )
    return JsonResponse({
        key: _serialize(value or 0) for key, value in totals.items()
    } | {
        "by_provider": list(
            logs.values("provider").annotate(
                requests=Count("id"), total_tokens=Sum("total_tokens")
            ).order_by("provider")
        ),
        "by_model": list(
            logs.values("provider", "model").annotate(
                requests=Count("id"),
                total_tokens=Sum("total_tokens"),
                estimated_cost=Sum("estimated_cost"),
            ).order_by("provider", "model")
        ),
        "by_use_case": list(
            logs.values("use_case").annotate(
                requests=Count("id"), total_tokens=Sum("total_tokens")
            ).order_by("use_case")
        ),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def analytics_timeseries(request):
    require_superuser(request)
    logs = _period_logs(request)
    return JsonResponse({
        "daily": list(
            logs.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(
                requests=Count("id"),
                total_tokens=Sum("total_tokens"),
                failed_requests=Count("id", filter=Q(success=False)),
            )
            .order_by("day")
        )
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_activity(request):
    require_superuser(request)
    logs = _period_logs(request)
    return JsonResponse({
        "users": list(
            logs.values("user_id", "user__email")
            .annotate(
                requests=Count("id"),
                input_tokens=Sum("input_tokens"),
                output_tokens=Sum("output_tokens"),
                total_tokens=Sum("total_tokens"),
                failed_requests=Count("id", filter=Q(success=False)),
                last_request=Max("created_at"),
            )
            .order_by("-requests", "user__email")
        ),
        "sessions": list(
            logs.values(
                "session_id", "session__title", "user_id", "user__email", "use_case"
            )
            .annotate(
                requests=Count("id"),
                input_tokens=Sum("input_tokens"),
                output_tokens=Sum("output_tokens"),
                total_tokens=Sum("total_tokens"),
                failed_requests=Count("id", filter=Q(success=False)),
                last_request=Max("created_at"),
            )
            .order_by("-last_request")
        ),
        "recent": list(
            logs.values(
                "id", "user__email", "provider", "model",
                "use_case", "total_tokens", "success", "created_at",
            )[:25]
        ),
    })


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def model_pricing(request):
    require_superuser(request)
    if request.method == "GET":
        return JsonResponse({
            "pricing": list(ModelPricing.objects.values(
                "id", "provider", "model",
                "input_cost_per_million_tokens",
                "output_cost_per_million_tokens",
                "updated_at",
            ))
        })

    required = ("provider", "model")
    if any(not request.data.get(field) for field in required):
        return JsonResponse(
            {"detail": "provider and model are required."}, status=400
        )
    if request.data["provider"] not in dict(ModelPricing.PROVIDER_CHOICES):
        return JsonResponse({"detail": "Unsupported provider."}, status=400)
    max_price = Decimal("9999.99999999")
    prices = {}
    for field in ("input_cost_per_million_tokens", "output_cost_per_million_tokens"):
        value = request.data.get(field, 0) or 0
        try:
            value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return JsonResponse({"detail": f"{field} must be a valid number."}, status=400)
        if value < 0 or value > max_price:
            return JsonResponse(
                {"detail": f"{field} must be between 0 and {max_price}."},
                status=400,
            )
        prices[field] = value
    pricing, _ = ModelPricing.objects.update_or_create(
        provider=request.data["provider"],
        model=request.data["model"],
        defaults={
            "input_cost_per_million_tokens": prices["input_cost_per_million_tokens"],
            "output_cost_per_million_tokens": prices["output_cost_per_million_tokens"],
        },
    )
    return JsonResponse({"id": pricing.id, "message": "Pricing saved."}, status=201)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def use_case_config(request):
    require_superuser(request)
    if request.method == "GET":
        return JsonResponse({
            "configs": list(AIUseCaseConfig.objects.values(
                "id", "use_case", "provider", "model", "updated_at"
            ))
        })

    required = ("use_case", "provider", "model")
    if any(not request.data.get(field) for field in required):
        return JsonResponse(
            {"detail": "use_case, provider, and model are required."}, status=400
        )
    valid_use_cases = dict(AIUseCaseConfig.USE_CASE_CHOICES)
    if request.data["use_case"] not in valid_use_cases:
        return JsonResponse({"detail": "Unsupported use case."}, status=400)
    if request.data["provider"] not in dict(AIUseCaseConfig.PROVIDER_CHOICES):
        return JsonResponse({"detail": "Unsupported provider."}, status=400)

    config, _ = AIUseCaseConfig.objects.update_or_create(
        use_case=request.data["use_case"],
        defaults={
            "provider": request.data["provider"],
            "model": request.data["model"].strip(),
        },
    )
    return JsonResponse({"id": config.id, "message": "Use-case configuration saved."}, status=201)
