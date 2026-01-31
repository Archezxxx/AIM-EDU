from django import template
from django.urls import translate_url, reverse, resolve
from django.utils import translation

register = template.Library()

@register.simple_tag(takes_context=True)
def switch_lang(context, lang_code):
    """
    Returns the URL for the current page in the given language code.
    Fixes issues where standard translate_url might fail with prefix logic.
    """
    path = context['request'].path
    try:
        # First, try standard translate_url
        url = translate_url(path, lang_code)
        
        # If it returns the same path (and prefixes differ), it failed
        # E.g. /ru/schools/ -> /ru/schools/ when asking for 'ky'
        # Check if the prefix implies failure
        if url == path and lang_code not in path:
             # Try manual resolve and reverse
             match = resolve(path)
             with translation.override(lang_code):
                 url = reverse(match.view_name, args=match.args, kwargs=match.kwargs)
        
        # Append query parameters if they exist
        query = context['request'].GET.urlencode()
        if query:
            url = f"{url}?{query}"
            
        return url
    except Exception:
        return path # Fallback to current path
