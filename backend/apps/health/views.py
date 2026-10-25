from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    database = "ok"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        database = "unavailable"

    status_code = 200 if database == "ok" else 503
    return JsonResponse(
        {
            "status": "ok" if status_code == 200 else "degraded",
            "service": "stockpilot-api",
            "database": database,
        },
        status=status_code,
    )
