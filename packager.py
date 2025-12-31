import os
import json
import hashlib
import zipfile
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

import requests


# -----------------------------
# Hashing
# -----------------------------
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# -----------------------------
# Helpers
# -----------------------------
def file_kind(path: Path) -> str:
    return path.suffix.lower().lstrip(".") or "no_ext"


def build_summary(manifest, metadata):
    kinds = Counter(item["kind"] for item in manifest)

    lines = [
        "# Evidence Bundle Summary",
        "",
        f"**Case ID:** {metadata['case_id']}",
        f"**Analyst:** {metadata['analyst']}",
        f"**Source:** {metadata['source']}",
        f"**Created (UTC):** {metadata['created_at']}",
        "",
        f"**Total files:** {len(manifest)}",
        "",
        "## File types",
    ]

    for kind, count in kinds.items():
        lines.append(f"- {kind}: {count}")

    if metadata["notes"]:
        lines.extend(["", "## Notes", metadata["notes"]])

    return "\n".join(lines)


# -----------------------------
# Optional local AI (Ollama)
# -----------------------------
def ai_summary_local(summary_md: str, metadata: dict, model: str = "llama3") -> str:
    """
    Optional AI summary using a local Ollama model.
    Requires Ollama running on http://localhost:11434
    """
    try:
        prompt = f"""
Rewrite the following incident summary into a short executive summary.

Rules:
- bullet points only
- no speculation
- professional incident response tone
- include suggested next steps (max 3 bullets)

Metadata:
{json.dumps(metadata, indent=2)}

Summary:
{summary_md}
""".strip()

        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=30,
        )

        if r.status_code != 200:
            return ""

        return r.json().get("response", "").strip()

    except Exception:
        # AI is optional — never break the tool
        return ""


# -----------------------------
# Core packager
# -----------------------------
def package_evidence(
    input_dir: Path,
    output_zip: Path,
    metadata: dict,
    ai: bool = False,
    ai_model: str = "llama3",
):
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    metadata["created_at"] = created_at

    manifest = []
    hashes = []

    for root, _, files in os.walk(input_dir):
        for name in files:
            full = Path(root) / name
            rel = full.relative_to(input_dir).as_posix()

            entry = {
                "file": rel,
                "sha256": sha256_file(full),
                "size": full.stat().st_size,
                "kind": file_kind(full),
                "collected_at": created_at,
            }

            manifest.append(entry)
            hashes.append(f"{entry['sha256']}  {rel}")

    manifest.sort(key=lambda x: x["file"])
    summary = build_summary(manifest, metadata)

    ai_md = ""
    if ai:
        ai_md = ai_summary_local(summary, metadata, ai_model)

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for item in manifest:
            z.write(input_dir / item["file"], item["file"])

        z.writestr("manifest.json", json.dumps(manifest, indent=2))
        z.writestr("metadata.json", json.dumps(metadata, indent=2))
        z.writestr("hashes.sha256", "\n".join(hashes) + "\n")
        z.writestr("summary.md", summary)

        if ai_md:
            z.writestr("ai_summary.md", ai_md)

    print(f"[+] Created bundle: {output_zip}")
    print(f"[+] Files packaged: {len(manifest)}")
    if ai and not ai_md:
        print("[!] AI summary requested but not generated (Ollama not running or model unavailable).")


# -----------------------------
# CLI
# -----------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Package incident evidence into a verifiable forensic bundle."
    )
    ap.add_argument("input_dir", help="Evidence directory")
    ap.add_argument("-o", "--output", default="evidence_bundle.zip")
    ap.add_argument("--case-id", default="IR-0000")
    ap.add_argument("--analyst", default="Unknown")
    ap.add_argument("--source", default="SOC")
    ap.add_argument("--notes", default="")
    ap.add_argument(
        "--ai",
        action="store_true",
        help="Generate optional AI executive summary using local LLM (Ollama)",
    )
    ap.add_argument(
        "--ai-model",
        default="llama3",
        help="Ollama model name (default: llama3)",
    )
    args = ap.parse_args()

    metadata = {
        "case_id": args.case_id,
        "analyst": args.analyst,
        "source": args.source,
        "notes": args.notes,
    }

    package_evidence(
        Path(args.input_dir),
        Path(args.output),
        metadata,
        ai=args.ai,
        ai_model=args.ai_model,
    )


if __name__ == "__main__":
    main()
