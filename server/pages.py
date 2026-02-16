"""
MarchogSystemsOps Pages — JSON-backed page registry
Replaces SQLite pages table with a simple pages.json file
"""
import json
from pathlib import Path

PAGES_JSON = Path(__file__).parent.parent / "client" / "pages" / "pages.json"


def _read_pages() -> list[dict]:
    """Read and parse pages.json."""
    if not PAGES_JSON.exists():
        return []
    with open(PAGES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_pages(pages: list[dict]):
    """Write pages list back to pages.json."""
    with open(PAGES_JSON, "w", encoding="utf-8") as f:
        json.dump(pages, f, indent=2, ensure_ascii=False)
        f.write("\n")


def get_all_pages() -> list[dict]:
    """Get all registered pages."""
    return _read_pages()


def get_page(page_id: str) -> dict | None:
    """Get a single page by ID."""
    for p in _read_pages():
        if p["id"] == page_id:
            return p
    return None


def create_page(page_id: str, name: str, file: str, description: str = "",
                icon: str = "", category: str = "general", params: dict = None):
    """Create a new page."""
    pages = _read_pages()
    # Check for duplicate ID
    if any(p["id"] == page_id for p in pages):
        return False
    pages.append({
        "id": page_id,
        "name": name,
        "description": description,
        "file": file,
        "icon": icon or "ti-file",
        "category": category,
        "params": params or {}
    })
    _write_pages(pages)
    return True


def update_page(page_id: str, name: str = None, description: str = None,
                icon: str = None, category: str = None, params: dict = None):
    """Update a page's fields."""
    pages = _read_pages()
    for p in pages:
        if p["id"] == page_id:
            if name is not None:
                p["name"] = name
            if description is not None:
                p["description"] = description
            if icon is not None:
                p["icon"] = icon
            if category is not None:
                p["category"] = category
            if params is not None:
                p["params"] = params
            _write_pages(pages)
            return True
    return False


def delete_page(page_id: str):
    """Delete a page registration."""
    pages = _read_pages()
    filtered = [p for p in pages if p["id"] != page_id]
    if len(filtered) == len(pages):
        return False
    _write_pages(filtered)
    return True


def scan_pages_directory(pages_dir: Path) -> list[str]:
    """Auto-discover HTML files in the pages directory and register new ones."""
    if not pages_dir.exists():
        return []
    pages = _read_pages()
    registered_files = {p["file"] for p in pages}
    discovered = []
    for html_file in sorted(pages_dir.glob("*.html")):
        filename = html_file.name
        if filename in registered_files:
            continue
        page_id = html_file.stem
        page_name = page_id.replace("-", " ").replace("_", " ").title()
        pages.append({
            "id": page_id,
            "name": page_name,
            "description": f"Auto-discovered: {filename}",
            "file": filename,
            "icon": "ti-file",
            "category": "general",
            "params": {}
        })
        discovered.append(page_id)
        print(f"  [+] Auto-registered page: {page_id} ({filename})")
    if discovered:
        _write_pages(pages)
    return discovered
