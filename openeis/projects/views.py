from django.contrib.auth.decorators import user_passes_test

from .protectedmedia import protected_media


def staff_test(user):
    return user.is_staff

@protected_media
@user_passes_test(staff_test)
def get_protected_file(request, path):
    return path
