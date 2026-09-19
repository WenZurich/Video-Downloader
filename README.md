# YouTube MP4 Downloader

Windows x64 desktop app for downloading permitted YouTube content as MP4.

## Build quality

The Windows executable is built on GitHub Actions using the same hardened pipeline style as MP3-Organizer:

- Python syntax validation
- PySide6 offscreen UI smoke test
- FFmpeg runtime validation
- 125% / 150% / 200% HiDPI UI regression tests
- Windows icon
- Windows version metadata
- PyInstaller clean single-file build
- Packaged EXE smoke test
- SHA-256 checksum artifact

## Runtime

The EXE bundles its own Python runtime and FFmpeg dependency. No separate Python installation is required.

Only download content you are authorized to save and comply with YouTube's terms and applicable copyright law.
