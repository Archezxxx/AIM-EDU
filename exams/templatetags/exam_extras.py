from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key.
    Usage: {{ mydict|get_item:key }}
    """
    if dictionary:
        return dictionary.get(key)
    return None
