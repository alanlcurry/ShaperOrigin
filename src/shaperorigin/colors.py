"""Map RGB values to CSS3 color names for Shaper cut types."""

import logging
import re

import webcolors


def closest_color(requested_colour: tuple[int, int, int]) -> str:
    """Find the closest CSS3 color name for a given RGB value.

    Uses Euclidean distance in RGB color space to find the nearest named color.

    Args:
        requested_colour (tuple): RGB color values as (r, g, b).

    Returns:
        str: The name of the closest CSS3 color.
    """
    min_colours = {}
    for name in webcolors.names("css3"):
        r_c, g_c, b_c = webcolors.name_to_rgb(name)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


def get_color_name(rgb_tuple: tuple[int, int, int]) -> str:
    """Get the CSS3 color name for an RGB tuple.

    First attempts an exact match, then falls back to finding the closest color.

    Args:
        rgb_tuple (tuple): RGB color values as (r, g, b).

    Returns:
        str: The name of the exact or closest CSS3 color.
    """
    try:
        hex_value = webcolors.rgb_to_hex(rgb_tuple)
        return webcolors.hex_to_name(hex_value)
    except ValueError:
        return closest_color(rgb_tuple)


def get_color_name_rgb(rgb_str: str) -> str:
    """Convert a CSS RGB string to a color name.

    Parses a string in format 'rgb(r,g,b)' and converts it to a CSS3 color name.

    Args:
        rgb_str (str): RGB color string in format 'rgb(r,g,b)'.

    Returns:
        str: The CSS3 color name. Invalid input falls back to 'black'.
    """
    try:
        matches = re.findall(r"\d+", rgb_str)
        if len(matches) < 3:
            raise ValueError("Incomplete RGB data")

        rgb_value = tuple(map(int, matches[:3]))
        if not all(0 <= channel <= 255 for channel in rgb_value):
            raise ValueError("Values out of range")

        return get_color_name(rgb_value)
    except (ValueError, TypeError) as exc:
        logging.warning("Invalid RGB color '%s': %s. Defaulting to black.", rgb_str, exc)
        return "black"
