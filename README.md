# 闪动校园协议 CLI 工具箱

面向 **闪动校园 Android 客户端** 的纯 Python 协议工程化实现。

项目基于客户端网络通信与协议行为分析，将登录认证、用户信息、校园围栏、运动记录、排行榜、AI 运动及跑步相关协议拆分为独立 CLI，并通过统一协议层复用签名、加解密、验证码识别、网络传输、地理围栏与运动数据构造能力。

仓库采用 **按客户端版本独立维护** 的方式组织代码，不同版本之间互不污染，便于跟踪 App 更新带来的接口、签名及协议变化。

---

## 一、项目结构

仓库按照闪动校园客户端版本进行归档：

```text
com.huachenjie.shandong_school/
├── 8.6.8/
│   └── ...
├── 8.7.2/
│   └── ...
├── LICENSE
└── README.md
```

每个版本目录对应一次完整的协议分析结果。

当客户端更新并出现协议变化时，新版本会建立独立目录，而不是直接覆盖历史实现。

例如：

```text
8.6.8/
8.7.2/
8.x.x/
```

这样可以保留不同客户端版本之间的协议差异，也方便进行历史版本研究与对比。

---

## 二、设计思路

整体采用：

```text
业务 CLI
    │
    ▼
统一 Client 门面
    │
    ├── 协议构造
    ├── 签名 / 加解密
    ├── 验证码处理
    ├── 网络传输
    ├── 会话管理
    └── 地理 / 运动数据
```

不同业务功能保持独立入口：

```text
login_cli.py
user_cli.py
fence_cli.py
record_cli.py
rank_cli.py
ai_sport_cli.py
run_cli.py
```

底层公共能力统一复用，尽量避免：

```text
重复请求代码
重复签名代码
重复密码学实现
重复设备参数处理
重复协议字段构造
```

项目整体遵循：

```text
一个功能
    ↓
一个 CLI
    ↓
一个清晰入口
```

---

## 三、主要模块

不同版本的具体文件可能存在差异，典型结构如下：

| 模块                    | 作用                |
| --------------------- | ----------------- |
| `login_cli.py`        | 登录认证与会话初始化        |
| `user_cli.py`         | 用户信息及账户状态查询       |
| `fence_cli.py`        | 校园电子围栏与相关规则查询     |
| `record_cli.py`       | 运动记录及累计数据查询       |
| `rank_cli.py`         | 校园运动排行榜查询         |
| `ai_sport_cli.py`     | AI 运动项目及历史记录查询    |
| `run_cli.py`          | 跑步协议相关数据构造入口      |
| `client.py`           | 业务协议统一 Client 门面  |
| `crypto.py`           | 签名、AES、MD5 等密码学实现 |
| `captcha_solver.py`   | OpenCV 验证码图像处理    |
| `transport.py`        | HTTP 请求、协议头及网络传输  |
| `protocol_builder.py` | 坐标、围栏、轨迹及协议数据构造   |
| `session_store.py`    | 本地登录会话管理          |

具体实现请以对应版本目录中的代码为准。

---

## 四、环境

推荐：

```text
Python 3.10+
Windows / Linux / macOS
```

常用依赖：

```bash
pip install pycryptodome opencv-python numpy requests
```

部分版本或网络模式可能需要：

```text
ADB
Android 真机 / 模拟器
Root
LSPosed / Xposed
```

请根据对应版本实现选择运行环境。

---

## 五、使用方法

首先进入需要使用的客户端版本目录。

例如：

```bash
cd 8.7.2
```

之后运行对应业务 CLI。

### 登录

```bash
python login_cli.py
```

部分版本支持：

```bash
python login_cli.py -p 手机号
```

---

### 用户信息

```bash
python user_cli.py
```

---

### 校园围栏

```bash
python fence_cli.py
```

---

### 运动记录

```bash
python record_cli.py -t summary
```

阳光跑记录：

```bash
python record_cli.py -t sun -p 1
```

自由跑记录：

```bash
python record_cli.py -t free -p 1
```

---

### 排行榜

```bash
python rank_cli.py -t distance -s 2
```

或：

```bash
python rank_cli.py -t progress -s 1
```

---

### AI 运动

```bash
python ai_sport_cli.py -t categories
```

历史记录：

```bash
python ai_sport_cli.py -t records -p 1
```

---

### 跑步协议

```bash
python run_cli.py
```

部分版本支持直接指定运动参数：

```bash
python run_cli.py -d 2200 -p 320
```

其中：

```text
-d
```

表示目标距离。

```text
-p
```

表示配速参数。

具体参数请以对应版本 CLI 的 `--help` 与代码实现为准。

---

## 六、协议分析

本仓库中的协议实现来自对闪动校园 Android 客户端的：

```text
静态分析
        +
动态调试
        +
HTTPS 流量分析
        +
请求 / 响应字段对比
        +
客户端协议逻辑还原
```

典型流程：

