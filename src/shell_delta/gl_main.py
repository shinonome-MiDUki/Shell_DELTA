import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel
    )
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QImage
from PySide6.QtOpenGL import QOpenGLTexture
from OpenGL import GL

class OpenGLImageWidget(QOpenGLWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.texture = None
        self.image_ratio = 1.0  # 画像の幅/高さ

    def initializeGL(self):
        GL.glClearColor(0.1, 0.1, 0.1, 1.0)
        GL.glEnable(GL.GL_TEXTURE_2D)

        image = QImage(self.image_path).mirrored()
        
        if not image.isNull():
            self.image_ratio = image.width() / image.height()
            
            self.texture = QOpenGLTexture(image)
            self.texture.setMinificationFilter(QOpenGLTexture.Filter.Linear)
            self.texture.setMagnificationFilter(QOpenGLTexture.Filter.Linear)

    def _load_texture(self, path):
        # 古いテクスチャが存在する場合は破棄してメモリ開放
        if self.texture:
            self.texture.destroy()
            self.texture = None

        image = QImage(path).mirrored()
        if not image.isNull():
            self.image_path = path
            self.image_ratio = image.width() / image.height()

            # 新しいテクスチャを作成
            self.texture = QOpenGLTexture(image)
            self.texture.setMinificationFilter(QOpenGLTexture.Filter.Linear)
            self.texture.setMagnificationFilter(QOpenGLTexture.Filter.Linear)

    def change_image(self, new_image_path):
        self.makeCurrent()
        self._load_texture(new_image_path)
        self.resizeGL(self.width(), self.height())
        self.doneCurrent()
        self.update()

    def resizeGL(self, w, h):
        GL.glViewport(0, 0, w, h)
        
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        
        widget_ratio = w / h if h != 0 else 1.0

        if widget_ratio > self.image_ratio:
            factor = widget_ratio / self.image_ratio
            GL.glOrtho(-factor, factor, -1.0, 1.0, -1.0, 1.0)
        else:
            factor = self.image_ratio / widget_ratio
            GL.glOrtho(-1.0, 1.0, -factor, factor, -1.0, 1.0)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

    def paintGL(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        if not self.texture:
            return

        self.texture.bind()

        # -1.0 〜 1.0 の正方形の矩形を描画（resizeGL の glOrtho 側で比率を吸収）
        GL.glBegin(GL.GL_QUADS)
        
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex2f(-1.0, -1.0)

        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex2f(1.0, -1.0)

        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex2f(1.0, 1.0)

        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex2f(-1.0, 1.0)

        GL.glEnd()

        self.texture.release()


class MainUserUi(QWidget):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        main_lo = QVBoxLayout()

        read_btn = QPushButton("Read Sequence")
        main_lo.addWidget(read_btn, 1)
        self.seq_idx = 0

        self.sequence_root_dir = Path("/Users/shiinaayame/Downloads")
        self.gl_widget = OpenGLImageWidget(str(self.sequence_root_dir / f"cut{self.seq_idx:03d}_prologue.png"))
        main_lo.addWidget(self.gl_widget, 6)

        btn_lo = QHBoxLayout()
        prev_btn = QPushButton("Previous")
        prev_btn.clicked.connect(lambda: self.move_sequence(is_foward=False))
        self.current_frame_label = QLabel("0")
        self.current_frame_label.setAlignment(Qt.AlignCenter) 
        next_btn = QPushButton("Next")
        next_btn.clicked.connect(lambda: self.move_sequence(is_foward=True))

        btn_lo.addWidget(prev_btn)
        btn_lo.addWidget(self.current_frame_label)
        btn_lo.addWidget(next_btn)
        main_lo.addLayout(btn_lo, 3) 

        self.setLayout(main_lo)

    def move_sequence(self, is_foward: bool):
        self.seq_idx += 1 if is_foward else -1
        new_image_path = self.sequence_root_dir / f"cut{self.seq_idx:03d}_prologue.png"
        if not new_image_path.exists():
            print("Not exist")
            self.seq_idx += -1 if is_foward else 1
            return
        self.current_frame_label.setText(str(self.seq_idx))
        self.gl_widget.change_image(
            new_image_path=str(self.sequence_root_dir / f"cut{self.seq_idx:03d}_prologue.png")
            )



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("PySide OpenGL Aspect Ratio Fixed")
    window.resize(800, 600)

    main_ui = MainUserUi()
    window.setCentralWidget(main_ui)

    window.show()
    sys.exit(app.exec())