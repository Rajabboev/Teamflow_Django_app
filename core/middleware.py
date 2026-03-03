from .models import Profile


class EnsureProfileMiddleware:
    """Ensure every authenticated user has a Profile (for users created before signal)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            Profile.objects.get_or_create(
                user=request.user,
                defaults={"role": "member"},
            )
        return self.get_response(request)
