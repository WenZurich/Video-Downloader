import os
import sys
import threading
from pathlib import Path

import imageio_ffmpeg
import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget
from PySide6.QtCore import QObject, Qt, QThread, Signal, QSettings, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget
)

APP_NAME = "Video Downloader"
APP_VERSION = "2.0.0"
ORG_NAME = "WenZurich"

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
# Each language is a flat dict of string keys. Adding a new language is just a
# matter of adding another entry here with the same keys.

TRANSLATIONS = {
    "zh_TW": {
        "language_name": "繁體中文",
        "app_title": "影片下載器",
        "subtitle": "貼上任何網址，下載成 MP4",
        "link_section": "影片連結",
        "url_placeholder": "貼上影片網址，支援 YouTube、Vimeo、X、TikTok 等上千個網站",
        "paste": "貼上",
        "quality": "畫質",
        "output_format": "輸出格式",
        "playlist": "播放清單",
        "playlist_single": "只下載這一部",
        "playlist_all": "下載整個播放清單",
        "save_location": "儲存位置",
        "choose_folder": "選擇資料夾",
        "open_folder": "開啟資料夾",
        "cancel": "取消",
        "download": "下載 MP4",
        "quality_best": "最高畫質",
        "ready": "準備完成",
        "ready_detail": "貼上影片連結後即可開始下載",
        "resolving": "正在解析影片",
        "resolving_detail": "正在取得可用畫質…",
        "downloading": "下載中 {pct:.1f}%",
        "receiving": "正在接收影片資料",
        "eta_seconds": "約 {eta} 秒",
        "processing": "正在處理影片",
        "processing_detail": "合併影像與音訊並輸出 MP4",
        "playlist_item": "第 {n} 部 · {pct:.1f}%",
        "done": "下載完成",
        "done_dialog_title": "下載完成",
        "done_saved_to": "已儲存到：",
        "failed": "下載失敗",
        "failed_detail": "請查看錯誤訊息後再試一次",
        "cancelling": "正在取消",
        "cancelling_detail": "目前片段完成後會停止",
        "cancelled": "已取消",
        "cancelled_detail": "下載已停止",
        "warn_no_url_title": "缺少網址",
        "warn_no_url": "請先貼上影片網址。",
        "warn_no_folder_title": "缺少資料夾",
        "warn_no_folder": "請先選擇儲存位置。",
        "note": "僅下載你有權保存的內容，並遵守各網站使用條款與著作權規範。",
        "theme": "主題",
        "theme_system": "跟隨系統",
        "theme_light": "淺色",
        "theme_dark": "深色",
        "language": "語言",
        "err_drm": "這個網站的影片有數位版權保護（DRM），無法下載。",
        "err_unsupported": "無法辨識這個網址的影片，或這個網站不支援。",
        "err_private": "這部影片是私人或需要登入才能觀看。",
        "err_generic": "下載時發生問題。",
    },
    "en": {
        "language_name": "English",
        "app_title": "Video Downloader",
        "subtitle": "Paste any link, download as MP4",
        "link_section": "Video link",
        "url_placeholder": "Paste a video URL — works with YouTube, Vimeo, X, TikTok and thousands more",
        "paste": "Paste",
        "quality": "Quality",
        "output_format": "Format",
        "playlist": "Playlist",
        "playlist_single": "This video only",
        "playlist_all": "Download whole playlist",
        "save_location": "Save to",
        "choose_folder": "Choose folder",
        "open_folder": "Open folder",
        "cancel": "Cancel",
        "download": "Download MP4",
        "quality_best": "Best quality",
        "ready": "Ready",
        "ready_detail": "Paste a video link to start",
        "resolving": "Resolving video",
        "resolving_detail": "Fetching available qualities…",
        "downloading": "Downloading {pct:.1f}%",
        "receiving": "Receiving video data",
        "eta_seconds": "about {eta}s left",
        "processing": "Processing video",
        "processing_detail": "Merging video and audio into MP4",
        "playlist_item": "Item {n} · {pct:.1f}%",
        "done": "Download complete",
        "done_dialog_title": "Download complete",
        "done_saved_to": "Saved to:",
        "failed": "Download failed",
        "failed_detail": "Check the error and try again",
        "cancelling": "Cancelling",
        "cancelling_detail": "Will stop after the current fragment",
        "cancelled": "Cancelled",
        "cancelled_detail": "Download stopped",
        "warn_no_url_title": "No URL",
        "warn_no_url": "Please paste a video URL first.",
        "warn_no_folder_title": "No folder",
        "warn_no_folder": "Please choose where to save.",
        "note": "Only download content you are authorized to save, and follow each site's terms and copyright law.",
        "theme": "Theme",
        "theme_system": "System",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "language": "Language",
        "err_drm": "This video is DRM-protected and cannot be downloaded.",
        "err_unsupported": "Couldn't read a video from this URL, or the site isn't supported.",
        "err_private": "This video is private or requires sign-in.",
        "err_generic": "Something went wrong during the download.",
    },
}

