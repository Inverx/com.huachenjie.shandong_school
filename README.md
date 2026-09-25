# 闪动校园协议工程

<p align="center">
  <b>Shandong School · Android Protocol Analysis & Reverse Engineering</b>
</p>

<p align="center">
  面向「闪动校园」Android 客户端的协议分析、逆向研究与工程化实现。
</p>

---

## Telegram

> 项目更新、版本适配及相关通知优先通过 Telegram 发布。

###  通知频道

**Telegram Channel：**  
https://t.me/Inverx200

用于发布：

- 项目更新
- 新版本适配
- Release 发布
- 协议变化通知
- LSPosed 模块更新
- 重要公告

###  讨论群

**Telegram Group：**  
https://t.me/Inverx501

用于：

- 问题交流
- Bug 反馈
- Android 逆向讨论
- 协议分析交流
- LSPosed / Xposed 相关讨论

也可以直接通过 GitHub Issues 提交可复现的问题。

---
## 项目简介

本项目面向 **闪动校园 Android 客户端**，主要用于 Android 逆向、网络协议分析及相关工程化研究。

通过对客户端的：

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

逐步还原客户端相关网络通信逻辑，并将部分协议能力重新实现为可独立运行、便于维护和分析的 Python 工具。

项目目前主要包含两部分：

```text
Protocol CLI
+
LSPosed Hook Modules
```

其中协议实现按照 **App 客户端版本独立维护**，避免不同版本之间的协议差异互相污染。

---

## 项目结构

```text
com.huachenjie.shandong_school/
│
├── 8.6.8/
│   └── 闪动校园 8.6.8 协议实现
│
├── 8.7.2/
│   └── 闪动校园 8.7.2 协议实现
│
├── Lsposed-modules-Hook/
│   └── LSPosed / Xposed Hook 模块相关内容
│
├── LICENSE
└── README.md
```

### 版本目录

每个版本目录对应一次相对独立的客户端协议分析结果。

例如：

```text
8.6.8  →  8.6.8/
8.7.2  →  8.7.2/
8.x.x  →  8.x.x/
```

当客户端更新并出现：

```text
API Endpoint
Request Parameters
Headers
Signature
Encryption
Device Parameters
Captcha
Session
Protocol Logic
```

等变化时，将优先通过建立新的版本目录进行适配，而不是直接覆盖历史实现。

这样可以保留不同 App 版本之间的协议差异，也方便后续进行版本对比与研究。

---

## 功能

不同版本实现可能存在差异，目前项目涉及的主要能力包括：

| 模块 | 功能 |
|---|---|
| `login_cli.py` | 登录认证与会话初始化 |
| `user_cli.py` | 用户信息与账户状态查询 |
| `fence_cli.py` | 校园电子围栏及相关配置查询 |
| `record_cli.py` | 运动记录及累计数据查询 |
| `rank_cli.py` | 校园运动排行榜查询 |
| `ai_sport_cli.py` | AI 运动项目及历史记录查询 |
| `run_cli.py` | 运动协议相关数据构造与研究入口 |
| `client.py` | 统一业务 Client 门面 |
| `crypto.py` | 签名、AES、MD5 等密码学实现 |
| `captcha_solver.py` | 验证码图像处理 |
| `transport.py` | HTTP 请求与网络传输 |
| `protocol_builder.py` | 坐标、围栏、轨迹及协议数据构造 |
| `session_store.py` | 本地登录会话管理 |

具体文件及功能请以对应版本目录中的代码为准。

---

## 设计思路

项目并不是简单保存某个 HTTP 请求，而是尽可能将客户端网络协议拆分为可维护的工程结构。

```text
                    Business CLI
                         │
                         ▼
                       Client
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
 Protocol Builder      Crypto         Session
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
                     Transport
                         │
                         ▼
                     Network
```

业务 CLI 尽量只处理业务入口。

底层公共能力统一负责：

```text
协议字段构造
签名
加解密
验证码
Session
网络传输
设备上下文
坐标处理
运动数据结构
```

整体遵循：

```text
一个功能
   ↓
一个 CLI
   ↓
一个清晰入口
```

减少重复请求代码、重复签名逻辑以及不同业务模块之间的强耦合。

---

## 环境

推荐环境：

```text
Python 3.10+
Windows / Linux / macOS
```

常用 Python 依赖：

```bash
pip install pycryptodome opencv-python numpy requests
```

部分研究场景可能还需要：

```text
ADB
Android 真机 / 模拟器
Root
LSPosed / Xposed
```

具体环境要求请以对应版本代码为准。

---

# 快速开始

## 1. Clone

```bash
git clone https://github.com/Inverx/com.huachenjie.shandong_school.git
```

进入项目：

```bash
cd com.huachenjie.shandong_school
```

---

## 2. 选择客户端版本

例如：

```bash
cd 8.7.2
```

请尽量选择与目标客户端一致的版本目录。

---

## 3. 登录

```bash
python login_cli.py
```

部分版本支持：

```bash
python login_cli.py -p 手机号
```

具体参数：

```bash
python login_cli.py --help
```

---

## 4. 用户信息

```bash
python user_cli.py
```

---

## 5. 校园围栏

```bash
python fence_cli.py
```

---

## 6. 运动记录

汇总信息：

```bash
python record_cli.py -t summary
```

阳光跑：

```bash
python record_cli.py -t sun -p 1
```

自由跑：

```bash
python record_cli.py -t free -p 1
```

---

## 7. 排行榜

