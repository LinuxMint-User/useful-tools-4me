import os
import sys
import hashlib
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QLineEdit, QFileDialog, QComboBox, QMessageBox,
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon  # 导入 QIcon


def resource_path(relative_path):
    """获取资源路径，兼容打包后的路径"""
    if getattr(sys, 'frozen', False):  # 判断是否为打包后的可执行文件
        base_path = sys._MEIPASS  # 打包后资源文件的临时路径
    else:
        base_path = os.path.dirname(__file__)  # 开发环境下的脚本路径
    return os.path.join(base_path, relative_path)


class FileChecksumTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件校验值比较工具")
        self.setGeometry(100, 100, 800, 400)

        # 设置窗口图标
        self.setWindowIcon(QIcon(resource_path("icon.ico")))  # 使用 resource_path 函数

        self.init_ui()

    def init_ui(self):
        # 主布局
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # 左侧布局：文件选择
        self.file_label = QLabel("拖入文件或点击选择文件")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setFrameShape(QFrame.Shape.Box)
        self.file_label.setFrameShadow(QFrame.Shadow.Sunken)
        self.file_label.setLineWidth(2)
        self.file_label.setAcceptDrops(True)
        self.file_label.setStyleSheet("QLabel { border: 2px dashed #8f8f8f; }")
        self.file_label.setFixedSize(300, 200)
        self.file_label.installEventFilter(self)

        self.select_file_button = QPushButton("选择文件")
        self.select_file_button.clicked.connect(self.select_file)

        left_layout.addWidget(self.file_label)
        left_layout.addWidget(self.select_file_button)

        # 右侧布局：校验值输入和校验
        self.checksum_label = QLabel("输入校验值或选择校验文件")
        self.checksum_input = QLineEdit()
        self.checksum_input.setPlaceholderText("输入校验值或选择校验文件")
        self.checksum_input.textChanged.connect(self.clear_result)  # 输入校验值时清除结果

        self.checksum_file_button = QPushButton("选择校验文件")
        self.checksum_file_button.clicked.connect(self.select_checksum_file)

        self.checksum_type_combo = QComboBox()
        self.checksum_type_combo.addItems(["自动检测", "MD5", "SHA1", "SHA256"])

        self.check_button = QPushButton("校验")
        self.check_button.clicked.connect(self.perform_check)

        self.result_label = QLabel("校验结果：")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout.addWidget(self.checksum_label)
        right_layout.addWidget(self.checksum_input)
        right_layout.addWidget(self.checksum_file_button)
        right_layout.addWidget(self.checksum_type_combo)
        right_layout.addWidget(self.check_button)
        right_layout.addWidget(self.result_label)

        # 拖拽区域
        self.file_label.setAcceptDrops(True)
        self.file_label.dragEnterEvent = self.drag_enter_event
        self.file_label.dropEvent = self.drop_event

        # 主窗口布局
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if file_path:
            self.file_path = file_path
            self.file_label.setText(os.path.basename(file_path))  # 只显示文件名
            self.clear_result()  # 选择文件后清除结果

    def select_checksum_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择校验文件")
        if file_path:
            try:
                with open(file_path, "r") as f:
                    checksum = f.read().strip()
                    if not checksum:
                        raise ValueError("校验文件内容为空")
                    # 检查校验值格式是否合法
                    if len(checksum) not in [32, 40, 64]:
                        raise ValueError("校验文件内容格式不正确")
                    self.checksum_input.setText(checksum)
                    self.clear_result()  # 选择校验文件后清除结果
            except Exception as e:
                QMessageBox.critical(self, "错误", f"校验文件无效：{e}")

    def drag_enter_event(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def drop_event(self, event):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.file_path = file_path
        self.file_label.setText(os.path.basename(file_path))  # 只显示文件名
        self.clear_result()  # 拖拽文件后清除结果

    def calculate_checksum(self, file_path, checksum_type):
        hash_func = {
            "MD5": hashlib.md5(),
            "SHA1": hashlib.sha1(),
            "SHA256": hashlib.sha256()
        }.get(checksum_type)

        if not hash_func:
            return None

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"计算校验值时出错：{e}")
            return None

    def perform_check(self):
        try:
            file_path = getattr(self, "file_path", None)
            if not file_path:
                QMessageBox.warning(self, "警告", "请先选择文件！")
                return

            checksum_type = self.checksum_type_combo.currentText()
            checksum_input = self.checksum_input.text().strip()

            if checksum_type == "自动检测":
                # 尝试自动检测校验值类型
                checksum_type = self.detect_checksum_type(checksum_input)
                if not checksum_type:
                    QMessageBox.warning(self, "警告", "无法自动检测校验值类型！")
                    return

            calculated_checksum = self.calculate_checksum(file_path, checksum_type)
            if calculated_checksum is None:
                return

            if calculated_checksum.lower() == checksum_input.lower():
                self.result_label.setText("校验结果：成功")
                self.result_label.setStyleSheet("color: green")
            else:
                self.result_label.setText("校验结果：失败")
                self.result_label.setStyleSheet("color: red")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"校验时出错：{e}")

    def detect_checksum_type(self, checksum):
        length = len(checksum)
        if length == 32:
            return "MD5"
        elif length == 40:
            return "SHA1"
        elif length == 64:
            return "SHA256"
        return None

    def clear_result(self):
        # 清除校验结果
        self.result_label.setText("校验结果：")
        self.result_label.setStyleSheet("")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileChecksumTool()
    window.show()
    sys.exit(app.exec())