LANG_ORDER = ["zh_TW", "en"]


class I18n:
    """Tiny translation helper. Call tr(key, **fmt)."""

    def __init__(self, lang="zh_TW"):
        self.lang = lang if lang in TRANSLATIONS else "zh_TW"

    def set_language(self, lang):
        if lang in TRANSLATIONS:
            self.lang = lang

    def tr(self, key, **fmt):
        table = TRANSLATIONS.get(self.lang, TRANSLATIONS["zh_TW"])
        text = table.get(key, TRANSLATIONS["en"].get(key, key))
        if fmt:
            try:
                return text.format(**fmt)
            except (KeyError, IndexError, ValueError):
                return text
        return text


# ---------------------------------------------------------------------------
# Theming
# ---------------------------------------------------------------------------
# Two full palettes. The system option resolves to one of them at runtime.

PALETTES = {
    "light": {
        "bg": "#F6F6F8",
        "surface": "#FFFFFF",
        "surface_2": "#F1F1F5",
        "border": "#E4E4EA",
        "border_strong": "#D5D5DD",
        "text": "#17171A",
        "text_muted": "#6B6B73",
        "text_faint": "#9A9AA2",
        "field": "#FBFBFD",
        "accent": "#4F46E5",
        "accent_hover": "#4338CA",
        "accent_text": "#FFFFFF",
        "secondary": "#ECECF1",
        "secondary_hover": "#E1E1E8",
        "disabled_bg": "#EAEAEF",
        "disabled_text": "#A7A7AF",
        "track": "#E4E4EA",
    },
    "dark": {
        "bg": "#151519",
        "surface": "#1E1E24",
        "surface_2": "#26262E",
        "border": "#2E2E37",
        "border_strong": "#3A3A45",
        "text": "#F2F2F5",
        "text_muted": "#A2A2AD",
        "text_faint": "#71717C",
        "field": "#26262E",
        "accent": "#6366F1",
        "accent_hover": "#7C7EF5",
        "accent_text": "#FFFFFF",
        "secondary": "#2E2E37",
        "secondary_hover": "#383842",
        "disabled_bg": "#26262E",
        "disabled_text": "#5A5A63",
        "track": "#2E2E37",
    },
}


