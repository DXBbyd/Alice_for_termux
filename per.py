import os

# 人格文件夹路径（固定，与main.py同目录下的persona文件夹）
PERSONA_DIR = "./persona"
# 当前激活的人格（默认值）
current_persona = "你是AI爱丽丝超算，一个友好的多功能助手，回答简洁自然。"

def init_persona():
    """初始化人格文件夹，自动生成3个默认人格文件"""
    if not os.path.exists(PERSONA_DIR):
        os.mkdir(PERSONA_DIR)
        # 写入默认人格
        default_personas = [
            ("1_可爱助手.txt", "你是AI爱丽丝超算，性格软萌，喜欢用语气词（呀、呢、哦），回答简短亲切。"),
            ("2_技术专家.txt", "你是AI爱丽丝超算，技术领域专家，回答专业、严谨，侧重逻辑和细节，避免口语化。"),
            ("3_幽默搭档.txt", "你是AI爱丽丝超算，幽默风趣，擅长用调侃和比喻，回答轻松接地气，偶尔讲冷笑话。")
        ]
        for filename, content in default_personas:
            with open(f"{PERSONA_DIR}/{filename}", "w", encoding="utf-8") as f:
                f.write(content)
        print(f"[初始化] 已创建人格文件夹及默认人格")

def list_personas():
    """列出所有可用人格（带序号）"""
    init_persona()  # 确保文件夹存在
    # 获取所有txt格式的人格文件
    persona_files = [f for f in os.listdir(PERSONA_DIR) if f.endswith(".txt")]
    if not persona_files:
        return "暂无人格文件，可在 persona/ 文件夹添加 .txt 人格描述"
    
    # 按文件名序号排序（支持1_xxx.txt格式，怕我忘了waw）
    persona_files.sort(key=lambda x: int(x.split("_")[0]) if x.split("_")[0].isdigit() else 999)
    
    # 构建列表字符串
    res = "📋 可用人格列表：\n"
    for idx, filename in enumerate(persona_files, 1):
        # 去掉.txt后缀，显示人格名
        persona_name = os.path.splitext(filename)[0]
        res += f"  {idx}. {persona_name}\n"
    res += "\n切换指令：/persona 序号（例：/persona 1）"
    return res.strip()

def switch_persona(seq_num: str, clear_history_func):
    """切换人格，自动清空聊天记录"""
    init_persona()
    persona_files = [f for f in os.listdir(PERSONA_DIR) if f.endswith(".txt")]
    persona_files.sort(key=lambda x: int(x.split("_")[0]) if x.split("_")[0].isdigit() else 999)
    
    # 校验序号合法性
    try:
        idx = int(seq_num) - 1  # 转为列表索引
        if idx < 0 or idx >= len(persona_files):
            return f"序号无效！请输入 1-{len(persona_files)} 之间的数字"
    except ValueError:
        return "序号格式错误！请输入数字（例：/persona 1）"
    
    # 读取选中的人格内容
    selected_file = persona_files[idx]
    with open(f"{PERSONA_DIR}/{selected_file}", "r", encoding="utf-8") as f:
        persona_content = f.read().strip()
    if not persona_content:
        return f"「{selected_file}」文件内容为空，切换失败"
    
    # 更新当前人格并清空历史
    global current_persona
    current_persona = persona_content
    clear_history_func()  # 调用main.py的清空历史函数
    return f"✅ 人格切换成功！当前人格：{os.path.splitext(selected_file)[0]}\n（聊天记录已自动清空）"

def get_current_persona():
    """提供给main.py获取当前人格"""
    return current_persona
