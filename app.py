import os
import sys
import threading
from pathlib import Path

import imageio_ffmpeg
import yt_dlp
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget
)
from PySide6.QtCore import QUrl

APP_NAME = "YouTube MP4 Downloader"
APP_VERSION = "1.0.0"

LIGHT_QSS = """
QWidget {
    background: #F5F5F7;
    color: #1D1D1F;
    font-family: "Segoe UI";
    font-size: 14px;
}
QFrame#Card {
    background: #FFFFFF;
    border: 1px solid #E2E2E7;
    border-radius: 20px;
}
QLabel#Title {
    font-size: 28px;
    font-weight: 700;
}
QLabel#Subtitle, QLabel#Muted {
    color: #6E6E73;
}
QLabel#Section {
    font-size: 13px;
    font-weight: 650;
}
QLineEdit, QComboBox {
    background: #FAFAFC;
    border: 1px solid #D8D8DE;
    border-radius: 12px;
    padding: 0 13px;
    min-height: 42px;
}
QLineEdit:focus, QComboBox:focus {
    border: 2px solid #007AFF;
}
QComboBox::drop-down {
    border: none;
    width: 32px;
}
QPushButton {
    border: none;
    border-radius: 12px;
    min-height: 42px;
    padding: 0 18px;
    font-weight: 650;
}
QPushButton#Primary {
    color: white;
    background: #007AFF;
}
QPushButton#Primary:hover {
    background: #0068D9;
}
QPushButton#Secondary {
    color: #1D1D1F;
    background: #EEEEF2;
}
QPushButton#Secondary:hover {
    background: #E1E1E6;
}
QPushButton#Ghost {
    color: #1D1D1F;
    background: transparent;
    border: 1px solid #D4D4DA;
}
QPushButton#Ghost:hover {
    background: #F0F0F4;
}
QPushButton:disabled {
    color: #A1A1A6;
    background: #E9E9ED;
}
QFrame#StatusCard {
    background: #F7F7FA;
    border: 1px solid #ECECF0;
    border-radius: 14px;
}
QProgressBar {
    min-height: 8px;
    max-height: 8px;
    border: none;
    border-radius: 4px;
    background: #E5E5EA;
    text-align: center;
}
QProgressBar::chunk {
    border-radius: 4px;
    background: #007AFF;
}
"""

