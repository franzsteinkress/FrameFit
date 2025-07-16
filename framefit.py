# Copyright (c) 2025 Franz Steinkress
# Licensed under the MIT License - see LICENSE for details
#
# framefit.py
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QColorDialog, QFileDialog,
    QVBoxLayout, QHBoxLayout, QSpinBox, QGroupBox, QComboBox
)
from PyQt6.QtGui import QColor, QPixmap, QDragEnterEvent, QDropEvent, QImage, QIcon
from PyQt6.QtCore import Qt, QMimeData
from PIL import Image, ImageDraw, ImageFilter, ImageQt

INPUT_DIR = "input_images"
OUTPUT_DIR = "output_images"
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

class FrameFit(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FrameFit")
        self.setFixedSize(400, 660)
        self.setWindowIcon(QIcon("./resources/fs.ico"))
        self.setAcceptDrops(True)

        self.bg_color = QColor(255, 255, 255)
        self.mask_shape = "Rechteck"

        # Format Inputs
        self.width_input = QSpinBox()
        self.width_input.setRange(0, 1280)
        self.width_input.setValue(400)
        self.height_input = QSpinBox()
        self.height_input.setRange(0, 1280)
        self.height_input.setValue(400)

        # Kreis-Durchmesser Input
        self.circle_diameter_input = QSpinBox()
        self.circle_diameter_input.setRange(0, 1280)
        self.circle_diameter_input.setValue(400)

        # Position Inputs
        self.x_input = QSpinBox()
        self.x_input.setRange(-1280, 1280)
        self.x_input.setValue(0)
        self.y_input = QSpinBox()
        self.y_input.setRange(-1280, 1280)
        self.y_input.setValue(0)

        self.btn_color = QPushButton("Farbe wählen")
        self.btn_color.clicked.connect(self.choose_color)

        self.btn_select_images = QPushButton("Bilder auswählen")
        self.btn_select_images.clicked.connect(self.select_images)
        self.selected_images = []

        self.btn_generate = QPushButton("Bilder erzeugen")
        self.btn_generate.clicked.connect(self.generate_images)

        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["Rechteck", "Kreis"])
        self.shape_combo.currentTextChanged.connect(self.set_mask_shape)

        self.preview_label = QLabel("Vorschau")
        self.preview_label.setFixedSize(300, 300)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid gray;")

        # Layout
        layout = QVBoxLayout()
        preview_container = QHBoxLayout()
        preview_container.addStretch()
        preview_container.addWidget(self.preview_label)
        preview_container.addStretch()
        layout.addLayout(preview_container)

        format_box = QGroupBox("Bildformat")
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Breite:"))
        format_layout.addWidget(self.width_input)
        format_layout.addWidget(QLabel("Höhe:"))
        format_layout.addWidget(self.height_input)
        format_box.setLayout(format_layout)

        position_box = QGroupBox("Position im Bild")
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("X:"))
        position_layout.addWidget(self.x_input)
        position_layout.addWidget(QLabel("Y:"))
        position_layout.addWidget(self.y_input)
        position_box.setLayout(position_layout)

        circle_box = QGroupBox("Kreis-Maske (optional)")
        circle_layout = QHBoxLayout()
        circle_layout.addWidget(QLabel("Durchmesser:"))
        circle_layout.addWidget(self.circle_diameter_input)
        circle_box.setLayout(circle_layout)

        layout.addWidget(format_box)
        layout.addWidget(position_box)
        layout.addWidget(QLabel("Formmaske:"))
        layout.addWidget(self.shape_combo)
        layout.addWidget(circle_box)
        layout.addWidget(self.btn_color)
        layout.addWidget(self.btn_select_images)
        layout.addWidget(self.btn_generate)

        self.setLayout(layout)

    def choose_color(self):
        color = QColorDialog.getColor(initial=self.bg_color, title="Hintergrundfarbe wählen")
        if color.isValid():
            self.bg_color = color
            self.btn_color.setStyleSheet(f"background-color: {color.name()};")

    def select_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Bildvorlagen auswählen", INPUT_DIR,
                                                "Bilder (*.png *.jpg *.jpeg)")
        self.selected_images = files
        if files:
            self.update_preview(files[0])

    def set_mask_shape(self, shape):
        self.mask_shape = shape
        if self.selected_images:
            self.update_preview(self.selected_images[0])

    def generate_images(self):
        r, g, b = self.bg_color.red(), self.bg_color.green(), self.bg_color.blue()
        a = 255
        width = self.width_input.value()
        height = self.height_input.value()
        dx = self.x_input.value()
        dy = self.y_input.value()
        diameter = self.circle_diameter_input.value()

        count = 0
        first_output = None

        for path in self.selected_images:
            try:
                img = Image.open(path).convert("RGBA")
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                new_img = Image.new("RGBA", (width, height), (r, g, b, a))

                x = (width - img.width) // 2 + dx
                y = (height - img.height) // 2 + dy
                new_img.paste(img, (x, y), img)

                if self.mask_shape == "Kreis":
                    mask = Image.new("L", (width, height), 0)
                    draw = ImageDraw.Draw(mask)
                    cx = (width - diameter) // 2
                    cy = (height - diameter) // 2
                    draw.ellipse((cx, cy, cx + diameter, cy + diameter), fill=255)
                    mask = mask.filter(ImageFilter.GaussianBlur(2.5))
                    new_img.putalpha(mask)

                filename = os.path.basename(path)
                out_path = os.path.join(OUTPUT_DIR, filename)
                new_img.save(out_path)
                if count == 0:
                    first_output = new_img.copy()
                count += 1
            except Exception as e:
                print(f"Fehler bei {path}: {e}")

        if first_output:
            self.show_preview_image(first_output)

        self.preview_label.setText(f"{count} Bild(er) gespeichert.")

    def update_preview(self, path):
        r, g, b = self.bg_color.red(), self.bg_color.green(), self.bg_color.blue()
        a = 255
        width = self.width_input.value()
        height = self.height_input.value()
        dx = self.x_input.value()
        dy = self.y_input.value()
        diameter = self.circle_diameter_input.value()

        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            new_img = Image.new("RGBA", (width, height), (r, g, b, a))
            x = (width - img.width) // 2 + dx
            y = (height - img.height) // 2 + dy
            new_img.paste(img, (x, y), img)

            if self.mask_shape == "Kreis":
                mask = Image.new("L", (width, height), 0)
                draw = ImageDraw.Draw(mask)
                cx = (width - diameter) // 2
                cy = (height - diameter) // 2
                draw.ellipse((cx, cy, cx + diameter, cy + diameter), fill=255)
                # mask = mask.filter(ImageFilter.GaussianBlur(0.5))   # hart
                mask = mask.filter(ImageFilter.GaussianBlur(2.5))   # weich
                new_img.putalpha(mask)

            self.show_preview_image(new_img)
        except Exception as e:
            self.preview_label.setText("Vorschaufehler")

    def show_preview_image(self, image):
        qt_img = ImageQt.ImageQt(image.convert("RGBA"))
        pixmap = QPixmap.fromImage(QImage(qt_img))
        pixmap = pixmap.scaled(self.preview_label.width(), self.preview_label.height(), Qt.AspectRatioMode.KeepAspectRatio)
        self.preview_label.setPixmap(pixmap)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg'))]
        if paths:
            self.selected_images = paths
            self.update_preview(paths[0])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FrameFit()
    window.show()
    sys.exit(app.exec())
