# 闪动校园 Android Hook 工程

<p align="center">
  <b>Shandong School · Android Reverse Engineering & LSPosed Hook</b>
</p>

<p align="center">
  面向「闪动校园」Android 客户端的逆向分析、模拟器环境研究与 LSPosed Hook 模块。
</p>

---

## Telegram

> 项目更新、版本适配及相关通知优先通过 Telegram 发布。

### 通知频道

**Telegram Channel：**

`@Inverx200`

用于发布：

- 项目更新
- 新版本适配
- Release 发布
- Hook 模块更新
- 兼容性变化
- 重要公告

### 讨论群

**Telegram Group：**

`@Inverx501`

用于：

- 问题交流
- Bug 反馈
- Android 逆向讨论
- LSPosed / Xposed 相关讨论
- 模块兼容性交流

也可以直接通过 GitHub Issues 提交可复现的问题。

---

## 项目简介

本项目面向 **闪动校园 Android 客户端**，主要用于 Android 逆向、模拟器环境分析及 LSPosed Hook 技术研究。

本项目早期曾包含客户端网络协议分析及 Python 协议实现。

目前已经：

```text
移除早期协议部分
        ↓
停止维护 Python CLI
        ↓
仅保留 Android Hook 相关内容
        ↓
按客户端版本独立维护 LSPosed Hook 模块
```

当前项目主要用于：

```text
Android Reverse Engineering
+
Dynamic Analysis
+
Runtime Observation
+
LSPosed / Xposed Hook
+
Android Emulator Research
+
Version Compatibility Analysis
```

项目不再维护早期脱离 Android 客户端运行的网络协议实现。

---

## 项目结构

```text
com.huachenjie.shandong_school/
│
├── 8.7.2/
│   └── 闪动校园 8.7.2 Hook 模块
│
├── 8.7.4/
│   └── 闪动校园 8.7.4 Hook 模块
│
├── 8.7.7/
│   └── 闪动校园 8.7.7 Hook 模块
│
├── LICENSE
└── README.md
```

### 版本目录

每个版本目录对应一个相对独立的客户端版本。

例如：

```text
8.7.2  →  8.7.2/
8.7.4  →  8.7.4/
8.7.7  →  8.7.7/
8.x.x  →  8.x.x/
```

不同客户端版本之间可能存在：

```text
Class
Method
Field
Package
Runtime Logic
```

等差异。

因此模块按照客户端版本独立维护，避免不同版本之间的 Hook 逻辑互相影响。

请尽量使用与目标客户端版本一致的模块。

---

## LSPosed Hook

本项目目前主要维护：

```text
Android Device / Emulator
        │
        ├── Root
        │
        └── LSPosed
                │
                ▼
           Hook Module
                │
                ▼
          Target Process
```

模块主要服务于：

```text
Android Dynamic Analysis
Runtime Observation
Hook Research
Application Security Research
```

具体 Hook 内容、兼容版本及使用方式请以对应版本目录中的代码及 Release 说明为准。

---

## 使用环境

推荐环境：

```text
Android Emulator
Root
LSPosed
```

部分环境可能使用：

```text
Magisk
Kitsune Mask
```

具体 Root 方案及 Android 版本不做统一限制，以对应模块实际兼容情况为准。

---

## 使用方式

一般使用流程：

```text
安装目标客户端
        ↓
安装对应版本 Hook Module
        ↓
LSPosed 启用模块
        ↓
选择目标应用作用域
        ↓
重启目标应用
        ↓
观察 Hook 运行结果
```

请注意：

```text
客户端版本 ≠ 模块版本
```

并不代表可以跨版本直接使用。

如果模块无法正常工作，请首先确认：

```text
App Version
Android Version
Root Environment
LSPosed Version
Module Version
```

---

## 逆向研究流程

本项目相关模块通常来源于以下研究流程：

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
Runtime Observation
    │
    ▼
Hook Point
    │
    ▼
Module Implementation
    │
    ▼
Version Verification
```

尽可能将具体研究内容拆分为：

```text
Target Class
Target Method
Hook Logic
Runtime Data
Version Compatibility
```

减少不同版本之间的耦合。

---

## 隐私与数据安全

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
真实 GPS 数据
个人运动数据
```

运行过程中产生的：

```text
Debug Log
Screenshot
配置文件
设备参数
账号信息
```

应尽量只保存在本地。

提交以下内容之前：

```text
Issue
Pull Request
Debug Log
Screenshot
```

请自行检查并删除其中可能存在的个人信息、认证信息及设备标识。

---

## Issue / Pull Request

欢迎提交：

```text
Bug Report
Version Compatibility
Hook Research
Code Improvement
Documentation
Reverse Engineering Research
```