例如：

```bash
python rank_cli.py -t distance -s 2
```

或：

```bash
python rank_cli.py -t progress -s 1
```

---

## 8. AI 运动

查询项目：

```bash
python ai_sport_cli.py -t categories
```

查询历史记录：

```bash
python ai_sport_cli.py -t records -p 1
```

---

## 9. 运动协议

```bash
python run_cli.py
```

部分版本支持通过 CLI 指定协议参数。

例如：

```bash
python run_cli.py -d 2200 -p 320
```

不同版本参数可能发生变化，请优先查看：

```bash
python run_cli.py --help
```

以及对应版本源码。

---

# LSPosed Hook Modules

仓库同时维护：

```text
Lsposed-modules-Hook/
```

用于存放与本项目研究相关的 **LSPosed / Xposed Hook 模块**。

这部分主要服务于 Android 动态分析、调试及协议研究场景。

典型环境：

```text
Android Device / Emulator
        │
        ├── Root
        │
        ├── Magisk / Kitsune Mask
        │
        └── LSPosed
                │
                ▼
           Hook Module
                │
                ▼
          Target Process
```

模块的：

```text
APK
Version
Target App Version
Compatibility
Usage
```

请以对应目录及 GitHub Releases 中的说明为准。

---

# HTTPS 流量分析

部分 Android 网络请求可能存在：

```text
SSL Certificate Pinning
```

等证书校验机制。

在授权研究环境中，可以结合：

```text
Android Device / Emulator
        │
        ├── Root
        ├── LSPosed / Xposed
        └── SSL Pinning Research Module
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

进行客户端网络通信分析。

本项目研究过程中曾使用：

**hang666 / JustTrustMePro**

辅助分析 Android SSL Certificate Pinning。

相关项目版权及源代码归原作者所有，本仓库不包含其源代码或 APK。

---

# 协议分析流程

项目中协议实现通常来源于以下分析流程：

```text
Android APK
    │
    ▼
Static Analysis
    │
    ▼
Dynamic Analysis
    │
    ▼
Network Traffic
    │
    ▼
Request / Response
    │
    ▼
Signature / Encryption
    │
    ▼
Application Logic
    │
    ▼
Protocol Reconstruction
    │
    ▼
Python Implementation
```

最终尽可能将：

```text
Request
Signature
Encryption
Captcha
Session
Device Context
Coordinate
Protocol Data
```

拆分并重新实现为相互独立的模块。

---

# 验证码

部分认证流程可能包含滑块等人机验证机制。

相关版本中可能存在：

```text
captcha_solver.py
```

用于验证码图像分析。

部分实现涉及：

```text
OpenCV
Canny Edge
Template Matching
Contour Matching
```

验证码处理作为独立适配层存在，避免与核心业务代码强耦合。

---

# 坐标与电子围栏

涉及校园运动协议研究时，需要处理客户端中的坐标及电子围栏数据。

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
Track Segment
```

坐标尽量通过统一数据结构进行校验与传递，避免不同业务模块分别维护相同逻辑。

---

# 隐私与数据安全

请 **不要** 将真实用户敏感信息提交到公开仓库。

包括但不限于：

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
个人运动数据
```

运行过程中生成的账号、Session、设备参数及调试信息应尽量只保存在本地。

提交以下内容之前：

```text
Issue
Pull Request
Debug Log
Screenshot
HAR
抓包文件
```

请自行检查并删除其中可能存在的个人信息、认证信息及设备标识。

---

# Issue / Pull Request

欢迎提交：

```text
Bug Report
Protocol Change
Version Compatibility
Code Improvement
Documentation
Reverse Engineering Research
```

如果客户端更新导致协议失效，建议 Issue 中至少提供：

```text
App Version
Android Version
Python Version
Error Message
Minimal Reproduction
```

请不要在 Issue 中公开：

```text
账号
密码
Token
Cookie
完整 Session
个人身份信息
```

---

# Telegram

项目更新：

**https://t.me/Inverx200**

技术讨论：

**https://t.me/Inverx501**

如果发现新版本协议变化、兼容性问题或项目 Bug，也可以通过 GitHub Issues 反馈。

---

# Research & Disclaimer

本项目主要用于：

```text
Android Reverse Engineering
Network Protocol Analysis
Python Protocol Engineering
Application Security Research
Android HTTPS Traffic Analysis
LSPosed / Xposed Research
```

以及本人设备、本人账号或获得明确授权环境中的安全研究与技术学习。

请遵守所在地法律法规、目标服务的相关规则及授权范围。

请勿将本项目用于未经授权的账号访问、数据获取、系统操作或其他侵犯第三方权益的行为。

使用者应自行承担因使用、修改或分发本项目所产生的责任。

---

# Credits

### JustTrustMePro

感谢：

```text
hang666 / JustTrustMePro
```

本项目在 Android HTTPS 协议分析过程中参考或使用相关工具辅助研究 SSL Certificate Pinning。

其版权及源代码归原作者所有。

---

# License

本项目基于 **MIT License** 开源。

详见：

```text
LICENSE
```

---

<p align="center">
  <b>Android Reverse Engineering · Protocol Analysis · LSPosed</b>
</p>

<p align="center">
  <a href="https://t.me/Inverx200">Telegram Channel</a>
  ·
  <a href="https://t.me/Inverx501">Telegram Group</a>
  ·
  <a href="https://github.com/Inverx/com.huachenjie.shandong_school/issues">Issues</a>
</p>
