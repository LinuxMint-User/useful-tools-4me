import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
                             QFileDialog, QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QScrollArea, QDialogButtonBox
from PyQt5.QtGui import QIcon
from collections import defaultdict

# 在类定义中添加初始化变量
class DirectoryTreeGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("目录树生成器")
        self.setWindowIcon(QIcon(self.resource_path('icon.ico')))
        self.setGeometry(100, 100, 800, 600)
        self.selected_folders = set()  # 使用集合存储选中的文件夹
        self.current_dir_path = ""  # 添加当前目录路径变量
        self.init_ui()

    def resource_path(self, relative_path):
        """获取资源路径，兼容打包后的路径"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def init_ui(self):
        # 设置主窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #424242;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #424242;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #212121;
            }
            QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #424242;
                border-radius: 4px;
                font-family: 'Courier New';
                font-size: 14px;
            }
            QCheckBox {
                color: #E0E0E0;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:checked {
                background-color: #BB86FC;
            }
            QCheckBox::indicator:unchecked {
                background-color: #424242;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QDialog {
                background-color: #121212;
            }
            QMessageBox {
                background-color: #121212;
            }
            QMessageBox QLabel {
                color: #E0E0E0;
            }
            QMessageBox QPushButton {
                min-width: 80px;
            }
        """)

        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # 目录选择部分
        dir_layout = QHBoxLayout()
        main_layout.addLayout(dir_layout)
        
        self.dir_label = QLabel("目标目录:")
        dir_layout.addWidget(self.dir_label)
        
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("请选择或输入目录路径")
        dir_layout.addWidget(self.dir_input)
        
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.browse_button)
        
        # 选项部分
        options_layout = QHBoxLayout()
        main_layout.addLayout(options_layout)
        
        self.ignore_hidden_check = QCheckBox("忽略隐藏文件/文件夹")
        self.ignore_hidden_check.setChecked(True)
        options_layout.addWidget(self.ignore_hidden_check)
        
        self.show_files_check = QCheckBox("包含文件")
        self.show_files_check.setChecked(True)
        options_layout.addWidget(self.show_files_check)
        
        self.show_size_check = QCheckBox("显示文件大小")
        self.show_size_check.setChecked(False)
        options_layout.addWidget(self.show_size_check)

        # 连接信号槽并初始化状态
        self.show_files_check.stateChanged.connect(self.toggle_show_size_enabled)
        self.toggle_show_size_enabled(Qt.Checked)  # 手动触发一次以初始化状态

        # 新增: 展开控制按钮
        self.expand_control_button = QPushButton("选择展开的文件夹...")
        self.expand_control_button.clicked.connect(self.show_expand_dialog)
        options_layout.addWidget(self.expand_control_button)
        
        # 生成按钮
        self.generate_button = QPushButton("生成目录树")
        self.generate_button.clicked.connect(self.generate_tree)
        main_layout.addWidget(self.generate_button)
        
        # 结果展示
        self.result_label = QLabel("目录树结构:")
        main_layout.addWidget(self.result_label)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 14px;
            background-color: #1E1E1E;
            color: #E0E0E0;
            border: 1px solid #424242;
            border-radius: 4px;
        """)
        main_layout.addWidget(self.result_text)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        self.copy_button = QPushButton("复制到剪贴板")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(self.copy_button)
        
        self.save_button = QPushButton("保存到文件")
        self.save_button.clicked.connect(self.save_to_file)
        button_layout.addWidget(self.save_button)
        
        self.clear_button = QPushButton("清空")
        self.clear_button.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_button)
    
    def browse_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            self.dir_input.setText(dir_path)
    
    def toggle_show_size_enabled(self, state):
        """根据'包含文件'选项状态切换'显示文件大小'的可用状态"""
        self.show_size_check.setEnabled(state == Qt.Checked)
        if state != Qt.Checked:
            self.show_size_check.setChecked(False)

    def generate_tree(self):
        dir_path = self.dir_input.text().strip()
        if not dir_path:
            QMessageBox.warning(self, "警告", "请先选择或输入目录路径!")
            return
        
        if not os.path.isdir(dir_path):
            QMessageBox.warning(self, "警告", "指定的路径不是一个有效的目录!")
            return
        
        ignore_hidden = self.ignore_hidden_check.isChecked()
        show_files = self.show_files_check.isChecked()
        show_size = show_files and self.show_size_check.isChecked()  # 只有当包含文件时才考虑显示大小
        
        try:
            tree = self.build_directory_tree(
                dir_path, 
                ignore_hidden=ignore_hidden,
                show_files=show_files,
                show_size=show_size
            )
            self.result_text.setPlainText(tree)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成目录树时出错:\n{str(e)}")
    
    def show_expand_dialog(self):
        dir_path = self.dir_input.text().strip()
        if not dir_path or not os.path.isdir(dir_path):
            QMessageBox.warning(self, "警告", "请先选择有效的目录路径!")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("选择要展开的文件夹")
        dialog.resize(600, 500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #121212;
            }
            QLineEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #424242;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #424242;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QCheckBox {
                color: #E0E0E0;
                padding: 2px;
                background-color: #1E1E1E;
            }
            QScrollArea {
                background-color: #1E1E1E;
            }
            QWidget {
                background-color: #1E1E1E;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 搜索框部分
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索文件夹...")
        self.search_input.textChanged.connect(self.filter_folders)
        search_layout.addWidget(self.search_input)
        
        # 全选/全不选按钮
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_none_btn = QPushButton("全不选")
        select_all_btn.clicked.connect(lambda: self.toggle_all_checkboxes(True))
        select_none_btn.clicked.connect(lambda: self.toggle_all_checkboxes(False))
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(select_none_btn)
        
        search_layout.addLayout(button_layout)
        layout.addLayout(search_layout)
        
        # 滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(2)  # 减少复选框间距
        
        # 获取所有子目录并按层级排序
        self.folder_parents = {}
        self.folder_children = defaultdict(list)
        
        # 先收集所有文件夹并建立父子关系
        for root, dirs, _ in os.walk(dir_path):
            current_path = root
            for d in dirs:
                full_path = os.path.join(root, d)
                self.folder_parents[full_path] = current_path
                self.folder_children[current_path].append(full_path)
        
        # 修改这里 - 将folder_checkboxes改为存储所有复选框的列表
        self.folder_checkboxes_list = []  # 新增列表存储所有复选框
        self.folder_checkboxes = {}  # 保留字典用于快速查找
        
        def add_folder_to_layout(path, level):
            if path != dir_path:
                d = os.path.basename(path)
                cb = QCheckBox("    " * (level-1) + "📁 " + d)
                cb.setChecked(path in self.selected_folders)
                cb.full_path = path
                cb.level = level
                cb.stateChanged.connect(lambda state, cb=cb: self.on_folder_toggled(cb))
                self.folder_checkboxes[path] = cb
                self.folder_checkboxes_list.append(cb)  # 添加到列表
                self.content_layout.addWidget(cb)
            
            for child in sorted(self.folder_children.get(path, [])):
                add_folder_to_layout(child, level+1)
        
        add_folder_to_layout(dir_path, 0)
        
        self.content = QWidget()
        self.content.setLayout(self.content_layout)
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)
        
        # 确定/取消按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            self.selected_folders = {cb.full_path for cb in self.folder_checkboxes_list if cb.isChecked()}

    def filter_folders(self):
        """根据搜索文本过滤文件夹"""
        search_text = self.search_input.text().lower()
        for cb in self.folder_checkboxes_list:  # 改为使用列表
            cb.setVisible(search_text in cb.text().lower())

    def toggle_all_checkboxes(self, checked):
        """切换所有可见复选框状态"""
        for cb in self.folder_checkboxes_list:  # 改为使用列表
            if cb.isVisible():
                cb.setChecked(checked)

    def on_folder_toggled(self, checkbox):
        """当文件夹被选中/取消选中时的处理"""
        if checkbox.isChecked():
            current_path = self.folder_parents.get(checkbox.full_path)
            while current_path and current_path in self.folder_checkboxes:  # 字典用于快速查找
                self.folder_checkboxes[current_path].setChecked(True)
                current_path = self.folder_parents.get(current_path)
        else:
            queue = [checkbox.full_path]
            while queue:
                current_path = queue.pop(0)
                for child in self.folder_children.get(current_path, []):
                    if child in self.folder_checkboxes:  # 字典用于快速查找
                        self.folder_checkboxes[child].setChecked(False)
                        queue.append(child)

    def build_directory_tree(self, path, prefix="", ignore_hidden=True, show_files=True, show_size=False):
        """递归构建目录树"""
        if ignore_hidden and os.path.basename(path).startswith('.'):
            return ""
        
        name = os.path.basename(path)
        if not prefix:  # 根目录
            tree = f"{name}/\n"
        else:
            tree = ""  # 非根目录不重复显示名称
        
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            return tree + f"{prefix}  [权限被拒绝]\n"
        
        files = []
        dirs = []
        
        for entry in entries:
            full_path = os.path.join(path, entry)
            if ignore_hidden and entry.startswith('.'):
                continue
            if os.path.isdir(full_path):
                dirs.append(entry)
            elif show_files:
                files.append(entry)
        
        # 处理子目录
        for i, entry in enumerate(dirs):
            full_path = os.path.join(path, entry)
            if hasattr(self, 'selected_folders') and full_path not in self.selected_folders:
                # 如果文件夹不在选中列表中，只显示名称不展开
                if i == len(dirs) - 1 and not files:
                    tree += f"{prefix}└── {entry}/\n"
                else:
                    tree += f"{prefix}├── {entry}/\n"
                continue
            
            # 计算正确的缩进前缀
            if i == len(dirs) - 1 and not files:
                connector = "└── "
                new_prefix = prefix + "    "
            else:
                connector = "├── "
                new_prefix = prefix + "│   "
            
            # 添加当前目录连接线
            tree += f"{prefix}{connector}{entry}/\n"
            
            # 递归构建子树
            subtree = self.build_directory_tree(
                full_path, new_prefix, ignore_hidden, show_files, show_size
            )
            tree += subtree
        
        # 处理文件
        for i, entry in enumerate(files):
            full_path = os.path.join(path, entry)
            if i == len(files) - 1 and (i > 0 or len(dirs) > 0):
                tree += f"{prefix}└── {entry}"
            else:
                tree += f"{prefix}├── {entry}"
            
            if show_size:
                try:
                    size = os.path.getsize(full_path)
                    tree += f" ({self.format_size(size)})"
                except OSError:
                    tree += " (无法获取大小)"
            
            tree += "\n"
        
        return tree
    
    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def copy_to_clipboard(self):
        text = self.result_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "成功", "目录树已复制到剪贴板!")
        else:
            QMessageBox.warning(self, "警告", "没有内容可复制!")
    
    def save_to_file(self):
        text = self.result_text.toPlainText()
        if not text:
            QMessageBox.warning(self, "警告", "没有内容可保存!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "成功", "目录树已保存到文件!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件时出错:\n{str(e)}")
    
    def clear_results(self):
        self.result_text.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DirectoryTreeGenerator()
    window.show()
    sys.exit(app.exec_())