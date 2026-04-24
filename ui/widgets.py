"""
widgets.py
----------
Shared custom widgets and effects for the UI layer.
"""

from PyQt6.QtCore import QEasingCurve, QElapsedTimer, QEvent, QPoint, QPointF, QRect, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


def apply_surface_shadow(widget: QWidget, blur: float = 20.0, offset_y: float = 4.0):
    """Apply a soft shadow to elevated surfaces on top of the far background."""

    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset_y)
    shadow.setColor(QColor(10, 10, 10, 90))
    widget.setGraphicsEffect(shadow)


class ConsistentComboBox(QComboBox):
    """A flat-painted combo box that avoids native highlight artifacts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrame(False)
        self.setMouseTracking(True)
        self._hover_locked = False
        self._swallow_release = False
        self._popup_event_filter_installed = False
        self._popup = _ComboPopup(self)
        self._popup.item_chosen.connect(self._apply_popup_index)

    def showPopup(self):
        self._hover_locked = False
        self._popup.populate_from_combo(self)
        popup_width = max(self.width(), self._popup.sizeHint().width())
        popup_height = self._popup.preferred_height()
        self._popup.setFixedSize(popup_width, popup_height)
        self._popup.move(self.mapToGlobal(QPoint(0, self.height() + 6)))
        self._install_popup_event_filter()
        self._popup.show()
        self._popup.raise_()
        self.update()

    def hidePopup(self):
        self._popup.hide()
        self._remove_popup_event_filter()
        self._hover_locked = True
        self.update()

    def _install_popup_event_filter(self):
        if self._popup_event_filter_installed:
            return
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
            self._popup_event_filter_installed = True

    def _remove_popup_event_filter(self):
        if not self._popup_event_filter_installed:
            return
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        self._popup_event_filter_installed = False

    def _global_combo_rect(self) -> QRect:
        top_left = self.mapToGlobal(self.rect().topLeft())
        return QRect(top_left, self.rect().size())

    def eventFilter(self, watched, event):
        if not self._popup.isVisible():
            return super().eventFilter(watched, event)

        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            if self._global_combo_rect().contains(global_pos):
                self._swallow_release = True
                self.hidePopup()
                event.accept()
                return True

        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            if self._swallow_release:
                self._swallow_release = False
                event.accept()
                return True

        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.rect().contains(event.position().toPoint()):
                self.setFocus(Qt.FocusReason.MouseFocusReason)
                if self._popup.isVisible():
                    self._swallow_release = True
                    self.hidePopup()
                else:
                    self.showPopup()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._swallow_release:
                self._swallow_release = False
                event.accept()
                return
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        if not self._popup.isVisible() and not self._hover_locked:
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_locked = False
        self.update()
        super().leaveEvent(event)

    def wheelEvent(self, event):
        event.ignore()

    def paintEvent(self, event):
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(0, 0, -1, -1)
        radius = 10.0
        is_popup_open = self._popup.isVisible()
        is_hover = self.underMouse() and not self._hover_locked and not is_popup_open
        is_active = is_popup_open or self.hasFocus() or is_hover

        border = QColor("#2c2c2c")
        if not self.isEnabled():
            background = QColor("#262626")
            text = QColor("#7e7d75")
            arrow = QColor("#7e7d75")
        elif is_active:
            background = QColor("#313131")
            text = QColor("#f8f8f6")
            arrow = QColor("#f8f8f6")
        else:
            background = QColor("#262626")
            text = QColor("#bfbeb3")
            arrow = QColor("#bfbeb3")

        painter.setPen(QPen(border, 1))
        painter.setBrush(background)
        painter.drawRoundedRect(rect, radius, radius)

        text_rect = rect.adjusted(14, 0, -34, 0)
        painter.setPen(text)
        painter.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            self.currentText(),
        )

        cx = rect.right() - 16
        cy = rect.center().y()
        arrow_points = QPolygonF(
            [
                QPointF(cx - 4, cy - 2),
                QPointF(cx + 4, cy - 2),
                QPointF(cx, cy + 3),
            ]
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(arrow)
        painter.drawPolygon(arrow_points)

    def _apply_popup_index(self, index: int):
        self.setCurrentIndex(index)
        self.hidePopup()


class _NoWheelSpinMixin:
    def wheelEvent(self, event):
        event.ignore()


class NoWheelSpinBox(_NoWheelSpinMixin, QSpinBox):
    pass


class NoWheelDoubleSpinBox(_NoWheelSpinMixin, QDoubleSpinBox):
    pass


class _ComboPopup(QFrame):
    item_chosen = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("comboPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self._list = QListWidget()
        self._list.setObjectName("comboListWidget")
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self._list.setSpacing(0)
        self._list.viewport().setObjectName("comboListViewport")
        self._list.setAutoFillBackground(False)
        self._list.viewport().setAutoFillBackground(False)
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)

    def populate_from_combo(self, combo: QComboBox):
        self._list.clear()
        for idx in range(combo.count()):
            item = QListWidgetItem(combo.itemText(idx))
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self._list.addItem(item)

        current_row = max(0, combo.currentIndex())
        if self._list.count():
            self._list.setCurrentRow(current_row)

    def preferred_height(self) -> int:
        rows = min(self._list.count(), 8)
        row_height = self._list.sizeHintForRow(0) if self._list.count() else 32
        content_height = (row_height * rows) + max(0, rows - 1) * self._list.spacing()
        return content_height + 20

    def _on_item_clicked(self, item: QListWidgetItem):
        index = item.data(Qt.ItemDataRole.UserRole)
        self.item_chosen.emit(index)

    def hideEvent(self, event):
        parent = self.parentWidget()
        if isinstance(parent, ConsistentComboBox):
            parent._hover_locked = True
            parent.update()
        super().hideEvent(event)


class NavButton(QPushButton):
    """Sidebar button with a subtle animated indicator line."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(48)
        self.setMouseTracking(True)

        self._indicator_duration_ms = 180
        self._indicator_max_width = 52.0
        self._indicator_easing = QEasingCurve(QEasingCurve.Type.OutCubic)
        self._indicator_value = 0.0
        self._indicator_start = 0.0
        self._indicator_target = 0.0
        self._indicator_elapsed = QElapsedTimer()
        self._indicator_timer = QTimer(self)
        self._indicator_timer.setInterval(8)
        self._indicator_timer.timeout.connect(self._advance_indicator)

    def enterEvent(self, event):
        if not self.isChecked():
            self._animate_indicator(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.isChecked():
            self._animate_indicator(False)
        super().leaveEvent(event)

    def setChecked(self, checked: bool):
        changed = checked != self.isChecked()
        super().setChecked(checked)
        if changed:
            self._animate_indicator(checked or self.underMouse())
        self.update()

    def _animate_indicator(self, visible: bool):
        target = self._indicator_max_width if visible else 0.0
        if abs(target - self._indicator_value) < 0.01:
            self._indicator_value = target
            self.update()
            return

        self._indicator_start = self._indicator_value
        self._indicator_target = target
        self._indicator_elapsed.restart()
        if not self._indicator_timer.isActive():
            self._indicator_timer.start()

    def _advance_indicator(self):
        elapsed = self._indicator_elapsed.elapsed()
        progress = min(1.0, elapsed / self._indicator_duration_ms)
        eased = self._indicator_easing.valueForProgress(progress)
        self._indicator_value = self._indicator_start + (
            (self._indicator_target - self._indicator_start) * eased
        )
        self.update()

        if progress >= 1.0:
            self._indicator_value = self._indicator_target
            self._indicator_timer.stop()

    def paintEvent(self, event):
        del event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(0, 4, 0, -4)
        radius = 12.0

        if self.isChecked():
            background = QColor("#171716")
            text_color = QColor("#f8f8f6")
        elif self.underMouse():
            background = QColor("#313131")
            text_color = QColor("#f8f8f6")
        else:
            background = QColor("#1f1f1e")
            text_color = QColor("#bfbeb3")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(rect, radius, radius)

        indicator_width = self._indicator_value
        if self.isChecked() or indicator_width > 0.0:
            indicator_rect = QRectF(
                rect.left() + 14,
                rect.bottom() - 5,
                indicator_width,
                2.5,
            )
            painter.setBrush(QColor("#f8f8f6"))
            painter.drawRoundedRect(indicator_rect, 1.25, 1.25)

        painter.setPen(text_color)
        text_rect = rect.adjusted(18, 0, -18, 0)
        painter.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            self.text(),
        )
