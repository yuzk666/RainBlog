from .accounts import display_name_for


def account_identity(request):
    return {"current_display_name": display_name_for(request.user)}
