from django import template

register = template.Library()

@register.filter
def length_is(value, arg):
    """
    Check if the length of value equals arg.
    Usage: {% if line.fields|length_is:'1' %}
    
    Args:
        value: Any object that supports len()
        arg: String or integer to compare length against
        
    Returns:
        bool: True if len(value) == int(arg), False otherwise
    """
    try:
        return len(value) == int(arg)
    except (ValueError, TypeError, AttributeError):
        return False

@register.filter
def split(value, delimiter=','):
    """
    Split a string by delimiter and return a list.
    Usage: {% for item in string|split:"," %}
    
    Args:
        value: String to split
        delimiter: Delimiter to split by (default: ',')
        
    Returns:
        list: List of strings
    """
    if not value:
        return []
    try:
        return [item.strip() for item in str(value).split(delimiter) if item.strip()]
    except (ValueError, TypeError, AttributeError):
        return []