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


## Cloudflare / browser impersonation

The build includes yt-dlp's recommended `curl_cffi` impersonation backend and enables `generic:impersonate` for generic extraction. This addresses the specific "required impersonation dependency" 403 error shown by yt-dlp. It does not guarantee that every site or network will bypass every anti-bot challenge; sites that require user cookies may still need browser cookies.
