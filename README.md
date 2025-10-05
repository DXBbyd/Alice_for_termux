```markdown
# Alice for Termux 🤖

一个专为Termux设计的智能助手项目，让天童爱丽丝在你的移动设备上焕发活力！

## 📥 安装部署

### 第一步：克隆项目

**主仓库（推荐）**
```bash
git clone https://github.com/DXBbyd/Alice_for_termux.git
```

镜像仓库（如遇网络问题）

```bash
git clone http://hk-proxy.gitwarp.com/https://github.com/DXBbyd/Alice_for_termux.git
```

第二步：进入项目目录

```bash
cd Alice_for_termux
```

第三步：环境配置

确保你的系统已安装：

· ✅ Python 3.8+
· ✅ uv (现代Python包管理器)
· ✅ pip (Python包安装器)

第四步：创建虚拟环境

推荐使用 uv 创建虚拟环境：

```bash
uv venv
```

激活虚拟环境：

```bash
source .venv/bin/activate
```

第五步：安装依赖

使用阿里云镜像快速安装：

```bash
uv pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
```

第六步：启动程序

```bash
python start.py
```

🎯 快速命令汇总

```bash
git clone https://github.com/DXBbyd/Alice_for_termux.git
cd Alice_for_termux
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
python start.py
```

🔧 故障排除

如果 uv 未安装：

```bash
pip install uv
# 或
curl -LsSf https://astral.sh/uv/install.sh | sh
```

如果虚拟环境激活失败：

```bash
# 检查虚拟环境目录
ls -la | grep venv
# 手动激活
source venv/bin/activate
```

如果依赖安装失败：

```bash
# 使用传统pip
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
```

⚠️ 注意
每次重启，请手动进入虚拟环境

🆘 获取帮助

如遇问题，请按以下步骤排查：

1. 确认Python版本 ≥ 3.8
2. 确认虚拟环境已激活（命令行前应有(.venv)提示）
3. 确认所有依赖安装成功
4. 检查终端权限和存储空间

---
README.md直接用AI写的，因为我懒awa
