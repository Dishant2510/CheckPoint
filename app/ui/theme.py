"""
CheckPoint — Theme and styling system.

Defines the dark gaming aesthetic color palette, fonts, spacing,
and widget configuration used across all UI components.
"""

from typing import Any

# ──────────────────────────────────────────────────────────
#  Color Palette — Dark Gaming Aesthetic
# ──────────────────────────────────────────────────────────

COLORS = {
    # Backgrounds
    "bg_primary": "#0d1117",       # Deep space black
    "bg_secondary": "#161b22",     # Dark card background
    "bg_tertiary": "#1c2333",      # Elevated surface
    "bg_sidebar": "#0d1117",       # Sidebar background
    "bg_hover": "#21262d",         # Hover state
    "bg_active": "#1a3a5c",        # Active/selected state
    "bg_input": "#0d1117",         # Input field background
    "bg_card": "#161b22",          # Card background
    "bg_card_hover": "#1c2333",    # Card hover

    # Accent Colors
    "accent_primary": "#00d4ff",   # Neon cyan — primary accent
    "accent_secondary": "#7c3aed", # Electric purple
    "accent_success": "#10b981",   # Emerald green
    "accent_warning": "#f59e0b",   # Amber
    "accent_danger": "#ef4444",    # Red
    "accent_info": "#3b82f6",      # Blue

    # Accent Hover
    "accent_primary_hover": "#00b8d9",
    "accent_danger_hover": "#dc2626",
    "accent_success_hover": "#059669",

    # Text
    "text_primary": "#e6edf3",    # Primary text
    "text_secondary": "#8b949e",  # Secondary/muted text
    "text_tertiary": "#6e7681",   # Tertiary/disabled text
    "text_accent": "#00d4ff",     # Accent-colored text
    "text_on_accent": "#000000",  # Text on accent backgrounds

    # Borders
    "border_primary": "#30363d",  # Default border
    "border_secondary": "#21262d",  # Subtle border
    "border_accent": "#00d4ff",   # Accent border
    "border_hover": "#484f58",    # Border on hover

    # Status Colors
    "status_online": "#10b981",
    "status_offline": "#6e7681",
    "status_warning": "#f59e0b",
    "status_error": "#ef4444",
    "status_synced": "#00d4ff",

    # Chart Colors (for storage breakdown)
    "chart_1": "#00d4ff",
    "chart_2": "#7c3aed",
    "chart_3": "#10b981",
    "chart_4": "#f59e0b",
    "chart_5": "#ef4444",
    "chart_6": "#3b82f6",
    "chart_7": "#ec4899",
    "chart_8": "#06b6d4",

    # Scrollbar
    "scrollbar_bg": "#161b22",
    "scrollbar_thumb": "#30363d",
    "scrollbar_thumb_hover": "#484f58",

    # Shadows (for reference — applied via transparency)
    "shadow": "#000000",
}

# ──────────────────────────────────────────────────────────
#  Typography
# ──────────────────────────────────────────────────────────

FONTS = {
    "heading_xl": ("Segoe UI", 28, "bold"),
    "heading_lg": ("Segoe UI", 22, "bold"),
    "heading_md": ("Segoe UI", 18, "bold"),
    "heading_sm": ("Segoe UI", 15, "bold"),

    "body_lg": ("Segoe UI", 14),
    "body_md": ("Segoe UI", 13),
    "body_sm": ("Segoe UI", 12),
    "body_xs": ("Segoe UI", 11),

    "mono_md": ("Consolas", 13),
    "mono_sm": ("Consolas", 11),

    "button": ("Segoe UI Semibold", 13),
    "button_sm": ("Segoe UI Semibold", 11),

    "nav_item": ("Segoe UI Semibold", 13),
    "nav_item_active": ("Segoe UI Bold", 13),

    "stat_value": ("Segoe UI", 32, "bold"),
    "stat_label": ("Segoe UI", 12),
}

# ──────────────────────────────────────────────────────────
#  Spacing
# ──────────────────────────────────────────────────────────

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
    "section": 40,
}

RADIUS = {
    "sm": 6,
    "md": 8,
    "lg": 12,
    "xl": 16,
    "pill": 9999,
}

# ──────────────────────────────────────────────────────────
#  Sidebar Config
# ──────────────────────────────────────────────────────────

SIDEBAR_WIDTH = 220
SIDEBAR_COLLAPSED_WIDTH = 60

# ──────────────────────────────────────────────────────────
#  Icon Characters (Unicode symbols for sidebar nav)
# ──────────────────────────────────────────────────────────

ICONS = {
    "dashboard": "⊞",
    "games": "🎮",
    "backup": "💾",
    "settings": "⚙",
    "logs": "📋",
    "add": "＋",
    "delete": "🗑",
    "restore": "↩",
    "folder": "📁",
    "search": "🔍",
    "check": "✓",
    "warning": "⚠",
    "error": "✕",
    "info": "ℹ",
    "clock": "🕐",
    "storage": "💿",
    "shield": "🛡",
    "refresh": "↻",
    "export": "↗",
    "star": "★",
    "play": "▶",
    "stop": "■",
}

# ──────────────────────────────────────────────────────────
#  Launcher Labels & Colors
# ──────────────────────────────────────────────────────────

LAUNCHER_CONFIG = {
    "steam": {"label": "Steam", "color": "#1b2838"},
    "epic": {"label": "Epic Games", "color": "#2a2a2a"},
    "emulator": {"label": "Emulator", "color": "#7c3aed"},
    "offline": {"label": "Offline", "color": "#6e7681"},
    "unknown": {"label": "Unknown", "color": "#30363d"},
}


def get_chart_color(index: int) -> str:
    """Return a chart color by index, cycling through available colors."""
    chart_colors = [v for k, v in COLORS.items() if k.startswith("chart_")]
    return chart_colors[index % len(chart_colors)]
