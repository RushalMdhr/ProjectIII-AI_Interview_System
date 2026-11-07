from django.contrib import admin

from .models import AIRequestLog, AIUseCaseConfig, ModelPricing


@admin.register(ModelPricing)
class ModelPricingAdmin(admin.ModelAdmin):
    list_display = (
        "provider",
        "model",
        "input_cost_per_million_tokens",
        "output_cost_per_million_tokens",
        "updated_at",
    )
    list_filter = ("provider",)
    search_fields = ("model",)


@admin.register(AIUseCaseConfig)
class AIUseCaseConfigAdmin(admin.ModelAdmin):
    list_display = ("use_case", "provider", "model", "updated_at")
    list_filter = ("provider", "use_case")
    search_fields = ("model",)


@admin.register(AIRequestLog)
class AIRequestLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "provider",
        "model",
        "use_case",
        "user",
        "session",
        "total_tokens",
        "estimated_cost",
        "response_time_ms",
        "success",
    )
    list_filter = ("provider", "model", "use_case", "success", "created_at")
    search_fields = ("model", "user__email", "error_message")
    date_hierarchy = "created_at"
    readonly_fields = (
        "user",
        "session",
        "provider",
        "model",
        "use_case",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "estimated_cost",
        "response_time_ms",
        "success",
        "error_message",
        "created_at",
    )
