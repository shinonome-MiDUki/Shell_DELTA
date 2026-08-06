import sys
import re
import time
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QLineEdit
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

    def change_image(self, new_image_path):
        st = time.time()
        # OpenGL コンテキストをアクティブ化
        self.makeCurrent()

        # 新しい画像を読み込み
        self._load_texture(new_image_path)

        # 画像比率が変わった場合に備えて glOrtho 領域を更新
        self.resizeGL(self.width(), self.height())

        # コンテキストの割り当て解除
        self.doneCurrent()

        # 画面の再描画を要求 (paintGL が呼ばれる)
        self.update()
        print(time.time() - st)


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


class MainUserUi(QWidget):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sequence_root_dir = None
        self.mata_filename = None
        self.first_sequence_idx = 0
        self.frame_notation_len = 0
        self.inputting = False

        main_lo = QVBoxLayout()

        read_btn = QPushButton("Read Sequence")
        read_btn.clicked.connect(self.open_sequence)
        main_lo.addWidget(read_btn)
        self.seq_idx = 0
        self.frame_img_dict = {}

        labels_lo = QHBoxLayout()
        self.current_actual_img_idx_label = QLabel("----")
        self.current_actual_img_idx_label.setFixedWidth(50)
        self.current_actual_img_idx_label.setAlignment(Qt.AlignCenter) 
        self.current_actual_img_idx_label.setStyleSheet("border:2px solid #000000;")
        labels_lo.addWidget(self.current_actual_img_idx_label)
        self.current_opened_label = QLabel("Working Sequence : None")
        labels_lo.addWidget(self.current_opened_label)
        main_lo.addLayout(labels_lo)

        self.gl_widget = OpenGLImageWidget("")
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
        main_lo.addLayout(btn_lo, 2)

        video_lo = QHBoxLayout()
        play_btn = QPushButton("Play")
        play_btn.clicked.connect()
        video_lo.addWidget(play_btn)
        pause_btn = QPushButton("Pause")
        pause_btn.clicked.connect()
        video_lo.addWidget(pause_btn)
        render_btn = QPushButton("Render")
        video_lo.addWidget(render_btn)
        video_lo.addSpacing
        
        fps_input_lo = QHBoxLayout()
        fps_input_lo.addWidget(QLabel("FPS : "))
        fps_input_field = QLineEdit("24")

        main_lo.addLayout(video_lo, 1) 

        self.setLayout(main_lo)

    def _get_actual_img_idx(self) -> int:
        actual_img_idx = self.frame_img_dict.get(self.seq_idx, None)
        if actual_img_idx is not None:
            return actual_img_idx
        checking_idx = self.seq_idx - 1
        while actual_img_idx is None and checking_idx >= 0:
            actual_img_idx = self.frame_img_dict.get(checking_idx, None)
            checking_idx -= 1
        return actual_img_idx if actual_img_idx is not None else -1

    def move_sequence(self, is_foward: bool):
        if self.mata_filename is None:
            return
        self.inputting = False
        self.seq_idx += 1 if is_foward else -1
        actual_img_idx = self._get_actual_img_idx()
        actual_filename = self.mata_filename.replace(
            '#' * self.frame_notation_len, 
            f"{actual_img_idx:0{self.frame_notation_len}d}"
            )
        self.current_actual_img_idx_label.setText(str(actual_img_idx))
        new_image_path = self.sequence_root_dir / actual_filename
        if not new_image_path.exists():
            new_image_path = ""
        self.current_frame_label.setText(str(self.seq_idx))
        self.gl_widget.change_image(
            new_image_path=str(new_image_path)
            )

    def open_sequence(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Sequence", "", "PNG (*.png)")
        if not filename:
            return
        self.sequence_root_dir = Path(filename).resolve().parent
        matches = re.findall(r'\d+', filename)
        if len(matches) != 1:
            return
        self.gl_widget.change_image(new_image_path=filename)
        self.frame_notation_len = len(matches[0]) 
        self.first_sequence_idx = int(matches[0])   
        sharps = '#' * self.frame_notation_len       
        filename = re.sub(r'\d+', sharps, filename).split("/")[-1]
        self.mata_filename = filename
        self.seq_idx = self.first_sequence_idx
        self.current_opened_label.setText(
            f"Working Sequence : {self.sequence_root_dir / self.mata_filename}"
            )
        self.current_actual_img_idx_label.setText(str(self.seq_idx))
        self.current_frame_label.setText(str(self.first_sequence_idx))

        print(f"mfie : {self.mata_filename}")
        parts = [re.escape(p) for p in self.mata_filename.split(sharps)]
        print(f"parts : {parts}")
        regex_pattern = "^" + r"(\d+)".join(parts) + "$"
        print(regex_pattern)
        for item in self.sequence_root_dir.iterdir():
            print(item)
        print("**")
        numbers = [
            m.group(1)
            for item in self.sequence_root_dir.iterdir()
            if item.is_file() and (m := re.match(regex_pattern, item.name))
        ]
        print(numbers)
        for num in numbers:
            num = int(num)
            self.frame_img_dict[num] = num
        print(self.frame_img_dict)




    def keyPressEvent(self, event):
        _move_seq_keys = [
            Qt.Key.Key_Right,
            Qt.Key.Key_Left
        ]
        _num_keys = {
            Qt.Key.Key_0 : 0,
            Qt.Key.Key_1 : 1,
            Qt.Key.Key_2 : 2,
            Qt.Key.Key_3 : 3,
            Qt.Key.Key_4 : 4,
            Qt.Key.Key_5 : 5,
            Qt.Key.Key_6 : 6,
            Qt.Key.Key_7 : 7, 
            Qt.Key.Key_8 : 8,
            Qt.Key.Key_9 : 9
        }
        pressed = event.key()
        if pressed == Qt.Key.Key_Return:
            if not self.inputting: 
                return
            self.inputting = False
            self.frame_img_dict[self.seq_idx] = int(self.input_frame_num_str)
            actual_filename = self.mata_filename.replace(
                '#' * self.frame_notation_len, 
                f"{self.frame_img_dict[self.seq_idx]:0{self.frame_notation_len}d}"
                )
            designated_image_path = self.sequence_root_dir / actual_filename
            if not designated_image_path.exists():
                designated_image_path = ""
            self.input_frame_num_str = ""
            self.gl_widget.change_image(new_image_path=designated_image_path)
        elif pressed in _move_seq_keys:
            if pressed == Qt.Key.Key_Right:
                self.move_sequence(is_foward=True)
            elif pressed == Qt.Key.Key_Left:
                self.move_sequence(is_foward=False)
        elif pressed in _num_keys:
            if self.mata_filename is None:
                return
            if not self.inputting:
                self.inputting = True
                self.input_frame_num_str = ""
            self.input_frame_num_str += str(_num_keys[pressed])
            self.current_actual_img_idx_label.setText(self.input_frame_num_str)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("PySide OpenGL Aspect Ratio Fixed")
    window.resize(800, 600)

    main_ui = MainUserUi()
    window.setCentralWidget(main_ui)

    window.show()
    sys.exit(app.exec())