def build_qss(p):
    """Build the full stylesheet string from a palette dict."""
    return f"""
QWidget {{
    background: {p['bg']};
    color: {p['text']};
    font-family: "Segoe UI", "Microsoft JhengHei UI", sans-serif;
    font-size: 14px;
}}
QFrame#Card {{
    background: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: 20px;
}}
QLabel#Title {{
    font-size: 27px;
    font-weight: 700;
    color: {p['text']};
}}
QLabel#Subtitle {{
    color: {p['text_muted']};
    font-size: 14px;
}}
QLabel#Muted {{
    color: {p['text_muted']};
}}
QLabel#Faint {{
    color: {p['text_faint']};
    font-size: 12px;
}}
QLabel#Section {{
    font-size: 13px;
    font-weight: 600;
    color: {p['text_muted']};
}}
QLineEdit, QComboBox {{
    background: {p['field']};
    color: {p['text']};
    border: 1px solid {p['border_strong']};
    border-radius: 12px;
    padding: 0 13px;
    min-height: 42px;
    selection-background-color: {p['accent']};
    selection-color: {p['accent_text']};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 2px solid {p['accent']};
    padding: 0 12px;
}}
QLineEdit:read-only {{
    color: {p['text_muted']};
    background: {p['surface_2']};
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox QAbstractItemView {{
    background: {p['surface']};
    color: {p['text']};
    border: 1px solid {p['border_strong']};
    border-radius: 10px;
    padding: 4px;
    outline: none;
    selection-background-color: {p['accent']};
    selection-color: {p['accent_text']};
}}
QPushButton {{
    border: none;
    border-radius: 12px;
    min-height: 42px;
    padding: 0 18px;
    font-weight: 600;
}}
QPushButton#Primary {{
    color: {p['accent_text']};
    background: {p['accent']};
}}
QPushButton#Primary:hover {{
    background: {p['accent_hover']};
}}
QPushButton#Secondary {{
    color: {p['text']};
    background: {p['secondary']};
}}
QPushButton#Secondary:hover {{
    background: {p['secondary_hover']};
}}
QPushButton#Ghost {{
    color: {p['text']};
    background: transparent;
    border: 1px solid {p['border_strong']};
}}
QPushButton#Ghost:hover {{
    background: {p['surface_2']};
}}
QPushButton:disabled {{
    color: {p['disabled_text']};
    background: {p['disabled_bg']};
    border: none;
}}
QPushButton#Ghost:disabled {{
    background: transparent;
    border: 1px solid {p['border']};
    color: {p['disabled_text']};
}}
QFrame#StatusCard {{
    background: {p['surface_2']};
    border: 1px solid {p['border']};
    border-radius: 14px;
}}
QComboBox#Toolbar {{
    min-height: 34px;
    padding: 0 10px;
    border-radius: 9px;
    background: {p['surface_2']};
    border: 1px solid {p['border']};
}}
QProgressBar {{
    min-height: 8px;
    max-height: 8px;
    border: none;
    border-radius: 4px;
    background: {p['track']};
    text-align: center;
}}
QProgressBar::chunk {{
    border-radius: 4px;
    background: {p['accent']};
}}
"""


def resolve_theme(mode):
    """Map a theme mode ('system'|'light'|'dark') to a concrete palette key."""
    if mode == "light":
        return "light"
    if mode == "dark":
        return "dark"
    # system
    try:
        hints = QGuiApplication.styleHints()
        scheme = hints.colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return "dark"
    except Exception:
        pass
    return "light"


# ---------------------------------------------------------------------------
# Download worker
# ---------------------------------------------------------------------------

