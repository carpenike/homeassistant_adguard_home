"""SVG processing utilities for AdGuard Home icons.

AdGuard Home provides SVG icons for blocked services as base64-encoded strings.
These utilities process the SVGs to:
1. Normalize size to match MDI icons (24x24 viewBox)
2. Apply a configurable fill color for theme compatibility
"""

from __future__ import annotations

import base64
import re


def process_svg_icon(base64_svg: str, fill_color: str) -> str:
    """Process an SVG icon for display in Home Assistant.

    Args:
        base64_svg: Base64-encoded SVG string from AdGuard Home API
        fill_color: Hex color to apply (e.g., "#44739e")

    Returns:
        Base64-encoded processed SVG as a data URL
    """
    if not base64_svg:
        return ""

    try:
        # Decode the base64 SVG
        svg_bytes = base64.b64decode(base64_svg)
        svg = svg_bytes.decode("utf-8")

        # Process the SVG
        svg = _normalize_svg_size(svg)
        svg = _apply_fill_color(svg, fill_color)

        # Re-encode to base64
        processed_b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{processed_b64}"

    except Exception:  # noqa: BLE001
        # If processing fails, return original as-is
        return f"data:image/svg+xml;base64,{base64_svg}"


def _normalize_svg_size(svg: str) -> str:
    """Normalize SVG to 24x24 size to match MDI icons.

    - Removes explicit width/height attributes from <svg> tag
    - Ensures viewBox exists (defaults to 24x24 if missing)

    Args:
        svg: Raw SVG string

    Returns:
        SVG with normalized size attributes
    """
    # Remove width attribute from root <svg> tag
    svg = re.sub(r"(<svg[^>]*)\s+width\s*=\s*[\"'][^\"']*[\"']", r"\1", svg)
    # Remove height attribute from root <svg> tag
    svg = re.sub(r"(<svg[^>]*)\s+height\s*=\s*[\"'][^\"']*[\"']", r"\1", svg)

    # If no viewBox exists, add a default 24x24 viewBox
    if "viewBox" not in svg and "viewbox" not in svg.lower():
        svg = svg.replace("<svg", '<svg viewBox="0 0 24 24"', 1)

    return svg


def _apply_fill_color(svg: str, fill_color: str) -> str:
    """Apply a fill color to the SVG.

    Removes existing fill attributes from paths/shapes and adds
    a global fill on the root <svg> element.

    Args:
        svg: SVG string
        fill_color: Hex color to apply (e.g., "#44739e")

    Returns:
        SVG with applied fill color
    """
    # Remove existing fill attributes (but not fill="none" which is intentional)
    # Match fill="..." but not fill="none"
    svg = re.sub(r'\s+fill\s*=\s*["\'](?!none)[^"\']*["\']', "", svg)

    # Remove existing stroke attributes for cleaner monochrome icons
    svg = re.sub(r'\s+stroke\s*=\s*["\'](?!none)[^"\']*["\']', "", svg)

    # Add fill to the root <svg> tag if not already present
    if 'fill="' not in svg.split(">", 1)[0]:
        svg = svg.replace("<svg", f'<svg fill="{fill_color}"', 1)

    return svg
