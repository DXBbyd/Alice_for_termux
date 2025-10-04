import os
import importlib.util
from config import PROJECT_CONFIG

# 插件注册表+禁用列表（全局）
PLUGIN_REGISTRY = {}
PLUGIN_DISABLED = set()

def _load_single_plugin(plugin_path: str) -> None:
    """加载单个插件"""
    plugin_name = os.path.basename(plugin_path)
    config_path = os.path.join(plugin_path, "config.json")
    if not os.path.exists(config_path):
        print(f"[插件] {plugin_name} 缺少 config.json，跳过")
        return
    with open(config_path, "r", encoding="utf-8") as f:
        config = eval(f.read())  # 简化读取，适配基础插件
    if not all(k in config for k in ["command", "name", "desc"]):
        print(f"[插件] {plugin_name} 配置不全，跳过")
        return

    init_path = os.path.join(plugin_path, "__init__.py")
    if not os.path.exists(init_path):
        print(f"[插件] {plugin_name} 缺少 __init__.py，跳过")
        return
    spec = importlib.util.spec_from_file_location(f"plugin_{plugin_name}", init_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "execute"):
        print(f"[插件] {plugin_name} 缺少 execute 函数，跳过")
        return

    PLUGIN_REGISTRY[config["command"]] = (config["name"], config["desc"], module.execute)
    print(f"[插件] 加载成功：{config['name']}（指令：{config['command']}）")

def load_plugins() -> None:
    """加载所有插件"""
    global PLUGIN_REGISTRY
    PLUGIN_REGISTRY.clear()
    plugin_dir = PROJECT_CONFIG["plugin_dir"]
    if not os.path.exists(plugin_dir):
        os.mkdir(plugin_dir)
        print(f"[插件] 插件文件夹不存在，已自动创建")
        return
    for item in os.listdir(plugin_dir):
        item_path = os.path.join(plugin_dir, item)
        if os.path.isdir(item_path):
            _load_single_plugin(item_path)

def get_plugin_registry() -> dict:
    return PLUGIN_REGISTRY

def get_disabled_plugins() -> set:
    return PLUGIN_DISABLED

def disable_plugin(cmd_prefix: str) -> str:
    """禁用插件"""
    if cmd_prefix not in PLUGIN_REGISTRY:
        return f"未找到指令前缀「{cmd_prefix}」的插件"
    if cmd_prefix in PLUGIN_DISABLED:
        return f"插件「{PLUGIN_REGISTRY[cmd_prefix][0]}」已禁用"
    PLUGIN_DISABLED.add(cmd_prefix)
    return f"禁用插件：{PLUGIN_REGISTRY[cmd_prefix][0]}（指令：{cmd_prefix}）"

def enable_plugin(cmd_prefix: str) -> str:
    """启用插件"""
    if cmd_prefix not in PLUGIN_REGISTRY:
        return f"未找到指令前缀「{cmd_prefix}」的插件"
    if cmd_prefix not in PLUGIN_DISABLED:
        return f"插件「{PLUGIN_REGISTRY[cmd_prefix][0]}」已启用"
    PLUGIN_DISABLED.remove(cmd_prefix)
    return f"启用插件：{PLUGIN_REGISTRY[cmd_prefix][0]}（指令：{cmd_prefix}）"

def show_plugins() -> str:
    """显示所有插件状态"""
    if not PLUGIN_REGISTRY:
        return "暂无已加载的插件（可在 plugins/ 目录添加插件）"
    res = "🔌 已加载插件列表：\n"
    for cmd, (name, desc, _) in PLUGIN_REGISTRY.items():
        status = "禁用" if cmd in PLUGIN_DISABLED else "启用"
        res += f"  - {name}（指令：{cmd}）{status}：{desc}\n"
    return res.strip()