class DownloadWorker(QObject):
    progress = Signal(float, str, str)
    finished = Signal(str)
    failed = Signal(str)      # emits "err_key|raw message"
    cancelled = Signal()

    def __init__(self, url, folder, quality, playlist, i18n):
        super().__init__()
        self.url = url
        self.folder = folder
        self.quality = quality
        self.playlist = playlist
        self.i18n = i18n
        self._cancel = threading.Event()
        self._current_index = 0

    def cancel(self):
        self._cancel.set()

    def _format_selector(self):
        limits = {
            "4K": 2160, "1440p": 1440, "1080p": 1080,
            "720p": 720, "480p": 480,
        }
        if self.quality in ("最高畫質", "Best quality"):
            return "bv*+ba/b"
        h = limits.get(self.quality)
        if h is None:
            return "bv*+ba/b"
        return f"bv*[height<={h}]+ba/b[height<={h}]"

    def _hook(self, data):
        if self._cancel.is_set():
            raise yt_dlp.utils.DownloadError("USER_CANCELLED")

        state = data.get("status")
        if state == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            current = data.get("downloaded_bytes") or 0
            pct = (current / total * 100.0) if total else 0.0

            # Track playlist position for nicer status text.
            idx = data.get("info_dict", {}).get("playlist_index")
            if idx:
                self._current_index = idx

            details = []
            speed = data.get("speed")
            eta = data.get("eta")
            if speed:
                details.append(f"{speed / 1024 / 1024:.1f} MB/s")
            if eta is not None:
                details.append(self.i18n.tr("eta_seconds", eta=eta))
            detail = " · ".join(details) if details else self.i18n.tr("receiving")

            if self.playlist and self._current_index:
                title = self.i18n.tr("playlist_item", n=self._current_index, pct=pct)
            else:
                title = self.i18n.tr("downloading", pct=pct)
            self.progress.emit(pct, title, detail)

        elif state == "finished":
            self.progress.emit(
                100.0, self.i18n.tr("processing"), self.i18n.tr("processing_detail")
            )

    def run(self):
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if not ffmpeg_exe or not os.path.isfile(ffmpeg_exe):
                raise RuntimeError(f"Bundled FFmpeg missing: {ffmpeg_exe}")

            if self.playlist:
                outtmpl = os.path.join(
                    self.folder,
                    "%(playlist_title,uploader)s",
                    "%(playlist_index)03d - %(title)s [%(id)s].%(ext)s",
                )
            else:
                outtmpl = os.path.join(self.folder, "%(title)s [%(id)s].%(ext)s")

            options = {
                "format": self._format_selector(),
                "format_sort": ["res", "vcodec:h264", "acodec:aac"],
                "merge_output_format": "mp4",
                "outtmpl": outtmpl,
                "windowsfilenames": True,
                "noplaylist": not self.playlist,
                "yesplaylist": self.playlist,
                "ignoreerrors": self.playlist,  # skip a bad item, keep going
                "progress_hooks": [self._hook],
                "ffmpeg_location": ffmpeg_exe,
                # curl_cffi browser impersonation — Chrome fingerprint.
                # This is what actually helps against many anti-bot 403s.
                "impersonate": ImpersonateTarget("chrome"),
                "extractor_args": {
                    "generic": {"impersonate": ["chrome"]},
                },
                "retries": 10,
                "fragment_retries": 10,
                "continuedl": True,
                "concurrent_fragment_downloads": 4,
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(self.url, download=True)

            if self._cancel.is_set():
                self.cancelled.emit()
                return

            if info and info.get("_type") == "playlist":
                title = info.get("title") or "Playlist"
            else:
                title = (info or {}).get("title") or "Video"
            self.finished.emit(title)

        except Exception as exc:
            msg = str(exc)
            if self._cancel.is_set() or "USER_CANCELLED" in msg:
                self.cancelled.emit()
            else:
                self.failed.emit(self._classify_error(msg))

    def _classify_error(self, msg):
        low = msg.lower()
        if "drm" in low or "protected" in low:
            return "err_drm|" + msg
        if "private" in low or "sign in" in low or "log in" in low or "login" in low:
            return "err_private|" + msg
        if "unsupported url" in low or "no video" in low or "unable to extract" in low:
            return "err_unsupported|" + msg
        return "err_generic|" + msg


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self, settings=None):
        super().__init__()
        self.thread = None
        self.worker = None
        self.settings = settings or QSettings(ORG_NAME, APP_NAME)

        lang = self.settings.value("language", "zh_TW")
        self.theme_mode = self.settings.value("theme", "system")
        self.i18n = I18n(lang)

        self.setWindowTitle(APP_NAME)
        self.resize(960, 720)
        self.setMinimumSize(820, 660)

        root = QWidget()
        self.setCentralWidget(root)
        page = QVBoxLayout(root)
        page.setContentsMargins(38, 28, 38, 30)
        page.setSpacing(18)

        # ---- Header: title + toolbar (theme / language) ----
        head = QHBoxLayout()
        head.setSpacing(12)

        titles = QVBoxLayout()
        titles.setSpacing(3)
        self.title = QLabel()
        self.title.setObjectName("Title")
        self.subtitle = QLabel()
        self.subtitle.setObjectName("Subtitle")
        titles.addWidget(self.title)
        titles.addWidget(self.subtitle)
        head.addLayout(titles)
        head.addStretch(1)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("Toolbar")
        self.theme_combo.setFixedWidth(130)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        self.lang_combo = QComboBox()
        self.lang_combo.setObjectName("Toolbar")
        self.lang_combo.setFixedWidth(120)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        toolbar.addWidget(self.theme_combo)
        toolbar.addWidget(self.lang_combo)
        head.addLayout(toolbar)
        page.addLayout(head)

        # ---- Main card ----
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26, 24, 26, 24)
        card_layout.setSpacing(16)

        self.link_label = self._section_label()
        card_layout.addWidget(self.link_label)

        url_row = QHBoxLayout()
        url_row.setSpacing(10)
        self.url_edit = QLineEdit()
        self.url_edit.setClearButtonEnabled(True)
        self.paste_btn = QPushButton()
        self.paste_btn.setObjectName("Secondary")
        self.paste_btn.setFixedWidth(96)
        self.paste_btn.clicked.connect(self.paste_url)
        url_row.addWidget(self.url_edit, 1)
        url_row.addWidget(self.paste_btn)
        card_layout.addLayout(url_row)

        # Quality / format / playlist row
        options = QHBoxLayout()
        options.setSpacing(16)

        quality_col = QVBoxLayout()
        quality_col.setSpacing(8)
        self.quality_label = self._section_label()
        quality_col.addWidget(self.quality_label)
        self.quality_combo = QComboBox()
        quality_col.addWidget(self.quality_combo)

        format_col = QVBoxLayout()
        format_col.setSpacing(8)
        self.format_label = self._section_label()
        format_col.addWidget(self.format_label)
        self.format_edit = QLineEdit("MP4")
        self.format_edit.setReadOnly(True)
        format_col.addWidget(self.format_edit)

        playlist_col = QVBoxLayout()
        playlist_col.setSpacing(8)
        self.playlist_label = self._section_label()
        playlist_col.addWidget(self.playlist_label)
        self.playlist_combo = QComboBox()
        playlist_col.addWidget(self.playlist_combo)

        options.addLayout(quality_col, 1)
        options.addLayout(format_col, 1)
        options.addLayout(playlist_col, 1)
        card_layout.addLayout(options)

        # Save location
        self.save_label = self._section_label()
        card_layout.addWidget(self.save_label)
        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        saved_path = self.settings.value("folder", str(Path.home() / "Downloads"))
        self.path_edit = QLineEdit(saved_path)
        self.browse_btn = QPushButton()
        self.browse_btn.setObjectName("Secondary")
        self.browse_btn.setMinimumWidth(140)
        self.browse_btn.clicked.connect(self.choose_folder)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(self.browse_btn)
        card_layout.addLayout(path_row)

        # Status card
        status_card = QFrame()
        status_card.setObjectName("StatusCard")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(18, 14, 18, 16)
        status_layout.setSpacing(5)

        self.status_label = QLabel()
        f = QFont("Segoe UI", 11)
        f.setWeight(QFont.DemiBold)
        self.status_label.setFont(f)
        self.detail_label = QLabel()
        self.detail_label.setObjectName("Muted")

        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)

        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.detail_label)
        status_layout.addSpacing(6)
        status_layout.addWidget(self.progress)
        card_layout.addWidget(status_card)

        # Action row
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        self.open_btn = QPushButton()
        self.open_btn.setObjectName("Ghost")
        self.open_btn.clicked.connect(self.open_folder)
        self.cancel_btn = QPushButton()
        self.cancel_btn.setObjectName("Ghost")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.download_btn = QPushButton()
        self.download_btn.setObjectName("Primary")
        self.download_btn.setFixedWidth(160)
        self.download_btn.clicked.connect(self.start_download)
        action_row.addWidget(self.open_btn)
        action_row.addWidget(self.cancel_btn)
        action_row.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        action_row.addWidget(self.download_btn)
        card_layout.addLayout(action_row)

        self.note = QLabel()
        self.note.setObjectName("Faint")
        self.note.setWordWrap(True)
        card_layout.addWidget(self.note)

        page.addWidget(card, 1)

        # Populate combos & text, then apply theme.
        self._populate_static_combos()
        self.retranslate()
        self.apply_theme()

    # ---- helpers ----
    def _section_label(self):
        label = QLabel()
        label.setObjectName("Section")
        return label

    def _populate_static_combos(self):
        # Theme combo (store mode as data)
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        for mode in ("system", "light", "dark"):
            self.theme_combo.addItem("", mode)
        idx = {"system": 0, "light": 1, "dark": 2}.get(self.theme_mode, 0)
        self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.blockSignals(False)

        # Language combo (store lang code as data)
        self.lang_combo.blockSignals(True)
        self.lang_combo.clear()
        for code in LANG_ORDER:
            self.lang_combo.addItem(TRANSLATIONS[code]["language_name"], code)
        cur = LANG_ORDER.index(self.i18n.lang) if self.i18n.lang in LANG_ORDER else 0
        self.lang_combo.setCurrentIndex(cur)
        self.lang_combo.blockSignals(False)

    def retranslate(self):
        tr = self.i18n.tr
        self.title.setText(tr("app_title"))
        self.subtitle.setText(tr("subtitle"))
        self.link_label.setText(tr("link_section"))
        self.url_edit.setPlaceholderText(tr("url_placeholder"))
        self.paste_btn.setText(tr("paste"))
        self.quality_label.setText(tr("quality"))
        self.format_label.setText(tr("output_format"))
        self.playlist_label.setText(tr("playlist"))
        self.save_label.setText(tr("save_location"))
        self.browse_btn.setText(tr("choose_folder"))
        self.open_btn.setText(tr("open_folder"))
        self.cancel_btn.setText(tr("cancel"))
        self.download_btn.setText(tr("download"))
        self.note.setText(tr("note"))

        # Quality combo — preserve selection by index.
        q_idx = max(0, self.quality_combo.currentIndex())
        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()
        self.quality_combo.addItems(
            [tr("quality_best"), "4K", "1440p", "1080p", "720p", "480p"]
        )
        self.quality_combo.setCurrentIndex(q_idx)
        self.quality_combo.blockSignals(False)

        # Playlist combo
        p_idx = max(0, self.playlist_combo.currentIndex())
        self.playlist_combo.blockSignals(True)
        self.playlist_combo.clear()
        self.playlist_combo.addItems([tr("playlist_single"), tr("playlist_all")])
        self.playlist_combo.setCurrentIndex(p_idx)
        self.playlist_combo.blockSignals(False)

        # Theme combo labels
        self.theme_combo.blockSignals(True)
        self.theme_combo.setItemText(0, tr("theme_system"))
        self.theme_combo.setItemText(1, tr("theme_light"))
        self.theme_combo.setItemText(2, tr("theme_dark"))
        self.theme_combo.blockSignals(False)

        # Only reset status text if idle.
        if not self.cancel_btn.isEnabled():
            self.status_label.setText(tr("ready"))
            self.detail_label.setText(tr("ready_detail"))

    def apply_theme(self):
        key = resolve_theme(self.theme_mode)
        qss = build_qss(PALETTES[key])
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)

    # ---- toolbar handlers ----
    def on_theme_changed(self, index):
        self.theme_mode = self.theme_combo.itemData(index) or "system"
        self.settings.setValue("theme", self.theme_mode)
        self.apply_theme()

    def on_language_changed(self, index):
        code = self.lang_combo.itemData(index) or "zh_TW"
        self.i18n.set_language(code)
        self.settings.setValue("language", code)
        self.retranslate()

    # ---- actions ----
    def paste_url(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_edit.setText(text)
            self.url_edit.setFocus()
            self.url_edit.setCursorPosition(len(text))

    def choose_folder(self):
        current = self.path_edit.text().strip() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(
            self, self.i18n.tr("choose_folder"), current
        )
        if folder:
            self.path_edit.setText(folder)
            self.settings.setValue("folder", folder)

    def open_folder(self):
        folder = self.path_edit.text().strip()
        if not folder:
            return
        Path(folder).mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def set_busy(self, busy):
        self.download_btn.setEnabled(not busy)
        self.cancel_btn.setEnabled(busy)
        self.quality_combo.setEnabled(not busy)
        self.playlist_combo.setEnabled(not busy)
        self.url_edit.setEnabled(not busy)
        self.paste_btn.setEnabled(not busy)
        self.path_edit.setEnabled(not busy)
        self.browse_btn.setEnabled(not busy)
        self.lang_combo.setEnabled(not busy)

    def start_download(self):
        url = self.url_edit.text().strip()
        folder = self.path_edit.text().strip()
        tr = self.i18n.tr

        if not url:
            QMessageBox.warning(self, tr("warn_no_url_title"), tr("warn_no_url"))
            return
        if not folder:
            QMessageBox.warning(self, tr("warn_no_folder_title"), tr("warn_no_folder"))
            return

        Path(folder).mkdir(parents=True, exist_ok=True)
        self.settings.setValue("folder", folder)
        self.progress.setValue(0)
        self.status_label.setText(tr("resolving"))
        self.detail_label.setText(tr("resolving_detail"))
        self.set_busy(True)

        playlist = self.playlist_combo.currentIndex() == 1

        self.thread = QThread(self)
        self.worker = DownloadWorker(
            url, folder, self.quality_combo.currentText(), playlist, self.i18n
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.cancelled.connect(self.on_cancelled)

        for signal in (self.worker.finished, self.worker.failed, self.worker.cancelled):
            signal.connect(self.thread.quit)

        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_worker_refs)
        self.thread.start()

    def _clear_worker_refs(self):
        self.worker = None
        self.thread = None

    def cancel_download(self):
        if self.worker:
            self.worker.cancel()
            self.status_label.setText(self.i18n.tr("cancelling"))
            self.detail_label.setText(self.i18n.tr("cancelling_detail"))

    def on_progress(self, pct, title, detail):
        self.progress.setValue(int(max(0.0, min(100.0, pct)) * 10))
        self.status_label.setText(title)
        self.detail_label.setText(detail)

    def on_finished(self, title):
        tr = self.i18n.tr
        self.progress.setValue(1000)
        self.status_label.setText(tr("done"))
        self.detail_label.setText(title)
        self.set_busy(False)
        QMessageBox.information(
            self, tr("done_dialog_title"),
            f"{title}\n\n{tr('done_saved_to')}\n{self.path_edit.text()}"
        )

    def on_failed(self, payload):
        tr = self.i18n.tr
        # payload is "err_key|raw message"
        if "|" in payload:
            key, raw = payload.split("|", 1)
        else:
            key, raw = "err_generic", payload
        self.status_label.setText(tr("failed"))
        self.detail_label.setText(tr("failed_detail"))
        self.set_busy(False)
        friendly = tr(key)
        QMessageBox.critical(self, tr("failed"), f"{friendly}\n\n{raw}")

    def on_cancelled(self):
        tr = self.i18n.tr
        self.progress.setValue(0)
        self.status_label.setText(tr("cancelled"))
        self.detail_label.setText(tr("cancelled_detail"))
        self.set_busy(False)


# ---------------------------------------------------------------------------
# Smoke test (used by CI) & entry point
# ---------------------------------------------------------------------------

def smoke_test(app):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    if not ffmpeg or not os.path.isfile(ffmpeg):
        raise RuntimeError(f"Bundled FFmpeg missing: {ffmpeg}")

    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        if ydl is None:
            raise RuntimeError("yt-dlp initialization failed")
        if not ydl._impersonate_target_available(ImpersonateTarget()):
            raise RuntimeError("curl_cffi impersonation target is unavailable")

    # Test both themes and both languages render without error.
    settings = QSettings(ORG_NAME, APP_NAME + "-SmokeTest")
    settings.clear()
    window = MainWindow(settings=settings)
    window.resize(960, 720)

    for mode in ("system", "light", "dark"):
        window.theme_mode = mode
        window.apply_theme()
        app.processEvents()

    for code in LANG_ORDER:
        window.i18n.set_language(code)
        window.retranslate()
        app.processEvents()

    window.show()
    app.processEvents()
    app.processEvents()

    assert window.url_edit.height() >= 42
    assert window.path_edit.height() >= 42
    assert window.download_btn.height() >= 42
    assert window.quality_combo.height() >= 42
    assert window.playlist_combo.height() >= 42
    assert window.width() >= 820
    assert window.height() >= 660

    window.close()
    settings.clear()


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    if "--smoke-test" in sys.argv:
        smoke_test(app)
        return 0

    window = MainWindow()
    window.show()

    # Repaint on live OS theme changes while in "system" mode.
    def on_scheme_changed(_):
        if window.theme_mode == "system":
            window.apply_theme()
    try:
        QGuiApplication.styleHints().colorSchemeChanged.connect(on_scheme_changed)
    except Exception:
        pass

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
