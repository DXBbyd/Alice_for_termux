import os
import sys
import time
import subprocess
# ---------------------- 核心配置（保留原有ASCII标题） ----------------------
ALICE_X_ASCII = """
=============================================
         _    _       ____  __  __  _____  
        / \\  | |     / ___||  \\/  || ____| 
       / _ \\ | |    | |    | |\\/| ||  _|   
      / ___ \\| |___ | |___ | |  | || |___  
     /_/   \\_|_____| \\____||_|  |_||_____| 
                                          
               __   __  _     
              \\ \\ / / | |    
               \\ V /  | |    
                > <   | |___ 
               /_/\\_\\ |_____|
=============================================
"""
# 颜色码（保留原有）
COLOR_BLUE = "\033[94m"      # 标题蓝
COLOR_GREEN = "\033[92m"    # 成功绿
COLOR_YELLOW = "\033[93m"   # 提示黄
COLOR_RED = "\033[91m"      # 错误红
COLOR_RESET = "\033[0m"     # 重置
REQUIREMENTS = ["requests", "python-dotenv", "websockets"]
MIRROR_URL = "https://mirrors.aliyun.com/pypi/simple"
# ---------------------- 原有工具函数（完全保留） ----------------------
def print_ascii_title():
    print(f"{COLOR_BLUE}{ALICE_X_ASCII}{COLOR_RESET}")

