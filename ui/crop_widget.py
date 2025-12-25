# --------------------------------------------------
# Crop Widget Module
# Interactive crop overlay for video selection with resizable handles
# --------------------------------------------------

from PyQt5.QtCore import Qt, QRect, QRectF, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QCursor, QPainterPath
from PyQt5.QtWidgets import QWidget

# --------------------------------------------------
# CropOverlay Class
# Transparent overlay widget for crop selection with interactive handles
# --------------------------------------------------
class CropOverlay(QWidget):
    crop_changed = pyqtSignal(QRect)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Crop rectangle and settings
        self.crop_rect = QRect()
        self.video_bounds = QRect()   # Actual video bounds in view
        self.aspect_ratio = None      # None = free, number = width / height
        self.min_size = 50            # Minimum crop size (pixels)

        # Drag state
        self.dragging = False
        self.resize_handle = None
        self.drag_start_pos = QPoint()
        self.drag_start_rect = QRect()

        # Resize handles around rectangle
        self.handles = {
            'top_left': QRect(0, 0, 12, 12),
            'top_right': QRect(0, 0, 12, 12),
            'bottom_left': QRect(0, 0, 12, 12),
            'bottom_right': QRect(0, 0, 12, 12),
            'top': QRect(0, 0, 12, 12),
            'bottom': QRect(0, 0, 12, 12),
            'left': QRect(0, 0, 12, 12),
            'right': QRect(0, 0, 12, 12),
        }

        self.setMouseTracking(True)

    # --------------------------------------------------
    # Video Bounds and Aspect Ratio Setup
    # Set video boundaries and maintain aspect ratio constraints
    # --------------------------------------------------
    def set_video_bounds(self, bounds: QRect):
        self.video_bounds = QRect(bounds)
        self.ensure_crop_within_bounds()

    def set_aspect_ratio(self, width: int, height: int):
        if width == 0 or height == 0:
            self.aspect_ratio = None
        else:
            self.aspect_ratio = float(width) / float(height)

        # If we have a crop, fit it to the new aspect ratio
        if self.aspect_ratio and not self.crop_rect.isEmpty():
            self._apply_aspect_ratio_to_rect(keep_center=True)

    # --------------------------------------------------
    # Crop Bounds Management
    # Ensure crop rectangle stays within video boundaries
    # --------------------------------------------------
    def ensure_crop_within_bounds(self):
        if not self.video_bounds.isValid():
            self.update()
            return

        if self.crop_rect.isEmpty():
            # Initial rectangle: 75% of video, centered
            w = int(self.video_bounds.width() * 0.75)
            h = int(self.video_bounds.height() * 0.75)

            # Minimum size
            w = max(w, self.min_size)
            h = max(h, self.min_size)

            if self.aspect_ratio:
                w = min(w, self.video_bounds.width())
                h_from_w = int(w / self.aspect_ratio)
                if h_from_w > self.video_bounds.height():
                    h = self.video_bounds.height()
                    w = int(h * self.aspect_ratio)
                else:
                    h = h_from_w

            x = self.video_bounds.x() + (self.video_bounds.width() - w) // 2
            y = self.video_bounds.y() + (self.video_bounds.height() - h) // 2
            self.crop_rect = QRect(x, y, w, h)
        else:
            self.crop_rect = self.constrain_to_bounds(self.crop_rect)

        if not self.video_bounds.contains(self.crop_rect):
            self.crop_rect.moveCenter(self.video_bounds.center())
            self.crop_rect = self.constrain_to_bounds(self.crop_rect)

        self.update_handles()
        self.update()

    def constrain_to_bounds(self, rect: QRect) -> QRect:
        if not self.video_bounds.isValid():
            return QRect(rect)

        bounds = self.video_bounds
        constrained = QRect(rect)

        # Keep within bounds
        if constrained.left() < bounds.left():
            constrained.moveLeft(bounds.left())
        if constrained.top() < bounds.top():
            constrained.moveTop(bounds.top())
        if constrained.right() > bounds.right():
            constrained.moveRight(bounds.right())
        if constrained.bottom() > bounds.bottom():
            constrained.moveBottom(bounds.bottom())

        # Minimum size
        if constrained.width() < self.min_size:
            constrained.setWidth(self.min_size)
        if constrained.height() < self.min_size:
            constrained.setHeight(self.min_size)

        # Intersect with bounds if needed
        if not bounds.contains(constrained):
            constrained = constrained.intersected(bounds)

        # Apply fixed aspect ratio if set
        if self.aspect_ratio:
            self.crop_rect = constrained
            self._apply_aspect_ratio_to_rect(keep_center=True)
            constrained = self.crop_rect

        return constrained

    def _apply_aspect_ratio_to_rect(self, keep_center: bool = True):
        if not self.aspect_ratio or self.crop_rect.isEmpty() or not self.video_bounds.isValid():
            return

        rect = QRect(self.crop_rect)
        if keep_center:
            center = rect.center()
        else:
            center = self.crop_rect.center()

        # Calculate height based on width and aspect ratio
        w = max(rect.width(), self.min_size)
        h = int(round(w / self.aspect_ratio))

        if h > self.video_bounds.height():
            h = self.video_bounds.height()
            w = int(round(h * self.aspect_ratio))

        # Ensure not larger than bounds
        w = min(w, self.video_bounds.width())
        h = min(h, self.video_bounds.height())

        new_rect = QRect(0, 0, w, h)
        new_rect.moveCenter(center)

        if not self.video_bounds.contains(new_rect):
            new_rect = new_rect.intersected(self.video_bounds)
            if new_rect.isEmpty():
                new_rect = QRect(self.video_bounds)

        self.crop_rect = new_rect
        self.update_handles()
        self.update()

    # --------------------------------------------------
    # Handle Management and Mouse Events
    # Interactive resizing and dragging functionality
    # --------------------------------------------------
    def update_handles(self):
        rect = self.crop_rect
        if rect.isEmpty():
            return

        size = 12
        half = size // 2

        self.handles['top_left'].moveTopLeft(rect.topLeft() - QPoint(half, half))
        self.handles['top_right'].moveTopRight(rect.topRight() + QPoint(-half, -half))
        self.handles['bottom_left'].moveBottomLeft(rect.bottomLeft() + QPoint(-half, half))
        self.handles['bottom_right'].moveBottomRight(rect.bottomRight() + QPoint(half, half))
        self.handles['top'].moveCenter(QPoint(rect.center().x(), rect.top()))
        self.handles['bottom'].moveCenter(QPoint(rect.center().x(), rect.bottom()))
        self.handles['left'].moveCenter(QPoint(rect.left(), rect.center().y()))
        self.handles['right'].moveCenter(QPoint(rect.right(), rect.center().y()))

    def get_handle_at(self, pos: QPoint):
        for name, handle_rect in self.handles.items():
            if handle_rect.contains(pos):
                return name
        return None

    def get_cursor_for_handle(self, handle_name: str):
        cursors = {
            'top_left': Qt.SizeFDiagCursor,
            'bottom_right': Qt.SizeFDiagCursor,
            'top_right': Qt.SizeBDiagCursor,
            'bottom_left': Qt.SizeBDiagCursor,
            'top': Qt.SizeVerCursor,
            'bottom': Qt.SizeVerCursor,
            'left': Qt.SizeHorCursor,
            'right': Qt.SizeHorCursor,
        }
        return QCursor(cursors.get(handle_name, Qt.ArrowCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            self.resize_handle = self.get_handle_at(pos)

            if self.resize_handle or self.crop_rect.contains(pos):
                self.dragging = True
                self.drag_start_pos = pos
                self.drag_start_rect = QRect(self.crop_rect)
                if not self.resize_handle:
                    self.resize_handle = "move"

    def mouseMoveEvent(self, event):
        pos = event.pos()

        if self.dragging:
            dx = pos.x() - self.drag_start_pos.x()
            dy = pos.y() - self.drag_start_pos.y()

            if self.resize_handle == "move":
                new_rect = self.drag_start_rect.translated(dx, dy)
                self.crop_rect = self.constrain_to_bounds(new_rect)
            else:
                new_rect = QRect(self.drag_start_rect)

                if "left" in self.resize_handle:
                    new_rect.setLeft(new_rect.left() + dx)
                if "right" in self.resize_handle:
                    new_rect.setRight(new_rect.right() + dx)
                if "top" in self.resize_handle:
                    new_rect.setTop(new_rect.top() + dy)
                if "bottom" in self.resize_handle:
                    new_rect.setBottom(new_rect.bottom() + dy)

                new_rect = new_rect.normalized()

                # Minimum size
                if new_rect.width() < self.min_size:
                    if "left" in self.resize_handle:
                        new_rect.setLeft(new_rect.right() - self.min_size)
                    else:
                        new_rect.setRight(new_rect.left() + self.min_size)

                if new_rect.height() < self.min_size:
                    if "top" in self.resize_handle:
                        new_rect.setTop(new_rect.bottom() - self.min_size)
                    else:
                        new_rect.setBottom(new_rect.top() + self.min_size)

                # Maintain aspect ratio if fixed
                if self.aspect_ratio:
                    new_rect = self._adjust_resize_with_aspect_ratio(new_rect)

                self.crop_rect = self.constrain_to_bounds(new_rect)

            self.update_handles()
            self.crop_changed.emit(self.crop_rect)
            self.update()
        else:
            handle = self.get_handle_at(pos)
            if handle:
                self.setCursor(self.get_cursor_for_handle(handle))
            elif self.crop_rect.contains(pos):
                self.setCursor(QCursor(Qt.SizeAllCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))

    def _adjust_resize_with_aspect_ratio(self, rect: QRect) -> QRect:
        if not self.aspect_ratio:
            return rect

        r = QRect(rect)
        center = r.center()

        if "top" in self.resize_handle or "bottom" in self.resize_handle:
            h = max(r.height(), self.min_size)
            w = int(round(h * self.aspect_ratio))
        else:
            w = max(r.width(), self.min_size)
            h = int(round(w / self.aspect_ratio))

        w = min(w, self.video_bounds.width())
        h = min(h, self.video_bounds.height())

        r.setSize(QRect(0, 0, w, h).size())
        r.moveCenter(center)
        return r

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resize_handle = None

    # --------------------------------------------------
    # Painting and Display
    # Visual rendering of crop overlay and handles
    # --------------------------------------------------
    def paintEvent(self, event):
        if self.crop_rect.isEmpty():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dark area around crop
        path = QPainterPath()
        path.addRect(QRectF(self.rect()))
        path.addRect(QRectF(self.crop_rect))
        painter.fillPath(path, QBrush(QColor(0, 0, 0, 180)))

        # Main crop border
        painter.setPen(QPen(Qt.white, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.crop_rect)

        # Corner guides
        guide_length = 20
        painter.setPen(QPen(Qt.white, 2))

        painter.drawLine(self.crop_rect.topLeft(),
                         self.crop_rect.topLeft() + QPoint(guide_length, 0))
        painter.drawLine(self.crop_rect.topLeft(),
                         self.crop_rect.topLeft() + QPoint(0, guide_length))

        painter.drawLine(self.crop_rect.topRight(),
                         self.crop_rect.topRight() - QPoint(guide_length, 0))
        painter.drawLine(self.crop_rect.topRight(),
                         self.crop_rect.topRight() + QPoint(0, guide_length))

        painter.drawLine(self.crop_rect.bottomLeft(),
                         self.crop_rect.bottomLeft() + QPoint(guide_length, 0))
        painter.drawLine(self.crop_rect.bottomLeft(),
                         self.crop_rect.bottomLeft() - QPoint(0, guide_length))

        painter.drawLine(self.crop_rect.bottomRight(),
                         self.crop_rect.bottomRight() - QPoint(guide_length, 0))
        painter.drawLine(self.crop_rect.bottomRight(),
                         self.crop_rect.bottomRight() - QPoint(0, guide_length))

        # Resize handles
        handle_color = QColor(255, 255, 255, 220)
        painter.setPen(QPen(Qt.white, 1))
        painter.setBrush(QBrush(handle_color))
        for handle_rect in self.handles.values():
            painter.drawRect(handle_rect)

        # Display dimensions
        size_text = f"{self.crop_rect.width()} × {self.crop_rect.height()}"
        painter.setFont(self.font())

        text_rect = painter.boundingRect(self.crop_rect, Qt.AlignCenter, size_text)
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.setPen(Qt.NoPen)
        painter.drawRect(text_rect.adjusted(-5, -2, 5, 2))

        painter.setPen(QPen(Qt.white, 1))
        painter.drawText(self.crop_rect, Qt.AlignCenter, size_text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ensure_crop_within_bounds()