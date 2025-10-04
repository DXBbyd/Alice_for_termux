import os
import sys
import importlib.util

# 插件注册表和禁用列表（全局）
PLUGIN_REGISTRY = {}  # {"/指令": (插件名, 描述, 执行函数)}
PLUGIN_DISABLED = set()

def load_all_plugins():
    """扫描 plugins/ 下所有文件夹，读取每个文件夹内的 config.py 作为插件配置"""
    global PLUGIN_REGISTRY
    PLUGIN_REGISTRY.clear()
    plugin_root_dir = "./plugins"
    
    # 创建插件总目录（若不存在）
    if not os.path.exists(plugin_root_dir):
        os.mkdir(plugin_root_dir)
        print("[插件加载器] 插件总目录 plugins/ 已创建")
        return
    
    #读取插件目录下下的所有插件
    for plugin_folder in os.listdir(plugin_root_dir):
        plugin_folder_path = os.path.join(plugin_root_dir, plugin_folder)
        # 只处理文件夹（跳过单个文件）
        if not os.path.isdir(plugin_folder_path):
            continue
        
        # 插件配置文件路径（文件夹内必须有 config.py）
        plugin_config_path = os.path.join(plugin_folder_path, "config.py")
        if not os.path.exists(plugin_config_path):
            print(f"[插件加载器] 文件夹 {plugin_folder} 缺少 config.py，跳过")
            continue
        
        # 动态导入插件的 config.py
        try:
            # 给每个插件的config模块起唯一名字（避免冲突）
            module_name = f"plugin_{plugin_folder}_config"
            spec = importlib.util.spec_from_file_location(module_name, plugin_config_path)
            plugin_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_config)
            
            # 校验插件配置完整性（必须包含4个核心字段）
            required_fields = ["trigger_cmd", "name", "desc", "execute"]
            if not all(hasattr(plugin_config, field) for field in required_fields):
                print(f"[插件加载器] {plugin_folder}/config.py 缺失字段（需{required_fields}），跳过")
                continue
            
            # 注册插件（触发指令去重）
            trigger = plugin_config.trigger_cmd
            if trigger in PLUGIN_REGISTRY:
                print(f"[插件加载器] 指令 {trigger} 已被其他插件占用，跳过 {plugin_folder}")
                continue
            
            PLUGIN_REGISTRY[trigger] = (
                plugin_config.name,
                plugin_config.desc,
                plugin_config.execute
            )
            print(f"[插件加载器] 加载成功：{plugin_config.name}（{plugin_folder}，指令：{trigger}）")
        
        except Exception as e:
            print(f"[插件加载器] 加载 {plugin_folder} 失败：{str(e)}")

# 初始化自动加载插件
load_all_plugins()
