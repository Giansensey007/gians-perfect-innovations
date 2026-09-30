#!/usr/bin/env python3
"""Build data/catalog.json and public/media from the abandoned-patent zip.

Ideas 05-15 come from _meta/batch-002-ideas.json.
Ideas 01-04 have no JSON record, so their narrative is parsed from the docx files.
Category labels for 01-04 are assigned here because those docx files do not
include a category line. The labels follow the same slash style as the later batch.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = Path(
    os.environ.get(
        "PATENT_ZIP",
        "/Users/seyitcansenpinar/Downloads/Innovator-Abandoned-Patents-batch-001-015.zip",
    )
)
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Docx files for 01-04 do not include a category. These match the later batch's style.
DOCX_CATEGORY = {
    "01": "climate / health",
    "02": "consumer hardware / energy",
    "03": "home / climate",
    "04": "health / consumer",
}

NARRATIVE_LABELS = (
    ("upgrade vs original", "upgrade"),
    ("next build step", "next"),
    ("target user", "target"),
    ("why now", "whyNow"),
    ("pitch", "pitch"),
)


def docx_paragraphs(blob: bytes) -> list[str]:
    inner = zipfile.ZipFile(io.BytesIO(blob))
    root = ET.fromstring(inner.read("word/document.xml"))
    lines: list[str] = []
    for para in root.iter(W + "p"):
        text = "".join(node.text or "" for node in para.iter(W + "t")).strip()
        if text:
            lines.append(text)
    return lines


def split_label(line: str) -> tuple[str | None, str]:
    low = line.lower()
    for prefix, key in NARRATIVE_LABELS:
        if low.startswith(prefix):
            rest = line[len(prefix) :].strip(" :.-")
            return key, rest
    return None, ""


def narrative_from_paragraphs(lines: list[str]) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        key, rest = split_label(line)
        if key:
            current = key
            sections.setdefault(key, [])
            if rest:
                sections[key].append(rest)
            continue
        if current:
            sections.setdefault(current, []).append(line)
    return {key: " ".join(parts).strip() for key, parts in sections.items()}


def field(lines: list[str], label: str) -> str:
    prefix = label.lower()
    for line in lines:
        if line.lower().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def claims_and_fto(lines: list[str]) -> tuple[list[str], str]:
    claims: list[str] = []
    fto_parts: list[str] = []
    mode = ""
    for line in lines:
        low = line.lower()
        if low.startswith("claim / summary") or low.startswith("claim/summary"):
            mode = "claims"
            continue
        if low.startswith("why abandoned"):
            mode = "fto"
            continue
        if mode == "claims":
            numbered = re.match(r"^\d+(?:-\d+)?\.\s*(.+)$", line)
            if numbered:
                claims.append(numbered.group(1).strip())
            elif low.startswith("also disclosed"):
                claims.append(line.strip())
        elif mode == "fto":
            fto_parts.append(line)
    return claims, " ".join(fto_parts).strip()


def parse_patent(lines: list[str]) -> dict[str, str]:
    blob = "\n".join(lines)
    number = ""
    app = ""
    match = re.search(
        r"Patent number:\s*([A-Z]{2}\d+[A-Z0-9]*)\s*(?:\(App\s*([^)]+)\))?",
        blob,
    )
    if match:
        number = match.group(1)
        app = (match.group(2) or "").strip()
    filing = ""
    publication = ""
    filing_match = re.search(r"Filing:\s*(\d{4}-\d{2}-\d{2})", blob)
    pub_match = re.search(r"Publication:\s*(\d{4}-\d{2}-\d{2})", blob)
    if filing_match:
        filing = filing_match.group(1)
    if pub_match:
        publication = pub_match.group(1)
    status = field(lines, "Status")
    abandon = ""
    recorded = re.search(r"recorded\s+(\d{4}-\d{2}-\d{2})", status, re.I)
    if recorded:
        abandon = recorded.group(1)
    url = ""
    url_match = re.search(r"https://patents\.google\.com/patent/\S+", blob)
    if url_match:
        url = url_match.group(0).rstrip(").,")
    claims, fto = claims_and_fto(lines)
    inventor = field(lines, "Inventors") or field(lines, "Inventor")
    return {
        "patentNumber": number,
        "app": app,
        "title": field(lines, "Title"),
        "inventor": inventor,
        "assignee": field(lines, "Assignee"),
        "status": status,
        "filing": filing,
        "publication": publication,
        "abandonDate": abandon,
        "patentUrl": url,
        "claims": claims,
        "fto": fto,
    }


def family_of(category: str) -> str:
    head = category.split("/")[0].strip().lower()
    if head.startswith("consumer"):
        return "consumer"
    if head.startswith("agri"):
        return "agri"
    return head or "other"


def short_name(name: str) -> str:
    return name.split()[0]


def espacenet(number: str) -> str:
    if not number:
        return ""
    return (
        "https://worldwide.espacenet.com/patent/search?q=pn%3D" + number
    )


def folder_for(zf: zipfile.ZipFile, nn: str) -> str:
    prefix = nn + " - "
    folders = {
        name.split("/")[0]
        for name in zf.namelist()
        if name.startswith(prefix)
    }
    if len(folders) != 1:
        raise SystemExit(f"Expected one folder for {nn}, found {folders}")
    return next(iter(folders))


def copy_images(zf: zipfile.ZipFile, folder: str, slug: str) -> list[dict[str, str]]:
    dest_dir = ROOT / "public" / "media" / slug
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True)
    names = [n for n in zf.namelist() if n.startswith(folder + "/")]
    specs = (
        ("photoreal-01.png", "photoreal", "photoreal-01.png"),
        ("photoreal-02.png", "photoreal", "photoreal-02.png"),
        ("render-01.png", "render", "render-01.png"),
        ("render-02.png", "render", "render-02.png"),
    )
    images = []
    for public_name, kind, suffix in specs:
        matches = [n for n in names if Path(n).name.endswith(suffix)]
        if len(matches) != 1:
            raise SystemExit(f"{folder}: expected one *{suffix}, found {matches}")
        blob = zf.read(matches[0])
        # Several "png" photoreal files are JPEG data. Serve them with a matching extension.
        if blob.startswith(b"\xff\xd8\xff") and public_name.endswith(".png"):
            public_name = public_name[:-4] + ".jpg"
        (dest_dir / public_name).write_bytes(blob)
        images.append(
            {
                "src": f"/media/{slug}/{public_name}",
                "kind": kind,
            }
        )
    return images


def idea_from_docx(zf: zipfile.ZipFile, folder: str, brief: dict) -> dict:
    nn = brief["nn"]
    desc_name = next(
        n
        for n in zf.namelist()
        if n.startswith(folder + "/") and n.endswith("Description.docx")
    )
    patent_name = next(
        n
        for n in zf.namelist()
        if n.startswith(folder + "/") and n.lower().endswith("patent.docx")
    )
    narrative = narrative_from_paragraphs(docx_paragraphs(zf.read(desc_name)))
    patent = parse_patent(docx_paragraphs(zf.read(patent_name)))
    category = DOCX_CATEGORY[nn]
    return {
        "pitch": narrative.get("pitch", brief.get("pitch", "")),
        "upgrade": narrative.get("upgrade", brief.get("upgrade", "")),
        "target": narrative.get("target", ""),
        "whyNow": narrative.get("whyNow", ""),
        "next": narrative.get("next", ""),
        "category": category,
        "claims": patent.pop("claims"),
        "fto": patent.pop("fto"),
        **patent,
    }


def idea_from_json(record: dict, brief: dict) -> dict:
    return {
        "pitch": record.get("pitch") or brief.get("pitch", ""),
        "upgrade": record.get("upgrade") or brief.get("upgrade", ""),
        "target": record.get("target", ""),
        "whyNow": record.get("whyNow", ""),
        "next": record.get("next", ""),
        "category": record.get("category", ""),
        "claims": record.get("claims") or [],
        "fto": record.get("fto", ""),
        "patentNumber": record.get("patentNumber") or brief.get("patentNumber", ""),
        "app": record.get("app", ""),
        "title": record.get("title", ""),
        "inventor": record.get("inventor", ""),
        "assignee": record.get("assignee", ""),
        "status": record.get("status") or brief.get("status", ""),
        "filing": record.get("filing", ""),
        "publication": record.get("pub", ""),
        "abandonDate": record.get("abandonDate", ""),
        "patentUrl": brief.get("patentUrl", ""),
        "short": record.get("short", ""),
    }


def main() -> None:
    if not ZIP_PATH.is_file():
        raise SystemExit(f"Zip not found: {ZIP_PATH}")
    with zipfile.ZipFile(ZIP_PATH) as zf:
        batch_all = json.loads(zf.read("_meta/batch-all.json"))
        rich_rows = json.loads(zf.read("_meta/batch-002-ideas.json"))
        rich_by_nn = {row["nn"]: row for row in rich_rows}
        ideas = []
        for brief in batch_all["ideas"]:
            nn = brief["nn"]
            folder = folder_for(zf, nn)
            slug = brief["slug"]
            if nn in rich_by_nn:
                parsed = idea_from_json(rich_by_nn[nn], brief)
            else:
                parsed = idea_from_docx(zf, folder, brief)
            number = parsed.get("patentNumber") or brief.get("patentNumber", "")
            url = parsed.get("patentUrl") or brief.get("patentUrl") or (
                f"https://patents.google.com/patent/{number}/en" if number else ""
            )
            category = parsed.get("category") or ""
            images = copy_images(zf, folder, slug)
            name = brief["name"]
            for image in images:
                label = "photograph" if image["kind"] == "photoreal" else "concept sheet"
                index = image["src"].rsplit("-", 1)[-1].split(".")[0]
                image["alt"] = f"{name}, {label} {index}"
            ideas.append(
                {
                    "nn": nn,
                    "slug": slug,
                    "name": name,
                    "short": parsed.get("short") or short_name(name),
                    "category": category,
                    "family": family_of(category),
                    "cardPitch": brief.get("pitch", ""),
                    "pitch": parsed.get("pitch") or brief.get("pitch", ""),
                    "upgrade": parsed.get("upgrade", ""),
                    "target": parsed.get("target", ""),
                    "whyNow": parsed.get("whyNow", ""),
                    "next": parsed.get("next", ""),
                    "claims": parsed.get("claims") or [],
                    "fto": parsed.get("fto", ""),
                    "patentNumber": number,
                    "app": parsed.get("app", ""),
                    "patentTitle": parsed.get("title", ""),
                    "inventor": parsed.get("inventor", ""),
                    "assignee": parsed.get("assignee", ""),
                    "status": parsed.get("status") or brief.get("status", ""),
                    "filing": parsed.get("filing", ""),
                    "publication": parsed.get("publication", ""),
                    "abandonDate": parsed.get("abandonDate", ""),
                    "patentUrl": url,
                    "espacenetUrl": espacenet(number),
                    "images": images,
                }
            )

    catalog = {
        "title": "Gian's Perfect Innovations",
        "source": "Abandoned US patent applications, batches 001-015",
        "disclaimer": (
            "These pages describe published US patent applications that were abandoned "
            "and never granted. They are concept revivals of those disclosures, not patents "
            "owned here, and not a freedom-to-operate opinion."
        ),
        "ideas": ideas,
    }
    payload = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    data_path = ROOT / "data" / "catalog.json"
    public_path = ROOT / "public" / "data" / "catalog.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(payload)
    public_path.write_text(payload)
    missing = []
    for idea in ideas:
        for key in ("pitch", "upgrade", "target", "whyNow", "next", "fto", "patentNumber", "category"):
            if not idea.get(key):
                missing.append(f"{idea['nn']} missing {key}")
        if len(idea["images"]) != 4:
            missing.append(f"{idea['nn']} images {len(idea['images'])}")
        if not idea["claims"]:
            missing.append(f"{idea['nn']} missing claims")
    if missing:
        raise SystemExit("Catalog incomplete:\n" + "\n".join(missing))
    print(f"Wrote {len(ideas)} ideas to {data_path}")


if __name__ == "__main__":
    main()
