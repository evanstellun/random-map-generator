import sys
import os
import json
import socket
import threading
import base64
import io
import subprocess
import psutil
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QMessageBox, QFileDialog,
                             QProgressDialog)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer

class MapClient(QThread):
    """地图客户端线程"""
    map_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, host='localhost', port=5000):
        super().__init__()
        self.host = host
        self.port = port
        self.command = None
        self.filename = None
        
    def set_command(self, command, filename=None):
        """设置命令"""
        self.command = command
        self.filename = filename
        
    def run(self):
        """执行命令"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(10)
            client.connect((self.host, self.port))
            
            # 构建请求
            request = {'command': self.command}
            if self.filename:
                request['filename'] = self.filename
                
            client.send(json.dumps(request).encode('utf-8'))
            
            # 接收响应
            response_data = b''
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                
                # 检查是否收到完整JSON
                try:
                    response = json.loads(response_data.decode('utf-8'))
                    break
                except json.JSONDecodeError:
                    continue
            
            client.close()
            
            if response.get('status') == 'success':
                if 'image' in response:
                    self.map_received.emit(response['image'])
                else:
                    self.map_received.emit(response['message'])
            else:
                self.error_occurred.emit(response.get('message', '未知错误'))
                
        except socket.timeout:
            self.error_occurred.emit('连接超时，请检查服务器是否运行')
        except ConnectionRefusedError:
            self.error_occurred.emit('无法连接到服务器，请确保服务器已启动')
        except Exception as e:
            self.error_occurred.emit(str(e))

class RandomMapGUI(QMainWindow):
    """随机地图GUI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.client = MapClient()
        self.client.map_received.connect(self.on_map_received)
        self.client.error_occurred.connect(self.on_error)
        
        self.progress_dialog = None
        self.init_ui()
        
        # 启动时自动加载第一张地图
        QTimer.singleShot(1000, self.load_initial_map)
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('随机地图生成器')
        self.setGeometry(100, 100, 800, 700)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        main_layout = QVBoxLayout()
        
        # 创建图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(600, 500)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                background-color: #f0f0f0;
            }
        """)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 创建按钮
        self.regenerate_btn = QPushButton('重新生成')
        self.regenerate_btn.setFixedSize(120, 40)
        self.regenerate_btn.clicked.connect(self.regenerate_map)
        
        self.save_btn = QPushButton('保存图片')
        self.save_btn.setFixedSize(120, 40)
        self.save_btn.clicked.connect(self.save_image)
        
        self.exit_btn = QPushButton('退出')
        self.exit_btn.setFixedSize(120, 40)
        self.exit_btn.clicked.connect(self.close)
        
        # 添加按钮到布局
        button_layout.addStretch()
        button_layout.addWidget(self.regenerate_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.exit_btn)
        button_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(self.image_label)
        main_layout.addLayout(button_layout)
        
        central_widget.setLayout(main_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
    def load_initial_map(self):
        """加载初始地图"""
        self.show_progress("正在加载初始地图...")
        self.client.set_command('get_image')
        self.client.start()
        
    def regenerate_map(self):
        """重新生成地图"""
        self.regenerate_btn.setEnabled(False)
        self.show_progress("正在重新生成地图...")
        
        self.client.set_command('generate')
        self.client.start()
        
    def save_image(self):
        """保存当前图片到maps文件夹，使用序号作为文件名"""
        import json
        import os
        
        # 确保maps文件夹存在
        maps_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maps')
        if not os.path.exists(maps_dir):
            os.makedirs(maps_dir)
        
        # JSON文件路径
        json_file = os.path.join(maps_dir, 'image_counter.json')
        
        # 读取当前序号
        current_number = 1
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    current_number = data.get('last_number', 1)
            except Exception as e:
                print(f"读取JSON文件失败: {e}")
                current_number = 1
        
        # 生成文件名
        filename = os.path.join(maps_dir, f"{current_number}.png")
        
        # 保存图片
        self.show_progress("正在保存图片...")
        self.client.set_command('save_image', filename)
        self.client.start()
        
        # 更新JSON文件中的序号
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({'last_number': current_number + 1}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"更新JSON文件失败: {e}")
            
    def show_progress(self, message):
        """显示进度对话框"""
        self.progress_dialog = QProgressDialog(self)
        self.progress_dialog.setWindowTitle("请稍候")
        self.progress_dialog.setLabelText(message)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setWindowModality(Qt.ApplicationModal)
        self.progress_dialog.setRange(0, 0)  # 无限进度条
        self.progress_dialog.show()
        
        # 3秒后自动关闭
        QTimer.singleShot(3000, self.close_progress)
        
    def close_progress(self):
        """关闭进度对话框"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
    def on_map_received(self, data):
        """收到地图数据的处理"""
        self.close_progress()
        
        try:
            # 检查是否是图片数据
            if data.startswith('iVBOR') or len(data) > 100:  # PNG base64 前缀
                image_data = base64.b64decode(data)
                image = QImage()
                image.loadFromData(image_data)
                
                # 调整图片大小以适应窗口
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                # 显示消息
                self.image_label.setText(data)
                
        except Exception as e:
            self.on_error(f"显示图片失败: {e}")
            
        self.regenerate_btn.setEnabled(True)
        
    def on_error(self, error_message):
        """处理错误"""
        self.close_progress()
        QMessageBox.critical(self, "错误", error_message)
        self.regenerate_btn.setEnabled(True)
        
    def closeEvent(self, event):
        """关闭事件"""
        # 直接停止服务器并清除缓存，不显示确认对话框
        self.stop_server_and_cleanup()
        event.accept()
    
    def stop_server_and_cleanup(self):
        """停止服务器并清除缓存文件"""
        try:
            # 1. 发送停止命令到服务器
            self.show_progress("正在停止服务器...")
            self.client.set_command('stop_server')
            self.client.start()
            
            # 等待一小段时间让服务器处理停止命令
            QTimer.singleShot(1000, self.cleanup_cache)
            
        except Exception as e:
            print(f"停止服务器时出错: {e}")
            # 即使发送停止命令失败，也继续清理缓存
            self.cleanup_cache()
    
    def cleanup_cache(self):
        """清除缓存文件"""
        try:
            import shutil
            
            # 清除__pycache__目录
            if os.path.exists('__pycache__'):
                shutil.rmtree('__pycache__', ignore_errors=True)
                print("已清除__pycache__目录")
            
            # 清除.pyc文件
            for file in os.listdir('.'):
                if file.endswith('.pyc'):
                    try:
                        os.remove(file)
                        print(f"已删除文件: {file}")
                    except:
                        pass
            
            # 清除日志文件
            log_files = ['server.log', 'error.log']
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        os.remove(log_file)
                        print(f"已删除日志文件: {log_file}")
                    except:
                        pass
            
            # 强制终止python ranmap_server.py进程
            self.kill_server_process()
            
            self.close_progress()
            print("缓存清理完成")
            
        except Exception as e:
            print(f"清理缓存时出错: {e}")
            self.close_progress()
    
    def kill_server_process(self):
        """强制终止服务器进程"""
        try:
            # 查找并终止python ranmap_server.py进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # 检查进程命令行是否包含ranmap_server.py
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and len(cmdline) > 1 and 'ranmap_server.py' in cmdline[-1]:
                            print(f"找到服务器进程 PID: {proc.info['pid']}")
                            proc.terminate()
                            print(f"已终止服务器进程 PID: {proc.info['pid']}")
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            print(f"终止服务器进程时出错: {e}")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    gui = RandomMapGUI()
    gui.show()
    
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())