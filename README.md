# Incident Evidence Packager

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-success)

A lightweight, educational Python tool for packaging digital forensics and incident
response evidence into a single, verifiable bundle.

---

## DFIR Toolchain Overview

![DFIR Toolchain](docs/dfir_toolchain_diagram.png)

This tool represents the **collection** phase of a DFIR workflow:
**collect → verify → reconstruct**.

---

## Purpose

During investigations, evidence is often scattered across logs and artifacts.
This tool creates a structured, integrity-preserving evidence bundle suitable
for operational use, training, and research.

---

## Usage

```bash
python packager.py <evidence_dir>   --case-id IR-2025-001   --analyst "Analyst Name"   --source "SOC"
```

---

## Output

- `manifest.json`
- `metadata.json`
- `hashes.sha256`
- `summary.md`
- original evidence files

---

## Educational Value

- Demonstrates forensic evidence handling
- Produces reproducible artifacts
- No external services or APIs

---

## License

MIT
