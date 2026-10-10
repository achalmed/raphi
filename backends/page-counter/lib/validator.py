"""
lib/validator.py — Validación de entradas y resolución de rutas de blogs.

Comprueba precondiciones (ruta base, nombres de blog) antes de procesar
nada, y traduce nombres lógicos de blog ("axiomata") a rutas reales
("<hub>/_pubs/<blog>/_site", según el registro `_pubs/pubs.yml`).
"""

from pathlib import Path
from typing import Dict, List, Optional

from config import (
    ALIAS_WEBSITE_ACHALMA,
    BLOGS_ESTANDAR,
    BLOGS_WEBSITE_ACHALMA,
    CARPETA_BLOG,
    RUTA_BASE_PUBLICACIONES,
    SUBDIR_PUBS,
)


def validate_base_path() -> bool:
    """
    Checks that the configured publications base directory exists.

    Returns:
        True if the base path exists, False otherwise.
    """
    return RUTA_BASE_PUBLICACIONES.exists()


def blog_site_path(blog_name: str) -> Path:
    """
    Resolves the rendered-site path of a standard blog.

    Args:
        blog_name: Logical blog name (the one in the registry `_pubs/pubs.yml`).

    Returns:
        Absolute path to the blog's _site directory.
    """
    return CARPETA_BLOG[blog_name] / "_site"


def known_blog_names() -> List[str]:
    """
    Returns every selectable blog name, including website-achalma aliases.
    """
    return BLOGS_ESTANDAR + list(BLOGS_WEBSITE_ACHALMA) + [ALIAS_WEBSITE_ACHALMA]


def find_unknown_blogs(selected: List[str]) -> List[str]:
    """
    Detects requested blog names that don't exist in the configuration.

    The v1.x silently ignored typos, so a misspelled blog produced an
    incomplete report with no warning; callers use this to alert the user.

    Args:
        selected: Blog names passed via -b/--blogs.

    Returns:
        The subset of names that are not configured.
    """
    known = set(known_blog_names())
    return [name for name in selected if name not in known]


def resolve_blog_paths(selected: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Maps each requested (or every configured) blog to its rendered-site path.

    Blogs whose _site directory doesn't exist yet (not rendered) are
    excluded from the result.

    Args:
        selected: Blog names to process; None means all configured blogs.

    Returns:
        Dict of {display_name: absolute_path}.
    """
    paths: Dict[str, str] = {}

    standard_targets = selected if selected else BLOGS_ESTANDAR
    for blog_name in standard_targets:
        if blog_name in BLOGS_ESTANDAR:
            site_path = blog_site_path(blog_name)
            if site_path.exists():
                paths[blog_name] = str(site_path)

    website_selected = (
        not selected
        or any(name in BLOGS_WEBSITE_ACHALMA or name == ALIAS_WEBSITE_ACHALMA
               for name in selected)
    )
    if website_selected:
        for section_name, relative_path in BLOGS_WEBSITE_ACHALMA.items():
            wanted = (
                not selected
                or section_name in selected
                or ALIAS_WEBSITE_ACHALMA in selected
            )
            section_path = RUTA_BASE_PUBLICACIONES / relative_path
            if wanted and section_path.exists():
                paths[f"{ALIAS_WEBSITE_ACHALMA}/{section_name}"] = str(section_path)

    return paths
