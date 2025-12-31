import os
import json
import hashlib
import zipfile
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


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


def package_evidence(input_dir: Path, output_zip: Path, metadata: dict):
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

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for item in manifest:
            z.write(input_dir / item["file"], item["file"])

        z.writestr("manifest.json", json.dumps(manifest, indent=2))
        z.writestr("metadata.json", json.dumps(metadata, indent=2))
        z.writestr("hashes.sha256", "\n".join(hashes) + "\n")
        z.writestr("summary.md", summary)

    print(f"[+] Created bundle: {output_zip}")
    print(f"[+] Files packaged: {len(manifest)}")


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
    args = ap.parse_args()

    metadata = {
        "case_id": args.case_id,
        "analyst": args.analyst,
        "source": args.source,
        "notes": args.notes,
    }

    package_evidence(Path(args.input_dir), Path(args.output), metadata)


if __name__ == "__main__":
    main()
