from html import escape


def participants_text(names: list[str]) -> str:
    """Список участников: количество и имена (first_name + last_name)."""
    if not names:
        return "👥 Участников: 0"
    lines = "\n".join(f"• {escape(name)}" for name in names)
    return f"👥 Участников: {len(names)}\n{lines}"