def install_uv() -> bool:
    print(f"{COLOR_YELLOW}🔧 未检测到 UV，正在安装...{COLOR_RESET}")
    try:
        subprocess.check_call(
            [sys.executable, "-c", 
             "import os; os.system('curl -LsSf https://astral.sh/uv/install.sh | sh')"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        uv_path = os.path.expanduser("~/.cargo/bin")
        os.environ["PATH"] = f"{uv_path}:{os.environ['PATH']}"
        print(f"{COLOR_GREEN}✅ UV 安装成功！{COLOR_RESET}")
        return True
    except Exception:
        print(f"{COLOR_YELLOW}❌ UV 安装失败，改用 pip...{COLOR_RESET}")
        return False

def check_deps() -> bool:
    print(f"{COLOR_YELLOW}[1/3] 检查依赖（阿里云镜像）...{COLOR_RESET}")
    has_uv = False
    try:
        subprocess.check_call(["uv", "--version"], stdout=subprocess.DEVNULL)
        has_uv = True
    except:
        has_uv = install_uv()
    try:
        cmd = ["uv", "pip", "install", "--upgrade", f"--index-url={MIRROR_URL}", *REQUIREMENTS] if has_uv else \
              [sys.executable, "-m", "pip", "install", "--upgrade", f"-i={MIRROR_URL}", *REQUIREMENTS]
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{COLOR_GREEN}✅ 依赖安装/补全完成！{COLOR_RESET}")
        return True
    except Exception:
        print(f"{COLOR_YELLOW}❌ 依赖安装失败，手动执行：")
        print(f"uv pip install -i {MIRROR_URL} {' '.join(REQUIREMENTS)}{COLOR_RESET}")
        return False

def check_config() -> bool:
    print(f"\n{COLOR_YELLOW}[2/3] 检查配置文件...{COLOR_RESET}")
    if not os.path.exists("config.py"):
        print(f"{COLOR_YELLOW}❌ 未找到 config.py！{COLOR_RESET}")
        return False
    with open("config.py", "r", encoding="utf-8") as f:
        if "你的AI_API密钥" in f.read():
            print(f"{COLOR_YELLOW}⚠️  API密钥未替换！{COLOR_RESET}")
            return input("继续启动？(y/n)：").strip().lower() == "y"
    print(f"{COLOR_GREEN}✅ 配置检查通过！{COLOR_RESET}")
    return True

def start_nt_adapter():
    """启动NT适配器（WS服务器），启动后可返回主程序"""
    print(f"\n{COLOR_YELLOW}📌 启动 NT 适配器（WS服务器）...{COLOR_RESET}")
    try:
        # 导入并启动NT适配器
        from NT_adapter import run_ws_server
        print(f"{COLOR_GREEN}✅ NT 适配器启动中，监听地址：ws://127.0.0.1:2048/ws{COLOR_RESET}")
        print(f"{COLOR_YELLOW}⚠️  按 Ctrl+C 关闭适配器并返回 Alice 主程序{COLOR_RESET}")
        run_ws_server()
        # 适配器关闭后返回主程序
        print(f"\n{COLOR_GREEN}✅ NT 适配器已关闭，返回 Alice 主程序{COLOR_RESET}")
    except ImportError:
        print(f"{COLOR_RED}❌ 未找到 NT_adapter.py，请先创建该文件！{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}❌ NT 适配器启动失败：{str(e)}{COLOR_RESET}")

def start_main() -> None:
    print(f"\n{COLOR_YELLOW}[3/3] 启动 AI 爱丽丝超算...{COLOR_RESET}")
    for i in range(3):
        print(f"{' ' * 15}加载中{'.' * (i+1)}", end="\r")
        time.sleep(0.8)
    
    # ------------ 关键：导入main.py模块，恢复插件读取与指令 ------------
    import main
    # 初始化人格+加载插件（main.py原有逻辑）
    main.init_persona()
    main.load_all_plugins()
    ai_client = main.AIClient()
    
    print(f"\n{COLOR_GREEN}✅ Alice X 启动成功！输入 /help 查看所有指令{COLOR_RESET}")
    while True:
        user_input = input("你：").strip()
        if not user_input:
            continue

        # 1. 退出程序
        if user_input.lower() in ["q", "/quit"]:
            # 关闭WS线程（若存在）
            if main.ws_thread and main.ws_thread.is_alive():
                main.stop_ws_server()
                print("[Alice X] 📌 WS服务器已关闭")
            print("[Alice X] 再见！")
            break

        if user_input == "/start NT":
            start_nt_adapter()
            continue

        # 3. 完全保留 main.py 原有指令逻辑（插件/人格/聊天等）
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0]
            params = parts[1].strip() if len(parts) > 1 else ""

            # 原有内置指令（/help /plugins /persona等）
            if cmd == "/help":
                reply = main.show_help()
            elif cmd == "/info":
                reply = main.show_system_info()
            elif cmd == "/clear":
                reply = main.clear_chat_history()
            elif cmd == "/history":
                reply = main.show_chat_history()
            elif cmd == "/plugins":
                reply = main.show_plugins()  # 恢复插件列表指令
            elif cmd == "/reset":
                main.load_all_plugins()
                reply = "✅ 所有插件重载完成"
            elif cmd == "/disable":
                reply = main.disable_plugin(params) if params else "❌ 请指定禁用指令（例：/disable /weather）"
            elif cmd == "/enable":
                reply = main.enable_plugin(params) if params else "❌ 请指定启用指令（例：/enable /weather）"
            elif cmd == "/persona":
                reply = main.list_personas() if params == "ls" else main.switch_persona(params, main.clear_chat_history)
            elif cmd == "/start ws":
                # 保留原有的WS服务器指令（若需）
                if main.ws_thread and main.ws_thread.is_alive():
                    reply = "❌ WS服务器已在运行"
                else:
                    main.ws_thread = main.threading.Thread(target=main.start_ws_server, daemon=True)
                    main.ws_thread.start()
                    time.sleep(1)
                    reply = f"✅ WS服务器启动成功：ws://127.0.0.1:2048/ws"
            elif cmd == "/stop ws":
                reply = main.stop_ws_server() or "✅ WS服务器已关闭"
            else:
                # 恢复插件调用（/天气 /一言等）
                reply = main.call_plugin(user_input) or f"❌ 未知指令「{cmd}」"

        # 4. 非指令：AI聊天（保留原有逻辑）
        else:
            reply = ai_client.chat(user_input)

        # 输出回复+记录历史（保留原有逻辑）
        print(f"[Alice X] {reply}\n")
        if user_input.lower() not in ["q", "/quit", "/clear"]:
            main.chat_history.append(f"你：{user_input}\nAlice：{reply}")

# ---------------------- 主逻辑（完全保留原有启动流程） ----------------------
if __name__ == "__main__":
    os.system("clear")
    print_ascii_title()
    # 原有依赖+配置检查
    if check_deps() and check_config():
        start_main()
    else:
        print(f"\n{COLOR_YELLOW}❌ 启动中断！{COLOR_RESET}")
        sys.exit(1)