如果模块无法正常工作，建议至少提供：

```text
App Version
Android Version
LSPosed Version
Module Version
Error Message
Relevant Log
Minimal Reproduction
```

请不要在 Issue 中公开：

```text
账号
密码
Token
Cookie
Session
个人身份信息
设备唯一标识
```

---

# 免责声明与使用限制

> **重要提示：** 在使用、复制、修改或分发本仓库中的任何代码、模块或文档前，请务必仔细阅读以下内容。

## 核心声明

```text
1. 本项目仅维护 Android 模拟器 / Root 环境下的 LSPosed Hook 模块
2. 早期 Python 网络协议部分已经移除，不再维护
3. 严禁利用本项目进行商业接单、有偿代跑、倒卖或付费引流
4. 官方联系后将第一时间停止维护，并归档或下架仓库
```

---

## 一、项目维护与研究范围

### 1. 维护方向

本仓库已经移除早期脱离 Android 客户端运行的网络协议部分。

目前及后续仅维护：

```text
Android Reverse Engineering
Android Emulator Analysis
LSPosed / Xposed Hook
Mobile Application Security Research
```

不再提供早期 Python 协议部分的更新、适配及技术支持。

### 2. 研究目的

本项目仅用于：

```text
Android 逆向技术学习
动态 Hook 技术研究
模拟器环境分析
移动应用安全研究
```

本项目仅限在本人合法所有的设备、本地模拟器或已经获得明确授权的测试环境中使用。

---

## 二、严禁商业接单与非法牟利

本项目为免费开源的技术研究项目。

严禁任何个人、团队、工作室或组织利用本项目，包括但不限于：

```text
源码
编译后的 APK
修改版本
衍生版本
```

进行以下行为：

- 商业接单
- 收费代跑
- 按次收费
- 包月收费
- 商业代运营
- 倒卖源码
- 倒卖编译产物
- 付费引流
- 建立收费群
- 付费教程捆绑
- 其他直接或间接的商业牟利行为

对于违反上述使用限制的行为，均属于使用者个人行为，与本项目作者无关。

由此产生的法律纠纷、账号问题、经济损失及其他责任，由实际使用者自行承担。

---

## 三、官方联系与停更机制

本项目旨在进行 Android 逆向与 Hook 技术研究，无意破坏目标软件的正常业务运营秩序。

本项目尊重目标软件开发团队及相关权利人的：

```text
知识产权
合法权益
正常运营
```

如果软件官方或相关权利人认为本项目的存在对软件正常运营产生不当影响，并与本人取得联系：

```text
收到通知
    ↓
停止维护
    ↓
停止版本适配
    ↓
停止 Release 更新
    ↓
归档或下架仓库
```

本人将第一时间无条件配合。

---

## 四、免责条款

### 合规使用

使用者必须自行遵守：

```text
所在国家或地区法律法规
所在高校规章制度
目标软件用户协议
目标环境授权范围
```

### 禁止滥用

严禁将本项目用于：

```text
未经授权访问他人账号
未经授权获取他人数据
破坏计算机信息系统
干扰目标服务器正常运行
侵犯第三方合法权益
其他违法或违规行为
```

### 风险自担

本项目按：

```text
AS-IS
```

形式提供，不附带任何明示或暗示的担保。

使用者应自行承担因下载、安装、使用、修改或分发本项目产生的一切风险，包括但不限于：

```text
客户端闪退
数据异常
账号封禁
设备异常
校规处分
经济损失
法律责任
```

本项目作者及贡献者不对因使用本项目产生的任何直接或间接损失承担责任。

---

# 赞赏与感谢

开源项目的持续研究与维护离不开社区朋友的鼓励。

特别感谢：

| 赞赏者 | 致谢说明 |
| :---: | :---: |
| **VXiok** | 感谢对本项目的赞赏与支持 |

也感谢所有提交 Issue、Pull Request、测试反馈及技术交流的朋友。

---

# Credits

## JustTrustMePro

```text
hang666 / JustTrustMePro
```

感谢原作者开源的优秀工具。

本项目早期 Android 动态调试与 HTTPS Certificate Pinning 分析过程中，曾参考或使用相关工具辅助研究。

其相关版权及源代码归原作者所有。

本仓库不包含其源代码。

---

# License

本项目的许可证文件见：

```text
LICENSE
```

具体许可条款请以仓库中的 LICENSE 文件为准。

---

<p align="center">
  <b>Android Reverse Engineering · LSPosed · Mobile Security Research</b>
</p>

<p align="center">
  Telegram Channel · Telegram Group · GitHub Issues
</p>