```text
Android App
    │
    ▼
网络流量分析
    │
    ▼
请求 / 响应结构
    │
    ▼
签名与加密分析
    │
    ▼
客户端逻辑分析
    │
    ▼
协议字段还原
    │
    ▼
Pure Python
```

目标并不是简单复制某个 HTTP 请求，而是尽可能将协议涉及的：

```text
请求结构
签名
加密
验证码
会话
设备上下文
坐标
运动数据
```

拆分并重新实现为可维护的 Python 模块。

---

## 七、HTTPS 抓包

闪动校园部分网络请求存在 HTTPS 证书校验相关限制。

本项目分析过程中使用 **JustTrustMePro** 辅助处理 Android SSL Certificate Pinning，以便在授权测试环境中观察 HTTPS 网络通信。

项目：

`hang666 / JustTrustMePro`

JustTrustMePro 是一个基于 Xposed 的 Android SSL Certificate Pinning 测试工具，可 Hook 多种 Android HTTPS / SSL 校验逻辑，用于应用安全研究及调试环境下的加密流量分析。

典型环境：

```text
Android Device / Emulator
        │
        ├── Root
        ├── LSPosed / Xposed
        └── JustTrustMePro
                │
                ▼
          HTTPS Proxy
                │
                ▼
      Request / Response
                │
                ▼
       Protocol Analysis
```

本仓库不包含 JustTrustMePro 源代码或 APK。

请从其官方 GitHub 项目获取。

---

## 八、密码学与签名

客户端部分接口存在请求签名及加密字段。

相关实现集中在类似：

```text
crypto.py
```

的基础模块中。

典型调用关系：

```text
Business Parameters
        │
        ▼
Protocol Parameters
        │
        ▼
Encryption / Signature
        │
        ▼
HTTP Request
```

这样业务 CLI 无需直接维护复杂的签名与密码学代码。

---

## 九、验证码

部分登录流程包含滑块人机验证。

对应版本中可能使用：

```text
captcha_solver.py
```

处理验证码相关逻辑。

当前部分实现基于：

```text
OpenCV
Canny Edge
Template / Contour Matching
```

完成图像位置分析。

验证码属于独立适配层，不与业务 CLI 强耦合。

---

## 十、校园围栏与坐标

涉及校园运动协议时，需要处理学校配置的电子围栏及坐标数据。

相关逻辑通常集中在：

```text
protocol_builder.py
```

包括：

```text
Coordinate Validation

Polygon Fence

Point In Polygon

GPS Point

Distance

Pace

Step Frequency

Track Segment
```

坐标相关逻辑尽量通过统一的数据结构进行校验与传递，避免不同业务模块自行维护坐标处理代码。

---

## 十一、网络传输

网络请求由统一 Transport 层负责。

典型结构：

```text
Business CLI
     │
     ▼
Client
     │
     ▼
Transport
     │
     ├── Request Builder
     ├── Headers
     ├── Signature
     ├── Device Context
     └── Network Channel
```

根据不同版本和测试环境，可以存在：

```text
Python Direct Request
```

或：

```text
ADB / Android Network Channel
```

等不同网络适配方式。

设备参数不应硬编码为开发者个人真实设备信息。

---

## 十二、版本兼容

闪动校园客户端协议会随着 App 更新发生变化。

可能变化的内容包括：

```text
API Endpoint
Request Parameters
Headers
Signature
Encryption
Device Parameters
Captcha
Session
Run Protocol
```

因此本项目不声明不同 App 版本之间完全兼容。

使用时应选择与客户端对应的版本目录：

```text
App Version
     │
     ▼
Repository Version Directory
```

例如：

```text
8.6.8 → 8.6.8/
8.7.2 → 8.7.2/
```

如果新版客户端协议发生变化，将通过新增版本目录进行适配。

---

## 十三、隐私

公开仓库中不应包含真实用户的：

```text
手机号
密码
Token
Cookie
Session
Device ID
Android ID
IMEI
OAID
真实姓名
学校账号
真实 GPS 轨迹
个人运动记录
```

运行过程中产生的账号、会话及设备相关信息应仅保存在本地。

提交：

```text
Issue
Pull Request
Debug Log
Screenshot
```

之前，请自行检查并清除敏感信息。

---

## 十四、研究用途

本项目主要用于：

```text
Android Reverse Engineering

Network Protocol Analysis

Python Protocol Engineering

Application Security Research

Android HTTPS Traffic Analysis
```

以及本人设备、本人账号和明确授权环境中的测试研究。

请勿用于未经授权的数据访问、账号操作或其他违反相关法律法规及服务条款的行为。

---

## Credits

### JustTrustMePro

感谢 `hang666/JustTrustMePro`。

本项目在 Android HTTPS 协议分析阶段使用该项目辅助处理 SSL Certificate Pinning。

JustTrustMePro 的版权及源代码归原作者所有，本仓库不包含其代码。

---

## License

本项目基于 [MIT License](LICENSE) 开源。
