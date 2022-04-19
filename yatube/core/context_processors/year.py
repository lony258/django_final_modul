from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    data_context = timezone.now()
    return {
        'year': data_context.year
    }
