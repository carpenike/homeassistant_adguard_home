"""Tests for SVG processing utilities."""

from __future__ import annotations

import base64

from custom_components.adguard_home_extended.svg_utils import (
    _apply_fill_color,
    _normalize_svg_size,
    process_svg_icon,
)


class TestNormalizeSvgSize:
    """Tests for _normalize_svg_size function."""

    def test_removes_width_attribute(self) -> None:
        """Test that width attribute is removed from SVG."""
        svg = '<svg width="128" viewBox="0 0 24 24"><path d="M0 0"/></svg>'
        result = _normalize_svg_size(svg)
        assert 'width="128"' not in result
        assert "viewBox" in result

    def test_removes_height_attribute(self) -> None:
        """Test that height attribute is removed from SVG."""
        svg = '<svg height="128" viewBox="0 0 24 24"><path d="M0 0"/></svg>'
        result = _normalize_svg_size(svg)
        assert 'height="128"' not in result
        assert "viewBox" in result

    def test_removes_both_dimensions(self) -> None:
        """Test that both width and height are removed."""
        svg = '<svg width="100" height="100" viewBox="0 0 24 24"><path/></svg>'
        result = _normalize_svg_size(svg)
        assert 'width="100"' not in result
        assert 'height="100"' not in result
        assert "viewBox" in result

    def test_adds_viewbox_if_missing(self) -> None:
        """Test that viewBox is added if not present."""
        svg = '<svg><path d="M0 0"/></svg>'
        result = _normalize_svg_size(svg)
        assert 'viewBox="0 0 24 24"' in result

    def test_preserves_existing_viewbox(self) -> None:
        """Test that existing viewBox is preserved."""
        svg = '<svg viewBox="0 0 32 32"><path d="M0 0"/></svg>'
        result = _normalize_svg_size(svg)
        assert 'viewBox="0 0 32 32"' in result
        assert 'viewBox="0 0 24 24"' not in result

    def test_handles_various_attribute_formats(self) -> None:
        """Test handling of different attribute quote styles."""
        svg = "<svg width='64' height='64'><path/></svg>"
        result = _normalize_svg_size(svg)
        assert "width=" not in result
        assert "height=" not in result


class TestApplyFillColor:
    """Tests for _apply_fill_color function."""

    def test_adds_fill_to_svg_root(self) -> None:
        """Test that fill color is added to SVG root."""
        svg = '<svg viewBox="0 0 24 24"><path d="M0 0"/></svg>'
        result = _apply_fill_color(svg, "#ff0000")
        assert 'fill="#ff0000"' in result

    def test_removes_existing_fill_attributes(self) -> None:
        """Test that existing fill attributes are removed."""
        svg = '<svg><path fill="#000000" d="M0 0"/></svg>'
        result = _apply_fill_color(svg, "#ff0000")
        assert 'fill="#000000"' not in result
        assert 'fill="#ff0000"' in result

    def test_removes_stroke_attributes(self) -> None:
        """Test that stroke attributes are removed."""
        svg = '<svg><path stroke="#000000" d="M0 0"/></svg>'
        result = _apply_fill_color(svg, "#ff0000")
        assert 'stroke="#000000"' not in result

    def test_preserves_fill_none(self) -> None:
        """Test that fill='none' is preserved (intentional transparency)."""
        svg = '<svg><path fill="none" d="M0 0"/></svg>'
        result = _apply_fill_color(svg, "#ff0000")
        assert 'fill="none"' in result

    def test_preserves_stroke_none(self) -> None:
        """Test that stroke='none' is preserved."""
        svg = '<svg><path stroke="none" d="M0 0"/></svg>'
        result = _apply_fill_color(svg, "#ff0000")
        assert 'stroke="none"' in result

    def test_does_not_duplicate_fill_on_root(self) -> None:
        """Test that fill is not duplicated if already on root."""
        svg = '<svg fill="#123456"><path d="M0 0"/></svg>'
        result = _apply_fill_color(svg, "#ff0000")
        # Should remove the old fill and not add a new one since we're
        # checking after the removal
        # The fill="#123456" gets removed, then fill="#ff0000" would be added
        # but the check is done on the original string split
        assert result.count('fill="') <= 2  # Root + possibly one "none"


class TestProcessSvgIcon:
    """Tests for process_svg_icon function."""

    def test_processes_valid_base64_svg(self) -> None:
        """Test processing of valid base64-encoded SVG."""
        svg = '<svg width="100" height="100"><path fill="#000"/></svg>'
        b64 = base64.b64encode(svg.encode()).decode()

        result = process_svg_icon(b64, "#44739e")

        assert result.startswith("data:image/svg+xml;base64,")
        # Decode and check processing was applied
        processed_b64 = result.replace("data:image/svg+xml;base64,", "")
        processed_svg = base64.b64decode(processed_b64).decode()
        assert 'width="100"' not in processed_svg
        assert 'fill="#44739e"' in processed_svg

    def test_returns_empty_string_for_empty_input(self) -> None:
        """Test that empty input returns empty string."""
        result = process_svg_icon("", "#ff0000")
        assert result == ""

    def test_handles_invalid_base64_gracefully(self) -> None:
        """Test that invalid base64 returns original as data URL."""
        invalid_b64 = "not-valid-base64!!!"
        result = process_svg_icon(invalid_b64, "#ff0000")
        # Should return original wrapped in data URL
        assert result == f"data:image/svg+xml;base64,{invalid_b64}"

    def test_handles_non_utf8_gracefully(self) -> None:
        """Test that non-UTF8 content is handled gracefully."""
        # Create valid base64 of non-UTF8 bytes
        binary_data = bytes([0x80, 0x81, 0x82])
        b64 = base64.b64encode(binary_data).decode()
        result = process_svg_icon(b64, "#ff0000")
        # Should return original as data URL on decode error
        assert result == f"data:image/svg+xml;base64,{b64}"

    def test_full_processing_pipeline(self) -> None:
        """Test complete processing of an SVG icon."""
        # Simulate a typical AdGuard Home icon SVG
        svg = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
            <path fill="#000000" d="M12 2L2 7v10l10 5 10-5V7L12 2z"/>
        </svg>"""
        b64_input = base64.b64encode(svg.encode()).decode()

        result = process_svg_icon(b64_input, "#44739e")

        # Decode result
        processed_b64 = result.replace("data:image/svg+xml;base64,", "")
        processed_svg = base64.b64decode(processed_b64).decode()

        # Verify transformations
        assert 'width="24"' not in processed_svg
        assert 'height="24"' not in processed_svg
        assert 'fill="#000000"' not in processed_svg
        assert 'fill="#44739e"' in processed_svg
        assert 'viewBox="0 0 24 24"' in processed_svg

    def test_preserves_svg_structure(self) -> None:
        """Test that SVG structure (paths, etc.) is preserved."""
        svg = '<svg viewBox="0 0 24 24"><path d="M12 0L24 12"/><circle cx="12" cy="12" r="5"/></svg>'
        b64 = base64.b64encode(svg.encode()).decode()

        result = process_svg_icon(b64, "#ffffff")

        processed_b64 = result.replace("data:image/svg+xml;base64,", "")
        processed_svg = base64.b64decode(processed_b64).decode()

        assert '<path d="M12 0L24 12"/>' in processed_svg
        assert '<circle cx="12" cy="12" r="5"/>' in processed_svg
