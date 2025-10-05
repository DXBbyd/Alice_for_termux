import requests
import os
import sys
import datetime
import threading
from config import AI_CONFIG, PROJECT_CONFIG
 # 修复后的导入部分（新增 import time）
import requests
import os
import sys
import datetime
import threading
import time  # 新增这行！解决 time 未定义问题
from config import AI_CONFIG, PROJECT_CONFIG

# ---------------------- 导入外部模块 ----------------------
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from plugin_loader import PLUGIN_REGISTRY, PLUGIN_DISABLED, load_all_plugins
from per import list_personas, switch_persona, get_current_persona, init_persona

# ---------------------- 全局变量 ----------------------
chat_history = []  # 聊天记录存储
ws_thread = None   # QQ适配：WS服务器线程（后台运行）


# ---------------------- AI客户端（核心对话逻辑） ----------------------
class AIClient:
    def __init__(self):
        self.api_key = AI_CONFIG["api_key"]
        self.base_url = AI_CONFIG["base_url"]
        self.model = AI_CONFIG["model"]
        # AI请求头（固定格式）
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def chat(self, user_input: str) -> str:
        """调用AI接口生成回复，带当前人格"""
        # 未替换API密钥时的提示
        if self.api_key == "你的AI_API密钥":
            return "❌ 请先在 config.py 中填写真实的 AI_API 密钥！"
        
        try:
            # 构造请求体（包含人格指令+用户输入）
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": get_current_persona()},  # 人格设定
                    {"role": "user", "content": user_input}               # 用户输入
                ]
            }

            # 发送请求到AI接口
            response = requests.post(
                url=f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=15  # 15秒超时保护
            )
            response.raise_for_status()  # 捕获404/500等HTTP错误

            # 解析AI回复
            return response.json()["choices"][0]["message"]["content"].strip()

        except requests.exceptions.Timeout:
            return "⏳ AI请求超时，请稍后重试"
        except requests.exceptions.ConnectionError:
            return "❌ 网络连接失败，无法连接AI接口"
        except Exception as e:
            return f"AI调用失败：{str(e)}"


# ---------------------- 终端指令辅助函数（完整保留） ----------------------
def clear_chat_history():
    """清空聊天记录"""
    global chat_history
    chat_history = []
    return "✅ 聊天记录已清空"


def show_chat_history():
    """查看聊天记录"""
    if not chat_history:
        return "📜 暂无聊天记录"
    # 格式化输出历史记录
    history_str = ["📜 聊天记录："]
    for idx, record in enumerate(chat_history, 1):
        history_str.append(f"\n{idx}. {record}")
    return "\n".join(history_str)


