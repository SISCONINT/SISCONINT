"""Utilidades de SQL compartidas."""


def escape_like(text: str) -> str:
    """Para que %, _ y \\ escritos por el usuario se busquen como texto y no como comodines."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")