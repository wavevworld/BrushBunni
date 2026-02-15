# =============================================================================
# JAZZMIN SETTINGS - Add this to your settings.py
# =============================================================================

JAZZMIN_SETTINGS = {
    # Title & Branding
    "site_title": "BrushBunni",
    "site_header": "BrushBunni",
    "site_brand": "BrushBunni",
    "site_logo": None,  # Or path to your logo: "blog/logo.png"
    "login_logo": None,
    "site_icon": None,
    "welcome_sign": "BrushBunni Admin",
    "copyright": "BrushBunni",
    
    # Search bar
    "search_model": [],  # Disable search - leave empty
    
    # Top menu links
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View Site", "url": "/", "new_window": True},
    ],
    
    # Hide apps/models from sidebar
    "hide_apps": ["auth"],  # Hide Authentication section completely
    "hide_models": [],
    
    # Custom icons (Font Awesome)
    "icons": {
        "blog": "fas fa-palette",
        "blog.Event": "fas fa-calendar-alt",
        "blog.EventPhoto": "fas fa-images",
    },
    
    # Default icon for apps/models
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    
    # Sidebar ordering
    "order_with_respect_to": ["blog", "blog.Event"],
    
    # UI Tweaks
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": ["auth"],
    
    # Custom CSS/JS - our files
    "custom_css": "admin/css/brushbunni.css",
    "custom_js": "admin/js/brushbunni.js",
    
    # Related modal (popup for foreign keys)
    "related_modal_active": False,
    
    # Change view tweaks
    "changeform_format": "horizontal_tabs",  # or "single", "collapsible", "carousel"
    "changeform_format_overrides": {
        "blog.event": "single",  # Single form for events (no tabs)
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",  # Options: default, darkly, cosmo, flatly, etc.
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