class DownloadWorker(QObject):
    progress = Signal(float, str, str)
    finished = Signal(str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, url: str, folder: str, quality: str):
        super().__init__()
        self.url = url
        self.folder = folder
        self.quality = quality
        self._cancel = threading.Event()

    def cancel(self):
        self._cancel.set()

    def _format_selector(self):
        limits = {
            "4K": 2160,
            "1440p": 1440,
            "1080p": 1080,
            "720p": 720,
            "480p": 480,
        }
        if self.quality == "最高畫質":
            return "bv*+ba/b"
        h = limits[self.quality]
        return f"bv*[height<={h}]+ba/b[height<={h}]"

    def _hook(self, data):
        if self._cancel.is_set():
            raise yt_dlp.utils.DownloadError("USER_CANCELLED")

        state = data.get("status")
        if state == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            current = data.get("downloaded_bytes") or 0
            pct = (current / total * 100.0) if total else 0.0

            details = []
            speed = data.get("speed")
            eta = data.get("eta")
            if speed:
                details.append(f"{speed / 1024 / 1024:.1f} MB/s")
            if eta is not None:
                details.append(f"約 {eta} 秒")
            detail = " · ".join(details) if details else "正在接收影片資料"
            self.progress.emit(pct, f"下載中 {pct:.1f}%", detail)

        elif state == "finished":
            self.progress.emit(100.0, "正在處理影片", "合併影像與音訊並輸出 MP4")

    def run(self):
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if not ffmpeg_exe or not os.path.isfile(ffmpeg_exe):
                raise RuntimeError(f"找不到內建 FFmpeg：{ffmpeg_exe}")

            options = {
                "format": self._format_selector(),
                "format_sort": ["res", "vcodec:h264", "acodec:aac"],
                "merge_output_format": "mp4",
                "outtmpl": os.path.join(self.folder, "%(title)s [%(id)s].%(ext)s"),
                "windowsfilenames": True,
                "noplaylist": True,
                "progress_hooks": [self._hook],
                "ffmpeg_location": ffmpeg_exe,
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

            self.finished.emit(info.get("title") or "影片")

        except Exception as exc:
            if self._cancel.is_set() or "USER_CANCELLED" in str(exc):
                self.cancelled.emit()
            else:
                self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(960, 690)
        self.setMinimumSize(820, 620)

        root = QWidget()
        self.setCentralWidget(root)
        page = QVBoxLayout(root)
        page.setContentsMargins(38, 30, 38, 30)
        page.setSpacing(18)

        head = QHBoxLayout()
        head.setSpacing(12)

        titles = QVBoxLayout()
        titles.setSpacing(4)
        title = QLabel(APP_NAME)
        title.setObjectName("Title")
        subtitle = QLabel("乾淨、直接，把影片下載成 MP4")
        subtitle.setObjectName("Subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)

        head.addLayout(titles)
        head.addStretch(1)

        self.version_label = QLabel(f"v{APP_VERSION}")
        self.version_label.setObjectName("Muted")
        head.addWidget(self.version_label, alignment=Qt.AlignTop)

        page.addLayout(head)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26, 26, 26, 24)
        card_layout.setSpacing(18)

        card_layout.addWidget(self._section_label("影片連結"))

        url_row = QHBoxLayout()
        url_row.setSpacing(10)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_edit.setClearButtonEnabled(True)
        self.paste_btn = QPushButton("貼上")
        self.paste_btn.setObjectName("Secondary")
        self.paste_btn.setFixedWidth(96)
        self.paste_btn.clicked.connect(self.paste_url)
        url_row.addWidget(self.url_edit, 1)
        url_row.addWidget(self.paste_btn)
        card_layout.addLayout(url_row)

        options = QHBoxLayout()
        options.setSpacing(16)

        quality_col = QVBoxLayout()
        quality_col.setSpacing(8)
        quality_col.addWidget(self._section_label("畫質"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["最高畫質", "4K", "1440p", "1080p", "720p", "480p"])
        quality_col.addWidget(self.quality_combo)

        format_col = QVBoxLayout()
        format_col.setSpacing(8)
        format_col.addWidget(self._section_label("輸出格式"))
        self.format_edit = QLineEdit("MP4")
        self.format_edit.setReadOnly(True)
        format_col.addWidget(self.format_edit)

        options.addLayout(quality_col, 1)
        options.addLayout(format_col, 1)
        card_layout.addLayout(options)

        card_layout.addWidget(self._section_label("儲存位置"))
        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        self.path_edit = QLineEdit(str(Path.home() / "Downloads"))
        self.browse_btn = QPushButton("選擇資料夾")
        self.browse_btn.setObjectName("Secondary")
        self.browse_btn.setFixedWidth(120)
        self.browse_btn.clicked.connect(self.choose_folder)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(self.browse_btn)
        card_layout.addLayout(path_row)

        status_card = QFrame()
        status_card.setObjectName("StatusCard")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(18, 14, 18, 16)
        status_layout.setSpacing(5)

        self.status_label = QLabel("準備完成")
        f = QFont("Segoe UI", 11)
        f.setWeight(QFont.DemiBold)
        self.status_label.setFont(f)

        self.detail_label = QLabel("貼上 YouTube 連結後即可開始下載")
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

        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.open_btn = QPushButton("開啟資料夾")
        self.open_btn.setObjectName("Ghost")
        self.open_btn.clicked.connect(self.open_folder)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("Ghost")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_download)

        self.download_btn = QPushButton("下載 MP4")
        self.download_btn.setObjectName("Primary")
        self.download_btn.setFixedWidth(156)
        self.download_btn.clicked.connect(self.start_download)

        action_row.addWidget(self.open_btn)
        action_row.addWidget(self.cancel_btn)
        action_row.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        action_row.addWidget(self.download_btn)
        card_layout.addLayout(action_row)

        note = QLabel("僅下載你有權保存的內容，並遵守 YouTube 使用條款與著作權規範。")
        note.setObjectName("Muted")
        card_layout.addWidget(note)

        page.addWidget(card, 1)

    def _section_label(self, text):
        label = QLabel(text)
        label.setObjectName("Section")
        return label

    def paste_url(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_edit.setText(text)
            self.url_edit.setFocus()
            self.url_edit.setCursorPosition(len(text))

    def choose_folder(self):
        current = self.path_edit.text().strip() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "選擇儲存資料夾", current)
        if folder:
            self.path_edit.setText(folder)

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
        self.url_edit.setEnabled(not busy)
        self.paste_btn.setEnabled(not busy)
        self.path_edit.setEnabled(not busy)
        self.browse_btn.setEnabled(not busy)

    def start_download(self):
        url = self.url_edit.text().strip()
        folder = self.path_edit.text().strip()

        if not url:
            QMessageBox.warning(self, "缺少網址", "請先貼上 YouTube 網址。")
            return
        if not folder:
            QMessageBox.warning(self, "缺少資料夾", "請先選擇儲存位置。")
            return

        Path(folder).mkdir(parents=True, exist_ok=True)
        self.progress.setValue(0)
        self.status_label.setText("正在解析影片")
        self.detail_label.setText("正在取得可用畫質…")
        self.set_busy(True)

        self.thread = QThread(self)
        self.worker = DownloadWorker(url, folder, self.quality_combo.currentText())
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
            self.status_label.setText("正在取消")
            self.detail_label.setText("目前片段完成後會停止")

    def on_progress(self, pct, title, detail):
        self.progress.setValue(int(max(0.0, min(100.0, pct)) * 10))
        self.status_label.setText(title)
        self.detail_label.setText(detail)

    def on_finished(self, title):
        self.progress.setValue(1000)
        self.status_label.setText("下載完成")
        self.detail_label.setText(title)
        self.set_busy(False)
        QMessageBox.information(self, "下載完成", f"{title}\n\n已儲存到：\n{self.path_edit.text()}")

    def on_failed(self, error):
        self.status_label.setText("下載失敗")
        self.detail_label.setText("請查看錯誤訊息後再試一次")
        self.set_busy(False)
        QMessageBox.critical(self, "下載失敗", error)

    def on_cancelled(self):
        self.progress.setValue(0)
        self.status_label.setText("已取消")
        self.detail_label.setText("下載已停止")
        self.set_busy(False)


def smoke_test(app: QApplication):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    if not ffmpeg or not os.path.isfile(ffmpeg):
        raise RuntimeError(f"Bundled FFmpeg missing: {ffmpeg}")

    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        if ydl is None:
            raise RuntimeError("yt-dlp initialization failed")

    window = MainWindow()
    window.resize(960, 690)
    window.show()
    app.processEvents()
    app.processEvents()

    assert window.url_edit.height() >= 42
    assert window.path_edit.height() >= 42
    assert window.download_btn.height() >= 42
    assert window.quality_combo.height() >= 42
    assert window.width() >= 820
    assert window.height() >= 620

    window.close()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet(LIGHT_QSS)

    if "--smoke-test" in sys.argv:
        smoke_test(app)
        return 0

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
