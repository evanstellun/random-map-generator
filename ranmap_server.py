import socket
import threading
import json
import base64
import io
import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ranmap import mapMapGenerator
import matplotlib.pyplot as plt

class RandomMapServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.current_image_data = None
        
    def generate_map_image(self):
        """生成地图并返回base64编码的图像数据"""
        try:
            print(f"[{datetime.now()}] 开始生成地图...")
            
            # 设置随机数种子以确保每次生成不同的地图
            import random
            import time
            import numpy as np
            random.seed(time.time())
            np.random.seed(int(time.time() * 1000) % 2**32)
            
            # 使用非GUI后端避免线程问题
            import matplotlib
            matplotlib.use('Agg')  # 使用非交互式后端
            import matplotlib.pyplot as plt
            
            # 重新导入ranmap模块以确保使用正确的后端
            from ranmap import mapMapGenerator
            
            generator = mapMapGenerator(width=100, height=100, num_points=80)
            fig, ax, main_points, small_terrain_list = generator.generate_map()
            
            # 彻底清除所有标题和文本
            ax.set_title('')
            plt.title('')
            fig.suptitle('')
            
            # 强制清除所有可能的文本元素（更保守的方法）
            try:
                # 只清除文本对象，不删除其他必要的子元素
                for txt in ax.texts[:]:
                    txt.remove()
                for txt in fig.texts[:]:
                    txt.remove()
                # 不清除艺术家对象和子元素，避免破坏图形结构
            except Exception as text_remove_error:
                print(f"清除文本时出错: {text_remove_error}")
            
            # 在保存之前再次清除标题
            ax.set_title('')
            plt.title('')
            fig.suptitle('')
            
            # 将图像保存到内存
            buffer = io.BytesIO()
            fig.savefig(buffer, format='PNG', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            
            # 在保存后彻底清除所有标题和文本（防止savefig添加标题）
            ax.set_title('')
            plt.title('')
            fig.suptitle('')
            
            # 再次强制清除所有可能的文本元素（更保守的方法）
            try:
                # 只清除文本对象，不删除其他必要的子元素
                for txt in ax.texts[:]:
                    txt.remove()
                for txt in fig.texts[:]:
                    txt.remove()
                # 不清除艺术家对象和子元素，避免破坏图形结构
            except Exception as text_remove_error:
                print(f"保存后清除文本时出错: {text_remove_error}")
            
            # 最后一次清除标题
            ax.set_title('')
            plt.title('')
            fig.suptitle('')
            
            # 转换为base64
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # 清理
            plt.close(fig)
            buffer.close()
            
            print(f"[{datetime.now()}] 地图生成完成")
            return image_data
            
        except Exception as e:
            print(f"[{datetime.now()}] 生成地图时出错: {e}")
            return None
    
    def handle_client(self, client_socket):
        """处理客户端请求"""
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                try:
                    request = json.loads(data)
                    command = request.get('command')
                    
                    if command == 'generate':
                        print(f"[{datetime.now()}] 收到重新生成请求")
                        image_data = self.generate_map_image()
                        
                        if image_data:
                            response = {
                                'status': 'success',
                                'image': image_data,
                                'message': '地图已生成'
                            }
                        else:
                            response = {
                                'status': 'error',
                                'message': '生成地图失败'
                            }
                    
                    elif command == 'get_image':
                        if self.current_image_data is None:
                            self.current_image_data = self.generate_map_image()
                        
                        if self.current_image_data:
                            response = {
                                'status': 'success',
                                'image': self.current_image_data,
                                'message': '当前地图'
                            }
                        else:
                            response = {
                                'status': 'error',
                                'message': '无法获取地图'
                            }
                    
                    elif command == 'save_image':
                        filename = request.get('filename', 'terrain_map.png')
                        if self.current_image_data:
                            try:
                                image_bytes = base64.b64decode(self.current_image_data)
                                with open(filename, 'wb') as f:
                                    f.write(image_bytes)
                                response = {
                                    'status': 'success',
                                    'message': f'图片已保存为: {filename}'
                                }
                            except Exception as e:
                                response = {
                                    'status': 'error',
                                    'message': f'保存失败: {e}'
                                }
                        else:
                            response = {
                                'status': 'error',
                                'message': '没有可保存的图片'
                            }
                    
                    elif command == 'stop_server':
                        print(f"[{datetime.now()}] 收到停止服务器请求")
                        response = {
                            'status': 'success',
                            'message': '服务器正在停止'
                        }
                        # 在新线程中延迟停止服务器，确保响应能发送给客户端
                        import threading
                        def delayed_stop():
                            import time
                            time.sleep(0.5)  # 等待响应发送
                            self.stop()
                            print(f"[{datetime.now()}] 服务器已停止")
                            sys.exit(0)
                        
                        stop_thread = threading.Thread(target=delayed_stop)
                        stop_thread.daemon = True
                        stop_thread.start()
                    
                    else:
                        response = {
                            'status': 'error',
                            'message': '未知命令'
                        }
                    
                    # 发送响应
                    response_json = json.dumps(response)
                    client_socket.send(response_json.encode('utf-8'))
                    
                except json.JSONDecodeError:
                    response = {
                        'status': 'error',
                        'message': '无效的JSON格式'
                    }
                    client_socket.send(json.dumps(response).encode('utf-8'))
                    
        except Exception as e:
            print(f"[{datetime.now()}] 客户端处理错误: {e}")
        finally:
            client_socket.close()
    
    def start(self):
        """启动服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            print(f"[{datetime.now()}] 服务器启动在 {self.host}:{self.port}")
            
            # 预生成第一张地图
            self.current_image_data = self.generate_map_image()
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"[{datetime.now()}] 客户端连接: {address}")
                    
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        print(f"[{datetime.now()}] 套接字错误: {e}")
                    break
                    
        except Exception as e:
            print(f"[{datetime.now()}] 服务器启动失败: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def stop(self):
        """停止服务器"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print(f"[{datetime.now()}] 服务器已停止")

if __name__ == '__main__':
    server = RandomMapServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        server.stop()