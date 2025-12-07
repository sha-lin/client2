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
