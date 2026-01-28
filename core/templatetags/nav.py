from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_active(context, url_name):
    """
    Return the extra Tailwind classes if this nav item is active.
    url_name can be a URL name or a raw path like '/pieces'.
    """
    request = context["request"]
    path = request.path

    try:
        target = reverse(url_name)
    except NoReverseMatch:
        target = url_name

    if target != "/" and target in path or path == target:
        # Active
        return "nav-active"
    else:
        # Inactive
        return "nav-inactive"
