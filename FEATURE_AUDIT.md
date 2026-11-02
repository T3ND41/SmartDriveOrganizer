# Feature and implementation audit — v0.8.1

**Audit date:** 2 November 2026  
**Repository:** https://github.com/T3ND41/SmartDriveOrganizer  
**Purpose:** Record the implemented scope and distinguish it from roadmap concepts discussed during research. This is an implementation and CI review, not a claim that every machine, drive or file format has been physically tested.

## Implemented capabilities

| Capability | Current implementation | Evidence / boundaries |
|---|---|---|
| Recursive deep scan | Scan one or several selected folders and mounted drives recursively; deduplicate nested roots; report inaccessible/skipped locations; avoid following symlinks, junctions and other reparse points. | `scanner.py`; `tests/test_scanner.py`. Protected Windows, recovery, application and dependency locations are intentionally excluded. |
| Exact file-format selection | Select broad file categories and individual extensions; the same filters apply to manual scans and watch folders. | `file_types.py`, `topic_rules_ui.py`, `automation.py`; `tests/test_file_types.py`. |
| Keyword and topic grouping | Built-in and user-defined topic rules, multiple keywords, partial/contains matching, selected-topic mode and custom destination folders. | `classifier.py`, `scanner.py`; `tests/test_classifier.py`, `tests/test_scanner.py`. |
| Repeated-name discovery | Finds repeated words and short phrases across different filenames, groups by file family, and presents suggestions for approval, rejection or renaming. | `discovery.py`, `discovery_ui.py`; `tests/test_discovery.py`. This is filename-pattern discovery, not automatic discovery from every document's full text. |
| Local full-text search | SQLite/FTS index with filename and supported extracted text, plus location, category, extension, topic, modified-date and size filters. | `search_index.py`, `search_dashboard.py`; `tests/test_search_index.py`. Index contents remain local to the device. |
| Supported document extraction | Optional local readers for PDF, DOCX, XLSX/XLSM, PPTX, plain text, CSV/TSV, HTML/XML, RTF, source text, EML and Outlook MSG; legacy DOC/XLS/PPT can use already-installed Office on Windows. | `content_reader.py`, `requirements-content.txt`; `tests/test_content_reader.py`. Unsupported, encrypted, damaged, oversized or locked files may be indexed by metadata only. |
| Review before file changes | Scanning and discovery are read-only. The user reviews a plan and explicitly chooses Apply. | `gui.py`, `scanner.py`, `operations.py`; `tests/test_workflow.py`, `tests/test_operations.py`. |
| Safe Copy and Move | Collision-safe destinations, verified copies, checksum-verified cross-volume moves, per-file journals, and Undo for Move when the original path is available. Apply revalidates source location, file type and previewed size. | `operations.py`; `tests/test_operations.py`. Copy is the safer first-use choice. |
| Duplicate and version review | Reports exact SHA-256 duplicates, likely filename versions and high text overlap. Only exact duplicate copies can be sent to the OS Recycle Bin, after explicit confirmation and fresh hash checks; possible versions and near-matches remain review-only. | `duplicates.py`, search dashboard; `tests/test_duplicates.py`. This later feature supersedes the older 0.3.0 research note that duplicate cleanup was not yet included. No permanent-delete feature is provided. |
| Background watch folders | Polls explicitly selected folders, baselines existing files, waits for new files to become stable, applies saved rules, persists state in SQLite and writes activity records. | `automation.py`, `automation_ui.py`; `tests/test_automation.py`. Poll-based, not a real-time filesystem event service; it runs only in the signed-in session while the machine is awake. |
| Adaptive local memory | Saves approved/rejected discovery patterns and user-taught filing corrections locally; rules can be reviewed and edited. | `learning.py`, `memory_ui.py`; `tests/test_learning.py`. |
| Themes and operation controls | Light, Dark and Redline themes; progress reporting; Pause, Resume and Cancel during supported active jobs. | `theme.py`, `operation_control.py`, `gui.py`; `tests/test_theme.py`, `tests/test_operation_control.py`. Pause state is not persisted after application exit. |
| GitHub publishing | Optional preview-first publishing of allowlisted source files and approved shared topic rules; excludes personal settings, databases and user documents; checks for common secret patterns; uses Git argument lists without shell execution. | `github_publish.py`; `tests/test_github_publish.py`. v0.8.1 also rejects symlink/reparse-point paths in the repository publishing target. |
| Windows distribution and updates | Per-user installer, portable PowerShell launcher, SHA-256 package verification, release-version matching and in-app notification for a newer official release. | `install.ps1`, `run.ps1`, `update_check.py`; `tests/test_distribution_files.py`, `tests/test_update_check.py`. In-app update check opens the release page; it does not silently replace the running program. |

## Security and reliability hardening in v0.8.1

- PDF reading requires pypdf 6.21.4 or later.
- Office ZIP containers are checked before parsing: at most 10,000 entries, 64 MB per entry, 256 MB aggregate uncompressed size and a 1,000:1 maximum compression ratio for large entries. DOCX XML members are capped at 16 MB.
- Email MIME traversal stops after 1,000 parts.
- PowerPoint macro automation is disabled before opening legacy presentations for text extraction.
- Apply refuses a missing, changed-size, non-regular, linked/reparse-point source or a path outside the roots selected for that scan.
- The GitHub source publisher refuses repository-relative writes that traverse symlinks or reparse points.
- Release workflow write permission is scoped to the job that publishes the release.

## Discussed or researched, but not included as working features

These items appeared in research notes or roadmap discussions. They are **not implemented in v0.8.1** and should not be mistaken for existing functionality:

1. **Local AI / LLM semantic classification or embedding search** (including optional Ollama integration). Current classification is deterministic filename/keyword matching and supported document text; there is no model-backed semantic ranking.
2. **OCR** for scanned/image-only PDFs and images.
3. **Image understanding**, video keyframe analysis, audio transcription or automatic media descriptions. Images, video and audio are handled through filename, extension, available metadata and user-defined rules.
4. **Full-text discovery of unknown topics.** The discovery suggestions use repeated filename patterns; document text is used for matching saved rules and local text search.
5. **Persistent pause recovery after closing the app.** Active-job Pause/Resume is session-bound. Operation journals preserve completed actions and support Move recovery/undo.
6. **Real-time filesystem event monitoring.** Background monitoring uses polling with a stability check.
7. **A complete scan of every path on a device.** Windows/system/recovery/dependency locations, links, inaccessible folders, offline volumes, encrypted files and damaged storage can be skipped for safety or availability.

These are separate roadmap candidates. Adding them safely requires explicit choices about model and parser dependencies, resource budgets, privacy, false-positive handling and test coverage.

## Verification boundary

The v0.8.1 pull-request workflow passed the automated Windows and Linux test suites, rendered the Light/Dark/Redline UI previews, and built the Windows executable. Tests use temporary folders and synthetic fixtures. CI does **not** replace testing on a physical multi-drive Windows machine, does not prove performance on multi-terabyte disks, and cannot verify access to a user's particular network/cloud drives or Office installation.