def show_system_info():
    """查看系统信息"""
    plugin_total = len(PLUGIN_REGISTRY)
    plugin_enabled = plugin_total - len(PLUGIN_DISABLED)
    return (
        "=== 系统信息 ===\n"
        f"🤖 程序：Alice X\n"
        f"🐍 Python：{sys.version.split()[0]}\n"
        f"🔌 插件：{plugin_total}个（启用{plugin_enabled}/禁用{len(PLUGIN_DISABLED)}）\n"
        f"⏰ 时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


def show_help():
    """显示完整指令列表（含QQ适配指令）"""
    help_content = [
        "=== Alice X 指令大全 ===",
        "📌 基础指令",
        "   /help      - 查看本帮助列表",
        "   /quit      - 退出程序（自动关闭WS服务器）",
        "   /info      - 查看系统信息",
        "",
        "📌 聊天指令",
        "   /history   - 查看聊天记录",
        "   /clear     - 清空聊天记录",
        "",
        "📌 人格指令",
        "   /persona ls - 列出所有人格",
        "   /persona 序号 - 切换人格（例：/persona 1）",
        "",
        "📌 插件指令",
        "   /plugins   - 查看所有插件及状态",
        "   /reset     - 重载所有插件",
        "   /disable 指令 - 禁用插件（例：/disable /weather）",
        "   /enable 指令  - 启用插件（例：/enable /weather）",
        ",
    ]
    return "\n".join(help_content)


def show_plugins():
    """查看插件列表及状态"""
    if not PLUGIN_REGISTRY:
        return "🔌 暂无插件，请在 plugins/ 目录放置独立插件文件夹"
    
    plugin_list = ["🔌 插件列表："]
    for cmd, (name, desc, _) in PLUGIN_REGISTRY.items():
        status = "✅ 启用" if cmd not in PLUGIN_DISABLED else "❌ 禁用"
        plugin_list.append(f"   {cmd} - {name} {status}：{desc}")
    return "\n".join(plugin_list)


def disable_plugin(cmd: str) -> str:
    """禁用指定插件"""
    if cmd not in PLUGIN_REGISTRY:
        return f"❌ 未找到指令「{cmd}」对应的插件"
    if cmd in PLUGIN_DISABLED:
        return f"⚠️  插件「{PLUGIN_REGISTRY[cmd][0]}」已处于禁用状态"
    
    PLUGIN_DISABLED.add(cmd)
    return f"✅ 已禁用插件：{PLUGIN_REGISTRY[cmd][0]}（触发指令：{cmd}）"


def enable_plugin(cmd: str) -> str:
    """启用指定插件"""
    if cmd not in PLUGIN_REGISTRY:
        return f"❌ 未找到指令「{cmd}」对应的插件"
    if cmd not in PLUGIN_DISABLED:
        return f"⚠️  插件「{PLUGIN_REGISTRY[cmd][0]}」已处于启用状态"
    
    PLUGIN_DISABLED.remove(cmd)
    return f"✅ 已启用插件：{PLUGIN_REGISTRY[cmd][0]}（触发指令：{cmd}）"


def call_plugin(user_input: str) -> str:
    """解析输入并调用对应插件"""
    if not user_input.startswith("/"):
        return ""  # 非指令输入，不调用插件
    
    # 拆分指令与参数（支持参数含空格）
    parts = user_input.split(maxsplit=1)
    cmd = parts[0]
    params = parts[1]。strip() if len(parts) > 1 else ""

    # 匹配插件指令并调用
    if cmd in PLUGIN_REGISTRY:
        if cmd in PLUGIN_DISABLED:
            return f"❌ 插件「{PLUGIN_REGISTRY[cmd][0]}」已禁用，可输入 /enable {cmd} 启用"
        # 调用插件的 execute 函数
        return PLUGIN_REGISTRY[cmd][2](params)
    
    return ""  # 未匹配到插件，返回空


def start_ws_server():
    """启动WS服务器（供Napcat连接，后台线程运行）"""
    from QQadapter import run_ws_server
    host = PROJECT_CONFIG["ws_host"]
    port = PROJECT_CONFIG["ws_port"]
    # 调用QQadapter中的WS启动逻辑
    run_ws_server(host, port)


def stop_ws_server():
    """关闭WS服务器"""
    from QQadapter import shutdown_ws_server
    global ws_thread
    shutdown_ws_server()
    ws_thread = 无  # 重置线程变量


# ---------------------- 主交互逻辑（供start.py调用） ----------------------
def run_with_ws():
    """带WS控制的完整交互会话（终端+QQ双模式）"""
    # 初始化AI客户端
    ai_client = AIClient()
    print("🤖 Alice X（QQ适配版）启动成功！输入 /help 查看所有指令\n")

    global ws_thread
    while True:
        user_input = input("你：")。strip()
        if not user_input:
            continue  # 忽略空输入

        # 1. 退出程序（自动关闭WS服务器）
        if user_input.lower() in ["q", "/quit"]:
            if ws_thread and ws_thread.is_alive():
                stop_ws_server()
                print("[Alice X] 📌 WS服务器已关闭")
            print("[Alice X] 再见！")
            break

        # 2. QQ适配：WS服务器控制指令
        if user_input == "/start ws":
            if ws_thread and ws_thread.is_alive():
                reply = "❌ WS服务器已在运行，无需重复启动"
            else:
                # 启动WS服务器（后台线程，不阻塞终端）
                ws_thread = threading.Thread(target=start_ws_server, daemon=True)
                ws_thread.start()
                time.sleep(1)  # 等待服务器启动完成
                reply = f"✅ WS服务器启动成功！Napcat连接地址：ws://{PROJECT_CONFIG['ws_host']}:{PROJECT_CONFIG['ws_port']}/ws"
        
        elif user_input == "/stop ws":
            if not (ws_thread and ws_thread.is_alive()):
                reply = "❌ WS服务器未启动"
            else:
                stop_ws_server()
                reply = "✅ WS服务器已关闭"

        # 3. 原有内置指令处理
        elif user_input.startswith("/"):
            # 拆分指令与参数
            parts = user_input.split(maxsplit=1)
            cmd = parts[0]
            params = parts[1].strip() if len(parts) > 1 else ""

            # 匹配指令并执行
            if cmd == "/help":
                reply = show_help()
            elif cmd == "/info":
                reply = show_system_info()
            elif cmd == "/clear":
                reply = clear_chat_history()
            elif cmd == "/history":
                reply = show_chat_history()
            elif cmd == "/plugins":
                reply = show_plugins()
            elif cmd == "/reset":
                load_all_plugins()
                reply = "✅ 所有插件重载完成"
            elif cmd == "/disable":
                reply = disable_plugin(params) if params else "❌ 请指定禁用的插件指令（例：/disable /weather）"
            elif cmd == "/enable":
                reply = enable_plugin(params) if params else "❌ 请指定启用的插件指令（例：/enable /weather）"
            elif cmd == "/persona":
                if params == "ls":
                    reply = list_personas()
                else:
                    reply = switch_persona(params, clear_chat_history)
            else:
                # 未匹配内置指令，尝试调用插件
                reply = call_plugin(user_input) or f"❌ 未知指令「{cmd}」，输入 /help 查看支持的指令"

        # 4. 非指令输入：调用AI聊天
        else:
            reply = ai_client.chat(user_input)

        # 输出回复并记录聊天历史
        print(f"[Alice X] {reply}\n")
        chat_history.append(f"你：{user_input}\nAlice：{reply}")


# ---------------------- 原始主入口（单独运行main.py） ----------------------
def main():
    """不含QQ适配的原始交互模式"""
    init_persona()
    load_all_plugins()
    ai_client = AIClient()
    print("🤖 Alice X 启动成功！输入 /help 查看指令\n")

    while True:
        user_input = input("你：").strip()
        if not user_input:
            continue
        if user_input.lower() in ["q", "/quit"]:
            print("[Alice X] 再见！")
            break
        
        # 指令处理（复用上述辅助函数）
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0]
            params = parts[1].strip() if len(parts) > 1 else ""
            if cmd == "/help":
                reply = show_help()
            elif cmd == "/info":
                reply = show_system_info()
            elif cmd == "/clear":
                reply = clear_chat_history()
            elif cmd == "/history":
                reply = show_chat_history()
            elif cmd == "/plugins":
                reply = show_plugins()
            elif cmd == "/reset":
                load_all_plugins()
                reply = "✅ 插件重载完成"
            elif cmd == "/disable":
                reply = disable_plugin(params) if params else "❌ 请指定禁用指令"
            elif cmd == "/enable":
                reply = enable_plugin(params) if params else "❌ 请指定启用指令"
            elif cmd == "/persona":
                reply = list_personas() if params == "ls" else switch_persona(params, clear_chat_history)
            else:
                reply = call_plugin(user_input) or f"❌ 未知指令「{cmd}」"
        else:
            reply = ai_client.chat(user_input)
        
        print(f"[Alice X] {reply}\n")
        chat_history.append(f"你：{user_input}\nAlice：{reply}")


# 程序入口（单独运行main.py时启用原始模式）
if __name__ == "__main__":
    main()
