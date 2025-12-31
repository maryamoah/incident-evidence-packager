\# Incident Evidence Packager



A lightweight Python utility for packaging incident response and digital forensics evidence into a single, verifiable bundle.



\## What it does

\- Computes SHA256 hashes for all evidence files

\- Generates a structured manifest and metadata

\- Produces a portable ZIP bundle for handover, review, or archiving



\## Why

During investigations, evidence is often scattered across logs, exports, and files.  

This tool provides a simple, deterministic way to preserve integrity and context.



\## Usage



```bash

python packager.py <evidence\_dir> \\

&nbsp; --case-id IR-2025-001 \\

&nbsp; --analyst "Analyst Name" \\

&nbsp; --source "SOC"



