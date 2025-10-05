#注意！这只是一个列举插件
# ---------------------- 插件核心配置（主程序读取） ----------------------
# 触发指令（用户输入该指令调用插件）
trigger_cmd = "/pic"

# 插件名称
name = "随机二次元图片插件（栗次元版）"

# 功能描述
desc = "随机调用栗次元API获取图片，自动用浏览器打开（直接输入/pic）"

# ---------------------- 插件核心逻辑 ----------------------
import requests
import subprocess
import os
import random

# 提供的3个栗次元API地址（随机调用其一）
ANIME_API_LIST = [
    "https://t.alcy.cc/mp",    # 移动竖图
    "https://t.alcy.cc/pc",    # PC横图
    "https://t.alcy.cc/"       # 栗次元主接口（默认返回二次元内容）
]

def execute(params: str) -> str:
    """
    执行函数：随机选API获取图片，在Termux中可靠地打开浏览器
    params: 指令后参数（本插件无需参数，忽略）
    """
    # 1. 随机选择一个API地址
    selected_api = random.choice(ANIME_API_LIST)

    # 2. 调用选中的API获取图片URL
    try:
        # 栗次元API直接返回图片内容或重定向到图片地址，需处理两种情况
        response = requests.get(
            selected_api,
            allow_redirects=True,  # 允许重定向，获取最终图片地址
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Linux; Android) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"}
        )
        response.raise_for_status()

        # 区分API返回类型：若为图片直接返回URL，若为页面则提取图片
        if "image" in response.headers.get("Content-Type", ""):
            pic_url = response.url  # 直接返回图片的API
        else:
            # 若API返回页面，尝试从页面中提取首张图片（适配主接口）
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                img_tag = soup.find("img")
                if not img_tag or not img_tag.get("src"):
                    raise Exception(f"未从API {selected_api} 提取到图片")
                pic_url = img_tag["src"]
                # 补全相对路径（若图片地址不含域名）
                if not pic_url.startswith("http"):
                    pic_url = f"https://t.alcy.cc{pic_url}"
            except ImportError:
                # 缺少bs4时降级为直接打开API地址
                pic_url = selected_api

    # 异常处理
    except requests.exceptions.Timeout:
        return f"⏳ API {selected_api} 请求超时，请稍后重试"
    except requests.exceptions.ConnectionError:
        return f"❌ 无法连接API {selected_api}，检查网络"
    except Exception as e:
        return f"❌ 图片获取失败：{str(e)}\n尝试打开API地址：{selected_api}"

    # 3. 在Termux中可靠地打开浏览器
    try:
        # 方法1: 使用termux-open-url（最直接）
        try:
            result = subprocess.run(
                ["termux-open-url", pic_url],
                check=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            return f"✅ 随机选中API：{selected_api}\n图片正在浏览器中打开...\n图片地址：{pic_url}"
        
        except (FileNotFoundError, subprocess.CalledProcessError):
            # 方法2: 使用am命令（Android原生方式）
            try:
                # 清除可能存在的浏览器选择缓存
                subprocess.run(["am", "force-stop", "com.termux"], check=False)
                
                # 使用am命令打开链接
                result = subprocess.run(
                    [
                        "am", "start",
                        "--user", "0",
                        "-a", "android.intent.action.VIEW",
                        "-d", pic_url,
                        "-c", "android.intent.category.BROWSABLE"
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return f"✅ 随机选中API：{selected_api}\n图片正在浏览器中打开...\n图片地址：{pic_url}"
            
            except subprocess.CalledProcessError as e:
                # 方法3: 尝试使用termux-api的广播方式
                try:
                    result = subprocess.run(
                        [
                            "am", "broadcast",
                            "-a", "com.termux.api.OPEN_URL",
                            "-e", "url", pic_url
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    return f"✅ 随机选中API：{selected_api}\n图片正在浏览器中打开...\n图片地址：{pic_url}"
                
                except subprocess.CalledProcessError:
                    # 所有方法都失败，提供手动访问选项
                    return f"❌ 无法自动打开浏览器\n✅ 图片获取成功！\n🔗 请手动复制以下地址到浏览器打开：\n{pic_url}\n\n📱 或者尝试安装Termux API：\npkg install termux-api"

    except Exception as e:
        return f"❌ 打开浏览器时出错：{str(e)}\n✅ 图片地址：{pic_url}\n请手动复制到浏览器打开"

    return f"✅ 随机选中API：{selected_api}\n图片地址：{pic_url}\n请手动在浏览器中打开"
