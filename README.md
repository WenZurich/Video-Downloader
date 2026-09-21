# Video Downloader

A Windows x64 desktop app for downloading permitted video content as MP4 from any supported site.

Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp), it works with YouTube, Vimeo, X (Twitter), TikTok, Facebook, Bilibili and [thousands of other sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

## Features

- **Universal** – paste a link from any supported site, not just YouTube
- **Quality picker** – best available, or cap at 4K / 1440p / 1080p / 720p / 480p
- **MP4 output** – video and audio merged into a single MP4 via bundled FFmpeg
- **Playlists** – download a whole playlist in one go, organized into a folder
- **Themes** – Light, Dark, or follow the system setting
- **Languages** – 繁體中文 and English, switchable at runtime
- **Remembers** your last folder, theme, and language

## Limitations

Some content cannot be downloaded, by design:

- **DRM-protected streaming** (Netflix, Disney+, Prime Video and similar paid platforms) is encrypted and is not supported.
- **Private or sign-in-only** content needs your own browser cookies.

The app shows a clear message in these cases rather than failing silently.

Only download content you are authorized to save, and comply with each site's terms of service and applicable copyright law.

## Runtime

The EXE bundles its own Python runtime and FFmpeg. No separate Python installation is required.

## Build quality

The Windows executable is built on GitHub Actions with a hardened pipeline:

- Python syntax validation
- PySide6 offscreen UI smoke test
- FFmpeg runtime validation
- yt-dlp Chrome impersonation check
- Theme (light/dark/system) and language (zh-TW/en) render tests
- 125% / 150% / 200% HiDPI UI regression tests, with light + dark preview artifacts
- Windows icon
- Windows version metadata
- PyInstaller clean single-file build
- Packaged EXE smoke test
- SHA-256 checksum artifact

## Cloudflare / browser impersonation

The build includes yt-dlp's recommended `curl_cffi` impersonation backend and requests the Chrome fingerprint (`impersonate: chrome`) for both normal and generic extraction. This addresses the common "required impersonation dependency" 403 error. It does not guarantee that every site or network will bypass every anti-bot challenge; sites that require user cookies may still need browser cookies.

## Adding a language

Open `app.py`, copy an entry in the `TRANSLATIONS` dict, translate each value, and add the new code to `LANG_ORDER`. The UI and the CI language test pick it up automatically.
