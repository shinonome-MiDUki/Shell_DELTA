import time
from pathlib import Path

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

        # PNG 画像を読み込み
        image = QImage(self.image_path).mirrored()
        
        if not image.isNull():
            # 画像の縦横比を保存
            self.image_ratio = image.width() / image.height()
            
            self.texture = QOpenGLTexture(image)
            self.texture.setMinificationFilter(QOpenGLTexture.Filter.Linear)
            self.texture.setMagnificationFilter(QOpenGLTexture.Filter.Linear)

    def _load_texture(self, path):
        """画像ファイルを読み込み、QOpenGLTexture を生成する内部関数"""
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

    def change_image(self, 
                     new_image_path: str | Path,
                     target_time: float = 0.0
                     ) -> None:
        self.makeCurrent()
        self._load_texture(new_image_path)
        self.resizeGL(self.width(), self.height())
        self.doneCurrent()
        while (time.time() < target_time): ...
        self.update()


    def resizeGL(self, w, h):
        GL.glViewport(0, 0, w, h)
        
        # 投影行列を設定してアスペクト比を補正
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        
        widget_ratio = w / h if h != 0 else 1.0

        # ウィンドウと画像の縦横比を比較し、描画範囲 (glOrtho) を調整
        if widget_ratio > self.image_ratio:
            # ウィンドウの方が横長：左右に余白を作る
            factor = widget_ratio / self.image_ratio
            GL.glOrtho(-factor, factor, -1.0, 1.0, -1.0, 1.0)
        else:
            # ウィンドウの方が縦長：上下に余白を作る
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


