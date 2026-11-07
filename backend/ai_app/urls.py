from django.urls import path

from .views import (
    analytics_summary,
    analytics_timeseries,
    model_pricing,
    use_case_config,
    user_activity,
)

app_name = "ai_app"

urlpatterns = [
    path("analytics/summary/", analytics_summary, name="analytics-summary"),
    path("analytics/timeseries/", analytics_timeseries, name="analytics-timeseries"),
    path("analytics/users/", user_activity, name="analytics-users"),
    path("analytics/pricing/", model_pricing, name="analytics-pricing"),
    path("analytics/use-case-config/", use_case_config, name="analytics-use-case-config"),
]
