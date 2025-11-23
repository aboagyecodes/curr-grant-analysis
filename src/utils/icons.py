"""
Icon Helper for Streamlit Dashboards

Uses Material Symbols for professional, consistent iconography
"""


def icon(name, size=20):
    """
    Render a Material Symbol icon
    
    Args:
        name: Icon name from Material Symbols (e.g., 'search', 'science', 'payments')
        size: Icon size in pixels (default 20)
    
    Returns:
        str: HTML string for the icon
    """
    return f'<span class="material-symbols-outlined" style="font-size:{size}px;vertical-align:middle;">{name}</span>'


def load_material_icons_css():
    """
    Returns HTML to load Material Symbols font
    Should be called once in each dashboard
    """
    return """
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
    <style>
    .material-symbols-outlined {
        font-variation-settings:
        'FILL' 0,
        'wght' 400,
        'GRAD' 0,
        'opsz' 24;
        vertical-align: middle;
        margin-right: 4px;
    }
    </style>
    """


# Icon mappings for common dashboard elements
ICONS = {
    'search': 'search',
    'investigate': 'science',
    'money': 'payments',
    'grant': 'volunteer_activism',
    'commodity': 'agriculture',
    'trending': 'trending_up',
    'news': 'article',
    'link': 'link',
    'notes': 'edit_note',
    'trophy': 'emoji_events',
    'chart': 'analytics',
    'calendar': 'calendar_month',
    'globe': 'public',
    'alert': 'error',
    'info': 'info',
    'success': 'check_circle',
    'settings': 'settings',
    'refresh': 'refresh',
}


def get_icon_html(icon_key, text="", size=20):
    """
    Get icon HTML with optional text
    
    Args:
        icon_key: Key from ICONS dict
        text: Optional text to display after icon
        size: Icon size in pixels
    
    Returns:
        str: Complete HTML string
    """
    icon_name = ICONS.get(icon_key, icon_key)
    icon_html = icon(icon_name, size)
    
    if text:
        return f"{icon_html} {text}"
    return icon_html
