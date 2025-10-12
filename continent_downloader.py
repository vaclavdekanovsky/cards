import os
import io
import urllib.request
import xml.etree.ElementTree as ET
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

class ContinentDownloader:
    """
    Downloads SVG outlines for continents and renders them to PNGs with a white background.

    Sources use Wikimedia Commons for SVG maps.
    """

    CONTINENT_SOURCES = {
        "americas": "https://upload.wikimedia.org/wikipedia/commons/d/d5/Americas_(orthographic_projection).svg",
        "europe": "https://upload.wikimedia.org/wikipedia/commons/4/44/Europe_(orthographic_projection).svg",
        "asia": "https://upload.wikimedia.org/wikipedia/commons/e/e4/Asia_(orthographic_projection).svg",
        "africa": "https://upload.wikimedia.org/wikipedia/commons/8/86/Africa_(orthographic_projection).svg",
        "oceania": "https://upload.wikimedia.org/wikipedia/commons/8/88/Australia-New_Guinea_(orthographic_projection).svg",
    }

    def __init__(self, targets=None, output_dir="output"):
        # Default to the 4 requested categories: americas, europe, asia, africa.
        # If you also want Australia+Oceania, include "oceania" in targets.
        if targets is None:
            targets = ["americas", "europe", "asia", "africa", "oceania"]
        self.targets = targets
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _download_text(self, url):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.read().decode("utf-8")
        except Exception as e:
            # Fallback between branches if 404 or similar
            try:
                alt = None
                if "/main/" in url:
                    alt = url.replace("/main/", "/master/")
                elif "/master/" in url:
                    alt = url.replace("/master/", "/main/")
                if alt:
                    req2 = urllib.request.Request(alt, headers=headers)
                    with urllib.request.urlopen(req2) as resp:
                        return resp.read().decode("utf-8")
            except Exception:
                pass
            raise

    def _inject_white_background(self, svg_text):
        """Wraps the SVG content with a white background rectangle (100% x 100%)."""
        try:
            root = ET.fromstring(svg_text)
        except ET.ParseError:
            # If the file has an XML declaration or unusual formatting, try to strip it and reparse
            svg_text = svg_text.split("?>", 1)[-1]
            root = ET.fromstring(svg_text)

        # Capture important sizing attributes
        viewBox = root.get("viewBox")
        width = root.get("width")
        height = root.get("height")

        # Build a new root with the same sizing
        attrib = {"xmlns": "http://www.w3.org/2000/svg"}
        if viewBox:
            attrib["viewBox"] = viewBox
        if width:
            attrib["width"] = width
        if height:
            attrib["height"] = height

        new_root = ET.Element("svg", attrib=attrib)

        # Add a white background
        ET.SubElement(new_root, "rect", width="100%", height="100%", fill="white")

        # Append all children from the original root
        for child in list(root):
            new_root.append(child)

        return ET.tostring(new_root, encoding="unicode")

    def _svg_to_png(self, svg_text, out_path, scale=1.0):
        # Render SVG to PNG via svglib + reportlab
        drawing = svg2rlg(io.StringIO(svg_text))
        if scale and scale != 1.0 and hasattr(drawing, "scale"):
            drawing.scale(scale, scale)
        renderPM.drawToFile(drawing, out_path, fmt="PNG")

    def process(self):
        for key in self.targets:
            url = self.CONTINENT_SOURCES.get(key)
            if not url:
                print(f"No source URL configured for '{key}', skipping.")
                continue
            try:
                print(f"Downloading {key} SVG...")
                svg_text = self._download_text(url)
                svg_with_bg = self._inject_white_background(svg_text)
                out_path = os.path.join(self.output_dir, f"{key}.png")
                self._svg_to_png(svg_with_bg, out_path)
                print(f"Saved {out_path}")
            except Exception as e:
                print(f"Failed processing {key}: {e}")

def main():
    # By default will produce americas, europe, asia, africa, oceania
    targets = ["americas", "europe", "asia", "africa", "oceania"]
    downloader = ContinentDownloader(targets=targets, output_dir="output")
    downloader.process()

if __name__ == "__main__":
    main()
