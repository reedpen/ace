# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Documentation cleanup: consistent install instructions, license/authorship placeholders, reduced duplicate README content, new `examples/` and `scripts/` helpers, expanded API reference (multimodal, ephys processors, config helpers).

## [0.1.0] - 2024-03-16

### Added
- Modern `pyproject.toml` with full dependency specification.
- `src` layout for better package isolation.
- `ace_neuro` package name.
- Integrated pipelines for Miniscope, Ephys, and Multimodal analysis.
- MkDocs documentation site.
- Automated CI for Python 3.10.

### Changed
- Reorganized source tree from `src2/` to `src/ace_neuro/`.
- Updated all internal imports to use the new package name.
- Simplified path management (removing explicit `.env` dependency).

### Removed
- Obsolete `src/` directory.
- Legacy `setup.py`.
- Stale root scripts and temporary README files.
