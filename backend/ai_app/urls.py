from django.urls import path

from .views import (
    analytics_summary,
    analytics_timeseries,
    model_pricing,
    use_case_config,
    user_usage,
    user_activity,
    token_usage_limit,
)

app_name = "ai_app"

urlpatterns = [
    path("analytics/summary/", analytics_summary, name="analytics-summary"),
    path("analytics/timeseries/", analytics_timeseries, name="analytics-timeseries"),
    path("usage/me/", user_usage, name="user-usage"),
    path("analytics/users/", user_activity, name="analytics-users"),
    path("analytics/pricing/", model_pricing, name="analytics-pricing"),
    path("analytics/use-case-config/", use_case_config, name="analytics-use-case-config"),
    path("analytics/token-limit/", token_usage_limit, name="analytics-token-limit"),
]
