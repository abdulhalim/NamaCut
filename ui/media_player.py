# --------------------------------------------------
# MediaPlayer Module
# Custom media player widget with video transformation and cropping capabilities
# --------------------------------------------------

from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer, QUrl
from PyQt5.QtGui import QTransform, QPainter
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem

from ui.crop_widget import CropOverlay

# --------------------------------------------------
# MediaPlayer Class
# Main media player widget with transformation and cropping support
# --------------------------------------------------
class MediaPlayer(QWidget):
    positionChanged = pyqtSignal(int)
    durationChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.media_player = QMediaPlayer()
        self.media_player.setVolume(100)

        # Transformation states
        self.current_rotation = 0
        self.flip_horizontal = False
        self.flip_vertical = False
        self.crop_rect = None
        self.crop_mode = False

        # UI components
        self.crop_overlay = None
        self.video_item = None
        self.scene = None
        self.view = None

        self.init_ui()
        self.setup_connections()

    # --------------------------------------------------
    # UI Initialization
    # --------------------------------------------------
    def init_ui(self):
        self.setMinimumSize(400, 300)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.video_container = QWidget()
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(0, 0, 0, 0)

        self.view = QGraphicsView()
        self.view.setStyleSheet("background-color: black;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        self.video_item = QGraphicsVideoItem()
        self.video_item.setAspectRatioMode(Qt.KeepAspectRatio)
        self.scene.addItem(self.video_item)

        self.video_layout.addWidget(self.view)

        self.crop_overlay = CropOverlay(self.view.viewport())
        self.crop_overlay.crop_changed.connect(self.on_crop_changed)
        self.crop_overlay.hide()

        self.main_layout.addWidget(self.video_container)
        self.setLayout(self.main_layout)

    # --------------------------------------------------
    # Signal Connections
    # --------------------------------------------------
    def setup_connections(self):
        self.media_player.positionChanged.connect(self.positionChanged.emit)
        self.media_player.durationChanged.connect(self.durationChanged.emit)

    # --------------------------------------------------
    # Video Loading and Management
    # --------------------------------------------------
    def load_video(self, video_path: str) -> bool:
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
        self.media_player.setVideoOutput(self.video_item)

        # Reset transformation states
        self.current_rotation = 0
        self.flip_horizontal = False
        self.flip_vertical = False
        self.crop_rect = None
        self.crop_mode = False
        self.video_item.setTransform(QTransform())
        self.crop_overlay.hide()

        QTimer.singleShot(200, self.fit_video_in_view)
        return True

    def fit_video_in_view(self):
        if self.video_item and self.video_item.nativeSize().isValid():
            self.view.fitInView(self.video_item, Qt.KeepAspectRatio)
            if self.crop_overlay and self.crop_mode:
                self._update_crop_overlay_bounds()

    def _update_crop_overlay_bounds(self):
        if not self.video_item or not self.view or not self.crop_overlay:
            return

        video_scene_rect = self.video_item.sceneBoundingRect()
        video_view_rect = self.view.mapFromScene(video_scene_rect).boundingRect()
        viewport_rect = self.view.viewport().rect()
        final_bounds = video_view_rect.intersected(viewport_rect)

        if final_bounds.isValid():
            self.crop_overlay.set_video_bounds(final_bounds)
            self.crop_overlay.setFixedSize(self.view.viewport().size())

    # --------------------------------------------------
    # Playback Control Methods
    # --------------------------------------------------
    def play(self):
        self.media_player.play()

    def pause(self):
        self.media_player.pause()

    def stop(self):
        """Stop media playback without clearing media"""
        try:
            self.media_player.pause()
            self.media_player.stop()
            self.media_player.setPosition(0)
            print("MediaPlayer: Playback stopped (media preserved)")
            
        except Exception as e:
            print(f"MediaPlayer stop error: {e}")

    def set_position_ms(self, milliseconds: int):
        self.media_player.setPosition(milliseconds)

    def get_current_time(self) -> float:
        return self.media_player.position() / 1000.0

    # --------------------------------------------------
    # Video Transformation Methods
    # --------------------------------------------------
    def rotate_left(self):
        self.current_rotation = (self.current_rotation - 90) % 360
        self.apply_transformations()

    def rotate_right(self):
        self.current_rotation = (self.current_rotation + 90) % 360
        self.apply_transformations()

    def flip_h(self):
        self.flip_horizontal = not self.flip_horizontal
        self.apply_transformations()

    def flip_v(self):
        self.flip_vertical = not self.flip_vertical
        self.apply_transformations()

    def apply_transformations(self):
        transform = QTransform()

        rect = self.video_item.boundingRect()
        if not rect.isValid():
            self.video_item.setTransform(QTransform())
            return

        center = rect.center()
        transform.translate(center.x(), center.y())

        if self.current_rotation != 0:
            transform.rotate(self.current_rotation)

        sx = -1 if self.flip_horizontal else 1
        sy = -1 if self.flip_vertical else 1
        transform.scale(sx, sy)

        transform.translate(-center.x(), -center.y())
        self.video_item.setTransform(transform)
        self.fit_video_in_view()

    def reset_transformations(self):
        self.current_rotation = 0
        self.flip_horizontal = False
        self.flip_vertical = False
        self.crop_rect = None

        if self.crop_mode:
            self.toggle_crop_mode()

        self.video_item.setTransform(QTransform())
        self.fit_video_in_view()

    # --------------------------------------------------
    # Crop Mode Management
    # --------------------------------------------------
    def toggle_crop_mode(self) -> bool:
        self.crop_mode = not self.crop_mode

        if self.crop_mode:
            self.crop_overlay.setParent(self.view.viewport())
            self.crop_overlay.setFixedSize(self.view.viewport().size())
            self.crop_overlay.show()
            self.crop_overlay.raise_()
            self._update_crop_overlay_bounds()
        else:
            self.crop_overlay.hide()
            self.crop_rect = None

        return self.crop_mode

    def set_crop_aspect_ratio(self, width: int, height: int):
        if self.crop_overlay:
            self.crop_overlay.set_aspect_ratio(width, height)

    def on_crop_changed(self, rect: QRect):
        if not rect.isValid() or not self.video_item or not self.crop_overlay:
            return

        top_left_view = self.crop_overlay.mapTo(self.view.viewport(), rect.topLeft())
        bottom_right_view = self.crop_overlay.mapTo(self.view.viewport(), rect.bottomRight())

        top_left_scene = self.view.mapToScene(top_left_view)
        bottom_right_scene = self.view.mapToScene(bottom_right_view)

        video_bounds = self.video_item.sceneBoundingRect()
        if not video_bounds.isValid() or video_bounds.width() == 0 or video_bounds.height() == 0:
            return

        tlx = max(top_left_scene.x(), video_bounds.left())
        tly = max(top_left_scene.y(), video_bounds.top())
        brx = min(bottom_right_scene.x(), video_bounds.right())
        bry = min(bottom_right_scene.y(), video_bounds.bottom())

        if brx <= tlx or bry <= tly:
            return

        x_rel = (tlx - video_bounds.x()) / video_bounds.width()
        y_rel = (tly - video_bounds.y()) / video_bounds.height()
        w_rel = (brx - tlx) / video_bounds.width()
        h_rel = (bry - tly) / video_bounds.height()

        native_size = self.video_item.nativeSize()
        if native_size.isValid() and native_size.width() > 0 and native_size.height() > 0:
            x_scaled = max(0, int(round(x_rel * native_size.width())))
            y_scaled = max(0, int(round(y_rel * native_size.height())))
            w_scaled = max(1, int(round(w_rel * native_size.width())))
            h_scaled = max(1, int(round(h_rel * native_size.height())))

            if x_scaled + w_scaled > native_size.width():
                w_scaled = native_size.width() - x_scaled
            if y_scaled + h_scaled > native_size.height():
                h_scaled = native_size.height() - y_scaled

            self.crop_rect = (x_scaled, y_scaled, w_scaled, h_scaled)

    def get_current_crop_rect(self):
        if not self.crop_mode or not self.crop_overlay:
            return None
        
        rect = self.crop_overlay.crop_rect
        if not rect.isValid():
            return None
        
        top_left_view = self.crop_overlay.mapTo(self.view.viewport(), rect.topLeft())
        bottom_right_view = self.crop_overlay.mapTo(self.view.viewport(), rect.bottomRight())

        top_left_scene = self.view.mapToScene(top_left_view)
        bottom_right_scene = self.view.mapToScene(bottom_right_view)

        video_bounds = self.video_item.sceneBoundingRect()
        if not video_bounds.isValid() or video_bounds.width() == 0 or video_bounds.height() == 0:
            return None

        tlx = max(top_left_scene.x(), video_bounds.left())
        tly = max(top_left_scene.y(), video_bounds.top())
        brx = min(bottom_right_scene.x(), video_bounds.right())
        bry = min(bottom_right_scene.y(), video_bounds.bottom())

        if brx <= tlx or bry <= tly:
            return None

        x_rel = (tlx - video_bounds.x()) / video_bounds.width()
        y_rel = (tly - video_bounds.y()) / video_bounds.height()
        w_rel = (brx - tlx) / video_bounds.width()
        h_rel = (bry - tly) / video_bounds.height()

        native_size = self.video_item.nativeSize()
        if native_size.isValid() and native_size.width() > 0 and native_size.height() > 0:
            x_scaled = max(0, int(round(x_rel * native_size.width())))
            y_scaled = max(0, int(round(y_rel * native_size.height())))
            w_scaled = max(1, int(round(w_rel * native_size.width())))
            h_scaled = max(1, int(round(h_rel * native_size.height())))

            if x_scaled + w_scaled > native_size.width():
                w_scaled = native_size.width() - x_scaled
            if y_scaled + h_scaled > native_size.height():
                h_scaled = native_size.height() - y_scaled

            return (x_scaled, y_scaled, w_scaled, h_scaled)
        
        return None

    # --------------------------------------------------
    # Video Filter Generation
    # Build FFmpeg filter string from current transformations
    # --------------------------------------------------
    def get_video_filters(self) -> str or None:
        filters = []

        current_crop = self.get_current_crop_rect()
        if current_crop and self.crop_mode:
            x, y, w, h = current_crop
            filters.append(f"crop={w}:{h}:{x}:{y}")

        if self.current_rotation == 90:
            filters.append("transpose=1")
        elif self.current_rotation == 180:
            filters.append("transpose=1,transpose=1")
        elif self.current_rotation == 270:
            filters.append("transpose=2")

        if self.flip_horizontal:
            filters.append("hflip")
        if self.flip_vertical:
            filters.append("vflip")

        return ",".join(filters) if filters else None

    # --------------------------------------------------
    # Event Handlers
    # --------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._handle_resize_and_update_overlay)

    def _handle_resize_and_update_overlay(self):
        self.fit_video_in_view()
        if self.crop_overlay and self.crop_mode:
            self.crop_overlay.setFixedSize(self.view.viewport().size())
            self._update_crop_overlay_bounds()

    # --------------------------------------------------
    # Cleanup Methods
    # --------------------------------------------------
    def close(self):
        try:
            self.media_player.stop()
            self.media_player.setMedia(QMediaContent())
        except Exception:
            pass
        super().close()