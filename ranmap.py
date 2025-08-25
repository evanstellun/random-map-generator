import numpy as np
import matplotlib.pyplot as plt
import random
from matplotlib.patches import Polygon
from scipy.interpolate import splprep, splev
from matplotlib.path import Path
from matplotlib.widgets import Button
import matplotlib.patches as patches
from scipy.ndimage import gaussian_filter

# 全局matplotlib设置，禁用自动标题生成
plt.rcParams['axes.titlesize'] = 0  # 标题字体大小设为0
plt.rcParams['figure.titlesize'] = 0  # 图形标题大小设为0
plt.rcParams['axes.titlepad'] = 0  # 标题填充设为0

def generate_complex_map(width=100, height=100, num_points=80):
    """
    生成复杂的随机地形形状，创建曲折丰富的海岸线
    
    参数:
        width: 地图宽度
        height: 地图高度
        num_points: 岛屿边界点数
    
    返回:
        map_points: 岛屿边界点坐标列表
    """
    # 生成随机中心点
    center_x = width // 2 + random.randint(-width//4, width//4)
    center_y = height // 2 + random.randint(-height//4, height//4)
    
    # 生成随机基础半径
    base_radius = min(width, height) // 4
    
    # 增加基础点数量以创建更复杂的形状
    angles = np.linspace(0, 2*np.pi, num_points//3, endpoint=False)
    
    # 为每个角度生成多层随机半径，创建更丰富的变化
    radii = []
    for i, angle in enumerate(angles):
        # 大尺度变化：创建主要的半岛和海湾（减少变化范围）
        macro_variation = random.uniform(0.7, 1.5)
        
        # 中尺度变化：增加中等大小的起伏（增加变化范围）
        medium_variation = random.uniform(0.5, 1.8)
        
        # 小尺度变化：添加细节和纹理（增加变化范围）
        fine_variation = random.uniform(0.6, 1.6)
        
        # 微尺度变化：创建非常精细的细节
        micro_variation = random.uniform(0.85, 1.2)
        
        # 添加位置相关的变化，使不同区域有不同的特征
        position_factor = i / len(angles)
        regional_variation = 1.0 + 0.4 * np.sin(position_factor * 3 * np.pi) * np.cos(position_factor * 5 * np.pi)
        
        # 组合所有变化层次
        radius = base_radius * macro_variation * medium_variation * fine_variation * micro_variation * regional_variation
        radii.append(radius)
    
    # 计算基础边界点坐标
    base_points = []
    for i, angle in enumerate(angles):
        x = center_x + radii[i] * np.cos(angle)
        y = center_y + radii[i] * np.sin(angle)
        base_points.append([x, y])
    
    # 添加第一个点以闭合曲线
    base_points.append(base_points[0])
    base_points = np.array(base_points)
    
    # 使用样条插值创建更精细的边缘
    try:
        # 使用样条插值，提高平滑度参数以创建更圆滑的曲线
        tck, u = splprep([base_points[:, 0], base_points[:, 1]], s=3.0, per=True)
        
        # 生成更密集的点以增加细节
        u_new = np.linspace(0, 1, num_points)
        smooth_points = splev(u_new, tck)
        
        # 适当减少随机扰动强度，创建更圆滑的海岸线
        for i in range(len(smooth_points[0])):
            # 根据位置添加多层次的扰动
            position_factor = i / len(smooth_points[0])
            
            # 基础噪声强度 - 减少强度以增加圆滑度
            base_noise = 1.5 + 0.8 * np.sin(position_factor * 6 * np.pi)
            
            # 中等频率扰动 - 减少强度
            medium_noise = 0.5 * np.sin(position_factor * 12 * np.pi + random.uniform(0, 2*np.pi))
            
            # 高频扰动 - 减少强度
            high_noise = 0.2 * np.sin(position_factor * 24 * np.pi + random.uniform(0, 2*np.pi))
            
            # 超高频扰动 - 大幅减少强度
            ultra_high_noise = 0.1 * np.sin(position_factor * 48 * np.pi + random.uniform(0, 2*np.pi))
            
            # 组合所有扰动
            total_noise_strength = base_noise + medium_noise + high_noise + ultra_high_noise
            
            # 添加适度的随机扰动
            noise_x = random.uniform(-total_noise_strength, total_noise_strength)
            noise_y = random.uniform(-total_noise_strength, total_noise_strength)
            
            # 应用扰动
            smooth_points[0][i] += noise_x
            smooth_points[1][i] += noise_y
        
        # 添加适度的随机细节以保持圆滑度
        for i in range(0, len(smooth_points[0]), 3):
            detail_factor = random.uniform(0.5, 1.2)
            angle_offset = random.uniform(-0.2, 0.2)
            radius_offset = random.uniform(-0.8, 0.8) * detail_factor
            
            # 计算当前点的极坐标
            current_x = smooth_points[0][i] - center_x
            current_y = smooth_points[1][i] - center_y
            current_radius = np.sqrt(current_x**2 + current_y**2)
            current_angle = np.arctan2(current_y, current_x)
            
            # 应用细节变化
            new_radius = current_radius + radius_offset
            new_angle = current_angle + angle_offset
            
            # 转换回笛卡尔坐标
            smooth_points[0][i] = center_x + new_radius * np.cos(new_angle)
            smooth_points[1][i] = center_y + new_radius * np.sin(new_angle)
        
        # 第三次样条插值以进一步平滑所有曲线，创建更加圆滑的转角
        try:
            final_points = np.column_stack((smooth_points[0], smooth_points[1]))
            tck_final, u_final = splprep([final_points[:, 0], final_points[:, 1]], s=4.0, per=True)
            u_final_new = np.linspace(0, 1, num_points)
            final_smooth = splev(u_final_new, tck_final)
            
            # 最终平滑处理：使用更高的平滑度参数确保转角圆滑
            tck_ultra, u_ultra = splprep([final_smooth[0], final_smooth[1]], s=6.0, per=True)
            u_ultra_new = np.linspace(0, 1, num_points)
            ultra_smooth = splev(u_ultra_new, tck_ultra)
            map_points = np.column_stack((ultra_smooth[0], ultra_smooth[1]))
        except:
            try:
                final_points = np.column_stack((smooth_points[0], smooth_points[1]))
                tck_final, u_final = splprep([final_points[:, 0], final_points[:, 1]], s=4.0, per=True)
                u_final_new = np.linspace(0, 1, num_points)
                final_smooth = splev(u_final_new, tck_final)
                map_points = np.column_stack((final_smooth[0], final_smooth[1]))
            except:
                map_points = np.column_stack((smooth_points[0], smooth_points[1]))
        
    except:
        # 如果插值失败，使用原始点但添加一些随机扰动
        map_points = base_points[:-1]
        for i in range(len(map_points)):
            map_points[i][0] += random.uniform(-1.0, 1.0)
            map_points[i][1] += random.uniform(-1.0, 1.0)
    
    return map_points



def generate_small_maps(main_map_points, width, height):
    """
    不生成附加地形，只返回空列表
    
    参数:
        main_map_points: 主地形边界点列表
        width: 地图宽度
        height: 地图高度
    
    返回:
        空列表
    """
    # 不生成附加地形，只返回空列表
    return []

def calculate_distance_to_boundary(x, y, boundary_points):
    """
    计算点到边界的距离
    
    参数:
        x: 点的x坐标
        y: 点的y坐标
        boundary_points: 边界点列表
    
    返回:
        到边界的距离
    """
    min_distance = float('inf')
    for i in range(len(boundary_points)):
        p1 = boundary_points[i]
        p2 = boundary_points[(i + 1) % len(boundary_points)]
        
        # 计算点到线段的距离
        segment_length = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        if segment_length == 0:
            continue
            
        # 计算投影点
        t = max(0, min(1, ((x - p1[0]) * (p2[0] - p1[0]) + (y - p1[1]) * (p2[1] - p1[1])) / (segment_length**2)))
        projection_x = p1[0] + t * (p2[0] - p1[0])
        projection_y = p1[1] + t * (p2[1] - p1[1])
        
        distance = np.sqrt((x - projection_x)**2 + (y - projection_y)**2)
        min_distance = min(min_distance, distance)
    
    return min_distance

def generate_elevation_data(main_boundary_points, small_boundary_points_list, width, height):
    """
    生成高程数据
    
    参数:
        main_boundary_points: 主地形边界点列表
        small_boundary_points_list: 附加地形边界点列表
        width: 地图宽度
        height: 地图高度
    
    返回:
        X, Y, Z: 网格坐标和高程数据
    """
    # 定义网格分辨率
    resolution = 100
    
    # 创建网格坐标
    x = np.linspace(0, width, resolution)
    y = np.linspace(0, height, resolution)
    X, Y = np.meshgrid(x, y)
    
    # 初始化高程数据
    Z = np.zeros((resolution, resolution))
    
    # 定义地形类型
    terrain_types = ['mountain', 'plateau', 'plain', 'basin', 'hills']
    
    # 处理所有地形（主地形和附加地形）
    all_maps = [(main_boundary_points, 'main')] + [(small_map, 'small') for small_map in small_boundary_points_list]
    
    for map_points_list, map_type in all_maps:
        # 为每个岛屿创建路径
        map_path = Path(map_points_list)
        
        # 创建岛屿掩码
        map_mask = np.zeros((resolution, resolution), dtype=bool)
        for i in range(resolution):
            for j in range(resolution):
                point = (X[i, j], Y[i, j])
                map_mask[i, j] = map_path.contains_point(point)
        
        # 使用多层噪声生成复杂地形
        # 生成基础噪声
        noise = np.random.normal(0, 1, (resolution, resolution))
        large_scale = gaussian_filter(noise, sigma=30)  # 大尺度地形
        medium_scale = gaussian_filter(noise, sigma=15)  # 中尺度地形
        small_scale = gaussian_filter(noise, sigma=5)   # 小尺度地形
        
        # 组合不同尺度的噪声
        combined_noise = (large_scale * 0.5 + medium_scale * 0.3 + small_scale * 0.2)
        combined_noise = (combined_noise - combined_noise.min()) / (combined_noise.max() - combined_noise.min())
        
        # 为每个地形特征创建权重
        terrain_weights = np.zeros((resolution, resolution))
        
        # 随机选择主要地形特征数量
        if map_type == 'main':
            num_features = random.randint(4, 7)
            max_elevation = random.uniform(70, 100)
        else:
            num_features = random.randint(2, 4)
            max_elevation = random.uniform(25, 45)
        
        # 获取岛屿边界范围
        min_x, max_x = np.min(map_points_list[:, 0]), np.max(map_points_list[:, 0])
        min_y, max_y = np.min(map_points_list[:, 1]), np.max(map_points_list[:, 1])
        
        # 预生成随机形状参数
        shape_params = []
        for _ in range(num_features):
            terrain_type = random.choice(terrain_types)
            
            # 随机中心位置，避免过于集中
            margin_x = (max_x - min_x) * 0.15
            margin_y = (max_y - min_y) * 0.15
            center_x = random.uniform(min_x + margin_x, max_x - margin_x)
            center_y = random.uniform(min_y + margin_y, max_y - margin_y)
            
            # 随机形状参数
            max_distance = random.uniform(min(max_x - min_x, max_y - min_y) / 4, 
                                        min(max_x - min_x, max_y - min_y) / 2.5)
            
            # 随机椭圆变形
            angle = random.uniform(0, 2*np.pi)
            stretch_x = random.uniform(0.7, 1.3)
            stretch_y = random.uniform(0.7, 1.3)
            
            shape_params.append((terrain_type, center_x, center_y, max_distance, angle, stretch_x, stretch_y))
        
        for terrain_type, center_x, center_y, max_distance, angle, stretch_x, stretch_y in shape_params:
            # 创建椭圆变形距离场
            dx = X - center_x
            dy = Y - center_y
            
            # 应用旋转和拉伸
            rotated_x = dx * np.cos(angle) + dy * np.sin(angle)
            rotated_y = -dx * np.sin(angle) + dy * np.cos(angle)
            
            # 椭圆距离
            elliptical_distance = np.sqrt((rotated_x/stretch_x)**2 + (rotated_y/stretch_y)**2)
            
            # 根据地形类型创建不规则的自然形状
            if terrain_type == 'mountain':
                # 山脉：不规则山峰，使用椭圆距离和噪声
                noise_shape = np.random.normal(0, 0.3, elliptical_distance.shape)
                mountain_base = np.exp(-elliptical_distance**1.8 / (2 * (max_distance/4)**2)) * (0.7 + noise_shape * 0.3)
                # 添加不规则边界
                mountain_base *= (1 + 0.2 * np.sin(elliptical_distance * 8) * np.exp(-elliptical_distance/2))
                weight = np.clip(mountain_base, 0, 1) * 0.9
                
            elif terrain_type == 'plateau':
                # 高原：不规则的高原地形
                plateau_noise = np.random.normal(0, 0.25, elliptical_distance.shape)
                plateau_base = np.exp(-elliptical_distance**1.5 / (2 * (max_distance/3)**2))
                plateau_shape = plateau_base * (0.8 + plateau_noise * 0.2)
                # 添加边缘不规则性
                plateau_shape *= (1 - 0.15 * np.random.normal(0, 1, plateau_shape.shape) * 
                                np.exp(-elliptical_distance))
                weight = np.clip(plateau_shape, 0, 1) * 0.7
                
            elif terrain_type == 'plain':
                # 平原：不规则的平坦区域
                plain_noise = np.random.normal(0, 1.0, elliptical_distance.shape)
                plain_shape = np.exp(-elliptical_distance**2 / (2 * (max_distance/1.5)**2))
                plain_shape = plain_shape * (0.4 + plain_noise * 0.15)
                # 添加随机起伏
                plain_shape += 0.1 * np.sin(elliptical_distance * 3 + plain_noise * 5) * np.exp(-elliptical_distance/3)
                weight = np.clip(plain_shape, 0, 0.5)
                
            elif terrain_type == 'basin':
                # 盆地：不规则的凹陷地形
                basin_noise = np.random.normal(0, 0.3, elliptical_distance.shape)
                basin_base = -np.exp(-elliptical_distance**2 / (2 * (max_distance/2.5)**2))
                basin_shape = basin_base * (0.6 + basin_noise * 0.2)
                # 添加不规则边缘
                basin_shape -= 0.1 * np.random.normal(0, 1, basin_shape.shape) * np.exp(-elliptical_distance/2)
                weight = np.clip(basin_shape, -0.7, 0) * 0.6
                
            else:  # hills
                # 丘陵：不规则的起伏地形
                hill_noise = np.random.normal(0, 0.25, elliptical_distance.shape)
                hill_pattern = np.sin(elliptical_distance * 2.5 + hill_noise * 4) * \
                               np.exp(-elliptical_distance / (max_distance * 0.7))
                hill_shape = hill_pattern * (0.5 + hill_noise * 0.2)
                # 添加更多不规则性
                hill_shape += 0.1 * np.sin(elliptical_distance * 6 + np.random.normal(0, 1)) * \
                             np.exp(-elliptical_distance/1.5)
                weight = np.clip(hill_shape, -0.4, 0.4) * 0.5
            
            # 使用最大值而非叠加来避免高度叠加，确保地形自然融合
            terrain_weights = np.maximum(terrain_weights, weight)
        
        # 结合噪声和地形特征
        elevation = combined_noise * 0.3 + terrain_weights
        
        # 归一化到0-1范围
        elevation = (elevation - elevation.min()) / (elevation.max() - elevation.min())
        
        # 应用岛屿掩码和缩放高程
        elevation = elevation * map_mask * max_elevation
        
        # 添加随机变化使地形更自然
        random_variation = np.random.normal(0, max_elevation * 0.05, (resolution, resolution))
        elevation = elevation + random_variation * map_mask
        
        # 确保边界处高程平滑过渡到0，使用更平缓的坡度
        for i in range(resolution):
            for j in range(resolution):
                if map_mask[i, j]:
                    distance_to_boundary = calculate_distance_to_boundary(X[i, j], Y[i, j], map_points_list)
                    # 增加过渡区域宽度，从3扩展到8
                    transition_width = 8
                    if distance_to_boundary < transition_width:
                        # 使用指数衰减函数，使坡度更加平缓
                        # 当距离为0时，衰减因子为0；当距离接近transition_width时，衰减因子接近1
                        smooth_factor = 1 - np.exp(-3 * distance_to_boundary / transition_width)
                        elevation[i, j] *= smooth_factor
                        
                        # 向外扩展岛屿范围，在边界外创建渐变区域
                        if distance_to_boundary < 2:
                            # 在边界外1个单位范围内，创建非常平缓的过渡
                            extended_factor = distance_to_boundary / 2
                            elevation[i, j] *= (0.3 + 0.7 * extended_factor)
        
        # 确保高程非负
        elevation = np.clip(elevation, 0, None)
        
        # 合并到总高程数据
        Z = np.maximum(Z, elevation)
    
    return X, Y, Z

class mapMapGenerator:
    def __init__(self, width=100, height=100, num_points=80):
        self.width = width
        self.height = height
        self.num_points = num_points
        self.fig = None
        self.ax = None
        self.canvas = None
        
    def generate_map(self):
        """
        生成完整的地形地图
        """
        # 动态创建fig和ax对象
        self.fig, self.ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # 如果是交互模式，设置键盘事件
        try:
            self.canvas = self.fig.canvas
            self.canvas.mpl_connect('key_press_event', self.on_key_press)
        except:
            # 在非交互模式下（如服务器端）忽略键盘事件
            pass
        
        # 生成复杂地形边界
        main_points = generate_complex_map(self.width, self.height, self.num_points)
        
        # 生成附加地形
        small_terrain_list = generate_small_maps(main_points, self.width, self.height)
        
        # 生成高程数据
        X, Y, Z = generate_elevation_data(main_points, small_terrain_list, self.width, self.height)
        
        # 设置背景为深蓝色（海洋）
        self.ax.set_facecolor('#1E90FF')
        
        # 不绘制等高线轮廓线，只显示填充区域
        
        # 简化等高线系统 - 减少等高线数量并取消高度标注
        # 为丰富地形定义颜色渐变（8个层次）
        colors = ['#1E90FF', '#228B22', '#32CD32', '#9ACD32',  # 蓝色海洋到绿色平原
                  '#DAA520', '#CD853F', '#8B4513', '#FFFFFF']   # 黄土地到棕色山地到白色雪顶
        
        # 简化的等高线数量（从15减少到8）
        simple_levels = 8
        
        # 使用mask确保等高线只在岛屿区域内显示
        from matplotlib.path import Path as MPath
        
        # 创建岛屿边界路径
        map_path = MPath(main_points)
        
        # 创建mask数组，确保等高线完全闭合在岛屿边界内
        x_flat = X.flatten()
        y_flat = Y.flatten()
        points = np.column_stack((x_flat, y_flat))
        mask = ~map_path.contains_points(points).reshape(X.shape)
        
        # 应用mask，确保等高线闭合
        Z_masked = np.ma.array(Z, mask=mask)
        
        # 绘制等高线填充和轮廓线
        contourf = self.ax.contourf(X, Y, Z_masked, levels=simple_levels, 
                                    colors=colors, alpha=0.7)
        
        # 绘制等高线轮廓线但不标注高度
        self.ax.contour(X, Y, Z_masked, levels=simple_levels, 
                       colors='#654321', linewidths=0.8, alpha=0.6)
        
        # 不绘制岛屿外框线，让等高线自然显示地形
        
        # 设置坐标轴范围
        self.ax.set_xlim(0, self.width)
        self.ax.set_ylim(0, self.height)
        
        # 设置坐标轴比例相等
        self.ax.set_aspect('equal')
        
        # 移除坐标轴
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # 彻底清除所有标题和文本
        self.ax.set_title('')
        plt.title('')
        self.fig.suptitle('')
        
        # 强制清除所有可能的文本元素（更保守的方法）
        try:
            # 只清除文本对象，不删除其他必要的子元素
            for txt in self.ax.texts[:]:
                txt.remove()
            for txt in self.fig.texts[:]:
                txt.remove()
            # 不清除艺术家对象和子元素，避免破坏图形结构
        except Exception as text_remove_error:
            print(f"清除文本时出错: {text_remove_error}")
        
        # 在tight_layout之前再次清除标题
        self.ax.set_title('')
        plt.title('')
        self.fig.suptitle('')
        
        # 显示图形
        # 不使用tight_layout，因为它在服务器端可能导致fig对象被破坏
        if self.fig is not None:
            self.fig.canvas.draw()
        
        # 在tight_layout之后彻底清除所有标题和文本
        if self.ax is not None:
            self.ax.set_title('')
        plt.title('')
        if self.fig is not None:
            self.fig.suptitle('')
        
        # 再次强制清除所有可能的文本元素（更保守的方法）
        try:
            # 只清除文本对象，不删除其他必要的子元素
            if self.ax is not None:
                for txt in self.ax.texts[:]:
                    txt.remove()
            if self.fig is not None:
                for txt in self.fig.texts[:]:
                    txt.remove()
            # 不清除艺术家对象和子元素，避免破坏图形结构
        except Exception as text_remove_error:
            print(f"最终清除文本时出错: {text_remove_error}")
        
        return self.fig, self.ax, main_points, small_terrain_list
    
    def on_key_press(self, event):
        """
        处理键盘事件
        """
        if event.key.lower() == 'r':
            print("重新生成地形地图...")
            self.generate_map()
    
    def show(self):
        """
        显示地图
        """
        self.generate_map()
        # 在显示之前彻底清除所有标题和文本
        if self.ax is not None:
            self.ax.set_title('')
        plt.title('')
        if self.fig is not None:
            self.fig.suptitle('')
        
        # 强制清除所有可能的文本元素（更保守的方法）
        try:
            # 只清除文本对象，不删除其他必要的子元素
            if self.ax is not None:
                for txt in self.ax.texts[:]:
                    txt.remove()
            if self.fig is not None:
                for txt in self.fig.texts[:]:
                    txt.remove()
            # 不清除艺术家对象和子元素，避免破坏图形结构
        except Exception as text_remove_error:
            print(f"显示前清除文本时出错: {text_remove_error}")
        
        plt.show()

def create_map_map(width=100, height=100, num_points=80):
    """
    创建地形地图（保持向后兼容）
    
    参数:
        width: 地图宽度
        height: 地图高度
        num_points: 地形边界点数
    """
    generator = mapMapGenerator(width, height, num_points)
    return generator.show()

def save_map_map(filename='terrain_map.png', width=100, height=100, num_points=80):
    """
    保存地形地图为图片文件
    
    参数:
        filename: 保存文件名
        width: 地图宽度
        height: 地图高度
        num_points: 地形边界点数
    """
    generator = mapMapGenerator(width, height, num_points)
    fig, ax, main_points = generator.generate_map()
    
    # 在保存之前彻底清除所有标题和文本
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
        print(f"保存前清除文本时出错: {text_remove_error}")
    
    # 在保存之前最后一次清除标题
    ax.set_title('')
    plt.title('')
    fig.suptitle('')
    
    fig.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'地形地图已保存为: {filename}')

if __name__ == '__main__':
    # 生成并显示随机地形地图
    create_map_map(width=100, height=100, num_points=80)
    
    # 也可以保存为图片文件
    # save_map_map('complex_terrain.png', width=150, height=150, num_points=120)