import os
import sys
from zipfile import ZipFile
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QFileDialog, QMessageBox, QScrollArea,
    QGroupBox, QFrame, QSizePolicy, QTextEdit
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QAction
from pyaxmlparser import APK

def resource_path(relative_path):
    """获取资源路径，兼容打包后的路径"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class APKInfoTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("APK 信息解析工具")
        self.setMinimumSize(QSize(900, 600))
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.init_ui()
        self.setAcceptDrops(True)

    def init_ui(self):
        # 主布局
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        # 左侧文件选择区域
        left_panel = self.create_left_panel()
        
        # 右侧信息展示区域
        right_panel = self.create_right_panel()
        
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)
        
        self.setCentralWidget(main_widget)

    def create_left_panel(self):
        """创建左侧文件选择面板"""
        layout = QVBoxLayout()
        
        # 拖放区域
        self.drop_area = QLabel("拖放APK文件到此区域\n或点击下方按钮选择文件")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 3px dashed #95a5a6;
                border-radius: 10px;
                color: #7f8c8d;
                font-size: 14px;
                padding: 10px;
                margin: 5px;
            }
        """)
        self.drop_area.setMinimumSize(370, 300)
        self.drop_area.setAcceptDrops(True)
        
        # 选择文件按钮
        btn_style = """
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                margin: 20px;
            }
            QPushButton:hover { background: #2980b9; }
        """
        self.btn_select = QPushButton("选择APK文件")
        self.btn_select.setStyleSheet(btn_style)
        self.btn_select.clicked.connect(self.select_file)
        
        layout.addWidget(self.drop_area)
        layout.addWidget(self.btn_select, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        return layout

    def create_right_panel(self):
        """创建右侧信息展示面板"""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        content_widget = QWidget()
        self.right_layout = QVBoxLayout(content_widget)
        
        # 基本信息组
        self.basic_group = self.create_info_group("基本信息", [
            ("包名", "package"),
            ("版本名称", "version"),
            ("版本代码", "version_code")
        ])
        
        # SDK信息组
        self.sdk_group = self.create_info_group("SDK信息", [
            ("最小SDK", "min_sdk"),
            ("目标SDK", "target_sdk")
        ])
        
        # 架构信息组
        self.arch_group = QGroupBox("支持的架构")
        self.arch_group.setLayout(QVBoxLayout())
        self.arch_content = QLabel("等待解析...")
        self.arch_content.setWordWrap(True)
        self.arch_content.setStyleSheet("color: #27ae60;")
        self.arch_group.layout().addWidget(self.arch_content)
        
        # 签名信息组（可复制版）
        self.signature_group = QGroupBox("签名信息")
        self.signature_group.setLayout(QVBoxLayout())

        # 使用可编辑文本框
        self.signature_content = QTextEdit()
        self.signature_content.setReadOnly(True)  # 只读模式
        self.signature_content.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # 禁用换行
        self.signature_content.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                color: #ff00ee;
                background-color: #555;
                border: 1px solid #dee2e6;
               border-radius: 4px;
               padding: 8px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        self.signature_content.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # 保持禁用自动换行
    
        # 添加右键菜单
        self.signature_content.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        copy_action = QAction("复制", self.signature_content)
        copy_action.triggered.connect(lambda: self.signature_content.copy())
        self.signature_content.addAction(copy_action)
    
        self.signature_group.layout().addWidget(self.signature_content)
        
        # 权限信息组（无滚动版）
        self.permission_group = QGroupBox("权限列表")
        self.permission_group.setStyleSheet("""
            QGroupBox {
                margin-top: 15px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)

        # 主布局配置
        self.permission_layout = QVBoxLayout()
        self.permission_layout.setContentsMargins(8, 8, 8, 8)
        self.permission_layout.setSpacing(5)

        # 内容容器
        self.permission_content = QWidget()
        self.permission_content.setLayout(self.permission_layout)

        # 将容器添加到分组
        self.permission_group.setLayout(QVBoxLayout())
        self.permission_group.layout().addWidget(self.permission_content)
        self.permission_group.layout().setContentsMargins(0, 0, 0, 0)

        # 设置尺寸策略
        self.permission_content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        # 添加到布局
        groups = [
            self.basic_group,
            self.sdk_group,
            self.arch_group,
            self.signature_group,
            self.permission_group
        ]
        for group in groups:
            self.right_layout.addWidget(group)
        
        self.scroll_area.setWidget(content_widget)
        
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.scroll_area)
        return right_layout

    def create_info_group(self, title, fields):
        """创建带字段的信息组"""
        group = QGroupBox(title)
        layout = QVBoxLayout()
        
        for field in fields:
            h_layout = QHBoxLayout()
            label = QLabel(f"{field[0]}:")
            label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            value = QLabel("未解析")
            value.setObjectName(field[1])
            value.setWordWrap(True)
            h_layout.addWidget(label)
            h_layout.addWidget(value, 1)
            layout.addLayout(h_layout)
            
            # 添加分割线
            if field != fields[-1]:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setStyleSheet("color: #ecf0f1;")
                layout.addWidget(line)
        
        group.setLayout(layout)
        return group

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        url = event.mimeData().urls()[0]
        file_path = url.toLocalFile()
        if file_path.lower().endswith(".apk"):
            self.process_apk(file_path)
        else:
            QMessageBox.warning(self, "错误", "请拖放有效的APK文件")

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择APK文件", "", "APK文件 (*.apk)"
        )
        if file_path:
            self.process_apk(file_path)

    def process_apk(self, file_path):
        """处理APK文件"""
        try:
            self.drop_area.setText(os.path.basename(file_path))
            self.drop_area.setStyleSheet("""
                QLabel {
                    border: 3px dashed #2ecc71;
                    color: #27ae60;
                }
            """)
            
            apk = APK(file_path)
            if not apk.is_valid_APK():
                raise ValueError("无效的APK文件")
            
            # 更新基本信息
            self.update_field("package", apk.get_package())
            self.update_field("version", apk.get_androidversion_name() or "未知")
            self.update_field("version_code", str(apk.get_androidversion_code() or "未知"))
            
            # 更新SDK信息
            self.update_field("min_sdk", apk.get_min_sdk_version() or "未知")
            self.update_field("target_sdk", apk.get_target_sdk_version() or "未知")
            
            # 更新架构信息
            arches = self.get_supported_architectures(file_path)
            self.arch_content.setText("\n".join([f"• {arch}" for arch in arches]) if arches else "未检测到原生库")
            
            # 更新签名信息（带换行格式）
            signature_data = apk.get_signature()
            if signature_data:
                try:
                    # 生成十六进制列表
                    hex_bytes = [f"{b:02x}" for b in signature_data]

                    # 按10个字节分组
                    grouped = []
                    for i in range(0, len(hex_bytes), 10):
                        group = hex_bytes[i:i+10]
                        grouped.append(" ".join(group))
                
                    # 转换为大写并添加换行
                    formatted_signature = "\n".join(grouped).upper()
                    self.signature_content.setPlainText(formatted_signature)
                
                except Exception as e:
                    self.signature_content.setPlainText(f"签名解析错误: {str(e)}")
            else:
                self.signature_content.setPlainText("未获取到签名信息")
            
            # 更新权限列表
            self.update_permissions(apk.get_permissions())
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"解析失败: {str(e)}")
            self.reset_ui()

    def add_copy_button(self):
        """添加浮动复制按钮"""
        btn_copy = QPushButton("复制全部", self.signature_content)
        btn_copy.setStyleSheet("""
            QPushButton {
                background: #8e44ad;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover { background: #9b59b6; }
        """)
        btn_copy.clicked.connect(self.copy_signature)
    
        # 将按钮定位在右上角
        btn_copy.move(self.signature_content.width() - 90, 5)

        # 窗口大小变化时自动调整按钮位置
        def update_position():
            btn_copy.move(self.signature_content.width() - 90, 5)
        self.signature_content.resizeEvent = lambda e: update_position()

    def copy_signature(self):
        """复制签名到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.signature_content.toPlainText())
        QMessageBox.information(self, "成功", "签名已复制到剪贴板", QMessageBox.StandardButton.Ok)

    def update_field(self, field_name, value):
        """更新字段值"""
        label = self.findChild(QLabel, field_name)
        if label:
            # 确保转换为字符串
            safe_value = str(value) if value is not None else "未知"
            label.setText(safe_value)
            label.setStyleSheet("color: #e67e22;" if safe_value == "未知" else "")

    def get_supported_architectures(self, apk_path):
        """获取支持的CPU架构"""
        arches = set()
        try:
            with ZipFile(apk_path, 'r') as z:
                for f in z.namelist():
                    if f.startswith('lib/'):
                        parts = f.split('/')
                        if len(parts) > 1 and parts[1] in [
                            'armeabi', 'armeabi-v7a', 
                            'arm64-v8a', 'x86', 
                            'x86_64', 'mips', 'mips64'
                        ]:
                            arches.add(parts[1])
        except Exception as e:
            print(f"Error reading APK: {str(e)}")
        return sorted(arches)

    def update_permissions(self, permissions):
        """更新权限列表（无滚动版）"""
        # 清空现有内容
        while self.permission_layout.count():
            item = self.permission_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
        if not permissions:
            label = QLabel("未检测到特殊权限")
            label.setStyleSheet("color: #95a5a6; padding: 10px;")
            self.permission_layout.addWidget(label)
        else:
            for perm in sorted(permissions):
                label = QLabel(f"• {perm}")
                label.setStyleSheet("""
                    QLabel {
                        color: #c0392b; 
                        margin: 3px 0;
                        padding: 2px 5px;
                        background: #f9f9f9;
                        border-radius: 3px;
                    }
                """)
                label.setWordWrap(True)
                self.permission_layout.addWidget(label)
    
        self.permission_layout.addStretch()

    def reset_ui(self):
        """重置界面状态"""
        self.drop_area.setText("拖放APK文件到此区域\n或点击下方按钮选择文件")
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 3px dashed #95a5a6;
                color: #7f8c8d;
            }
        """)
        for field in ["package", "version", "version_code", "min_sdk", "target_sdk"]:
            self.update_field(field, "")
        self.arch_content.setText("等待解析...")
        self.signature_content.setText("等待解析...")
        self.update_permissions([])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = APKInfoTool()
    window.show()
    sys.exit(app.exec())