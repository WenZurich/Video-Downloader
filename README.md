# Video Downloader

A Windows x64 desktop app for downloading permitted video content as MP4 from any supported site.

Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp), it works with YouTube, Vimeo, X (Twitter), TikTok, Facebook, Bilibili and [thousands of other sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

## Features

- **Universal** – paste a link from any supported site, not just YouTube
- **Download queue** – keep pasting links while downloads are running; new links are appended in order
- **Process-isolated downloads** – every download runs in a separate OS process; unsupported sites, yt-dlp errors, and even a hard worker crash can fail that row without taking down the GUI
- **Failure recovery** – transient failures get one conservative compatibility retry, failed rows stay in the queue, and they can be retried manually
- **Portable Windows package** – ships as an `onedir` ZIP instead of a self-extracting `onefile` EXE to reduce browser/antivirus heuristic false positives
- **YouTube compatibility fallback** – retryable YouTube failures can switch to the `web_safari` HLS client, then use the same lossless HLS → MP4 remux path
- **Sequential by default** – one download at a time for predictable bandwidth and stability
- **Optional concurrency** – switch to 2 or 3 simultaneous downloads when you want more throughput
- **Quality picker** – best available, or cap at 4K / 1440p / 1080p / 720p / 480p
- **MP4 output** – video and audio merged into a single MP4 via bundled FFmpeg
- **Lossless HLS/m3u8 remux** – HLS/m3u8 downloads are always finalized as MP4 with stream copy (`-c copy`), so the video/audio are not re-encoded
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

The portable folder bundles its own Python runtime and FFmpeg. No separate Python installation is required. Keep the extracted folder contents together and run `Video Downloader.exe`.

## Build quality

The Windows executable is built on GitHub Actions with a hardened pipeline:

- Python syntax validation
- PySide6 offscreen UI smoke test
- FFmpeg runtime validation
- Real HLS/m3u8 fixture test that remuxes to MP4 with `-c copy` and verifies the MP4 container
- yt-dlp Chrome impersonation check
- Theme (light/dark/system) and language (zh-TW/en) render tests
- Queue regression tests for multi-link paste, deduplication, ordering, sequential default, concurrency caps, failure retry isolation, hard worker-process crash isolation, and automatic continuation to the next queued item
- 125% / 150% / 200% HiDPI UI regression tests, with light + dark preview artifacts
- Windows icon
- Windows version metadata
- PyInstaller clean portable `onedir` build (`--noupx`, no self-extracting onefile wrapper)
- Packaged EXE smoke test
- SHA-256 checksum artifact

## Cloudflare / browser impersonation

The build includes yt-dlp's recommended `curl_cffi` impersonation backend and requests the Chrome fingerprint (`impersonate: chrome`) for both normal and generic extraction. This addresses the common "required impersonation dependency" 403 error. It does not guarantee that every site or network will bypass every anti-bot challenge; sites that require user cookies may still need browser cookies.

## Adding a language

Open `app.py`, copy an entry in the `TRANSLATIONS` dict, translate each value, and add the new code to `LANG_ORDER`. The UI and the CI language test pick it up automatically.


## Windows download reputation

The portable ZIP is intentionally built without PyInstaller's self-extracting `--onefile` wrapper because newly-built unsigned onefile executables can attract browser/antivirus heuristic warnings. The project also publishes the ZIP and its SHA-256 as a GitHub Release asset.

This build is still unsigned unless an Authenticode certificate is added. Packaging changes can reduce false positives, but they cannot guarantee Chrome Safe Browsing or Microsoft SmartScreen reputation. Authenticode signing is the reliable next step for publisher identity and reputation.
