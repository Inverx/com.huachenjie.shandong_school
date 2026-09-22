# 闪动校园协议 CLI 工具箱

面向闪动校园 Android 客户端的纯协议工程化工具集，提供一命令一入口式独立业务 CLI，底层横向复用签名、加解密、OpenCV 滑块人机验证与高拟真运动学生成引擎。

## 一、 架构与设计说明

各业务功能提供独立 CLI 入口，底层共享协议客户端、签名、加解密和协议构造模块：

```text
各业务 CLI (login_cli.py / user_cli.py / fence_cli.py / record_cli.py / rank_cli.py / ai_sport_cli.py / run_cli.py)
    │
    ▼
统一 Client 门面 (client.py - ShanDongClient)
    │
    ├── 协议构造器 (protocol_builder.py - 轨迹/分段/运动学)
    ├── 密码学模块 (crypto.py - sign签名/AES加解密/MD5校验)
    ├── 验证码模块 (captcha_solver.py - OpenCV边缘匹配)
    └── 传输网络层 (transport.py - 请求组装/签名注入/ADB通道)
```

## 二、 项目文件清单

| 文件 | 类型 | 职责说明 |
| :--- | :--- | :--- |
| **`login_cli.py`** | 业务 CLI | 闪动校园 / 登录认证（密码隐式输入，OpenCV 自动秒过滑块并保存会话） |
| **`user_cli.py`** | 业务 CLI | 闪动校园 / 用户信息与状态（个人资料、学校信息、诚信学分） |
| **`fence_cli.py`** | 业务 CLI | 闪动校园 / 校园围栏与规则（查询校区多边形打卡边界与必经点） |
| **`record_cli.py`** | 业务 CLI | 闪动校园 / 跑步记录与统计（累计里程统计、阳光跑/自由跑分页明细） |
| **`rank_cli.py`** | 业务 CLI | 闪动校园 / 跑步排行榜（30天全校里程榜、达标进度榜） |
| **`ai_sport_cli.py`** | 业务 CLI | 闪动校园 / AI 运动（AI 动作分类、历史锻炼打卡记录） |
| **`run_cli.py`** | 业务 CLI | 闪动校园 / 模拟跑步打卡（基于校园围栏与运动学生成轨迹并完成打卡） |
| **`client.py`** | 统一门面 | 业务方法统一封装，返回标准数据字典 |
| **`crypto.py`** | 密码学 | `sign` 签名计算、AES-256-CBC 字段加解密、`runImgRecord` 校验码 |
| **`captcha_solver.py`** | 视觉适配 | OpenCV Canny 边缘轮廓匹配滑块缺口 |
| **`transport.py`** | 传输适配 | 请求签名组装、设备指纹注入、ADB/直连网络通道适配 |
| **`protocol_builder.py`**| 协议构造 | 多边形地理围栏判定（PIP）、拟真配速步频轨迹切片生成 |
| **`session_store.py`** | 会话存储 | 本地轻量级 `session.json` 会话持久化与加载 |

## 三、 安装依赖

```bash
pip install pycryptodome opencv-python numpy requests
```

## 四、 使用方法

### 1. 登录认证 (自动识别滑块通过)
```bash
# 交互式输入手机号与密码 (密码隐式输入)
python login_cli.py

# 命令行参数传参
python login_cli.py -p 手机号
```

### 2. 查询用户信息与状态
```bash
python user_cli.py
```

### 3. 查询校园电子围栏与打卡要求
```bash
python fence_cli.py
```

### 4. 查询跑步记录与累计数据
```bash
# 查看学期累计跑步总统计
python record_cli.py -t summary

# 查看阳光跑历史记录 (第 1 页)
python record_cli.py -t sun -p 1

# 查看自由跑历史记录
python record_cli.py -t free -p 1
```

### 5. 查询跑步排行榜
```bash
# 查询女生全校 30 天里程榜
python rank_cli.py -t distance -s 2

# 查询男生全校达标进度榜
python rank_cli.py -t progress -s 1
```

### 6. 查询 AI 运动项目与记录
```bash
# 查询 AI 动作项目分类
python ai_sport_cli.py -t categories

# 查询 AI 运动历史锻炼记录
python ai_sport_cli.py -t records -p 1
```

### 7. 模拟跑步打卡 (高拟真轨迹生成)
```bash
# 交互式输入距离
python run_cli.py

# 指定打卡 2.2 公里，配速 5分20秒/km (320秒)
python run_cli.py -d 2200 -p 320
```

## 五、 注意事项与防封规则

1. **固定设备指纹**：闪动校园后台严格限制单学期单账号绑定物理设备不得超过 **3 台**。工具箱底层已锁定首选真实设备指纹（`deviceId: 7a3f91c2d8e64b5fa104ce7392bd6e81`，机型: `SM|SM-A5460`）。
2. **免代理直连机制**：针对 PC 端代理环境易受服务端防火墙拦截的问题，传输层默认通过连接手机的 ADB 发送直连请求；在无代理网络环境下也可直接切换为标准 Python 直连模式。

