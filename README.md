# VisionFlow Agent

> **VisionFlow Agent** 是一个专为桌面端设计的**通用视觉感知自动化代理**。它旨在打破传统软件自动化的边界，通过非侵入式的计算机视觉技术，为任何无 API 支持的应用提供“感知-编排-执行”的完整 Agent 能力。

---

## 📖 关于项目 (About)

在数字化办公与复杂软件交互的场景中，许多遗留软件（Legacy Software）和封闭平台缺乏开放的 API 接口，导致自动化流程难以触达。**VisionFlow Agent** 的诞生正是为了解决这一痛点。

本项目不仅是一个工具，更是一个**动作代理（Action Agent）**的实验性框架：
*   **视觉即接口**：通过像素级的特征分析（SIFT/Template Matching），将屏幕画面抽象为可编程的状态机。
*   **无代码编排**：内置可视化生命周期管理器，让非开发人员也能通过拖拽式逻辑定义复杂的跨应用流程。
*   **异步解耦**：采用生产级的事件总线架构，确保在执行高频自动化任务时保持极高的响应速度与系统稳定性。

我们致力于打造一个轻量、高效且易于扩展的桌面端“数字员工”内核，目前已作为核心组件参与小米 Agent 计划的探索与验证。


**VisionFlow Agent** 是一个基于计算机视觉（CV）的桌面级通用自动化编排代理。它采用完全解耦的“感知-决策-执行”架构，允许用户通过无代码（No-Code）的图形界面，定义基于视觉特征锚点（Visual Anchors）的屏幕自动化任务序列。

该项目特别适合为**无 API 接口的遗留系统**、**复杂桌面应用** 或 **第三方封闭软件** 提供低门槛的自动化解决方案。

## 🌟 核心特性 (Key Features)

* **感知与执行解耦 (Decoupled Architecture)**
  核心采用标准的 EventBus 观察者模式。`VisionOrchestratorDetector`（感知层）仅负责分析屏幕像素并发布状态变更事件；`ActionStrategy`（执行层）仅负责订阅事件并调度对应的任务序列，两者互不依赖。
* **通用视觉锚点匹配 (Universal Vision Anchors)**
  采用 **SIFT (Scale-Invariant Feature Transform)** 等多维特征匹配算法，实现**物理分辨率无关**的图像识别。无论是 1080p、4K 还是自由缩放的窗口，Agent 都能精准锁定目标特征。
* **低代码可视化编排 (Low-Code Orchestrator)**
  内置 React 驱动的图形化编排前端，支持将复杂流程拆解为 `Idle`（空闲）、`Lifecycle A/B/C`（不同特征触发）等多个生命周期状态。用户可通过拖拽和配置，实现键盘、鼠标点击、延时、条件循环等跨应用任务。
* **高鲁棒性状态机 (Robust State Machine)**
  底层维护了一个严格的 `AgentState` 显式状态机，具备**逐帧自纠正**机制，确保在复杂的 UI 干扰下也能保持逻辑稳定，防止误触发。
* **全后台运行支持 (Background Execution)**
  支持窗口遮挡情况下的后台图像识别与按键注入（具体视目标应用程序的句柄响应而定），无需全程霸占主屏幕。

---

## 🛠️ 技术栈 (Tech Stack)

* **核心引擎 (Core)**: Python 3.10+
* **计算机视觉 (Vision)**: OpenCV (SIFT, Template Matching), NumPy
* **系统交互 (OS Interop)**: `ctypes` (Win32 API), `pywin32`
* **前端编排器 (Frontend)**: React, Framer Motion, Lucide-React
* **配置管理 (Config)**: JSON, Pydantic

---

## 🚀 快速开始 (Quick Start)

### 1. 启动后端 Agent 引擎
```bash
# 激活虚拟环境并安装依赖
pip install -r requirements.txt

# 启动核心代理与 Web API 服务
python main.py
```

### 2. 启动前端 Orchestrator 面板
```bash
cd frontend
npm install
npm run dev
```

### 3. 配置你的生命周期任务
打开浏览器访问 `http://localhost:5173`。
1. 在 **空闲状态 (Idle)** 下配置 Agent 找不到任何特征时的默认动作（如：定时巡检、滚动屏幕）。
2. 在 **特征匹配状态 A/B** 下配置当屏幕出现特定 UI 元素（如弹窗、特定按钮、警告色块）时应该执行的动作流。
3. 保存配置，Agent 将自动热重载并开始工作！

---

## 📅 演进与计划 (Roadmap)

* [x] **架构解耦**：完成感知层与动作层的 EventBus 分离。
* [x] **SIFT 引入**：摆脱传统的静态模板匹配，实现尺度不变的特征锚点定位。
* [x] **生命周期编排器**：完成前端 React 编排面板，实现多分支状态调度。
* [ ] **动态锚点训练 (WIP)**：计划引入轻量级 VLM（视觉语言模型），让用户可以通过自然语言框选和定义视觉特征，实现从“手动截取特征图”到“语义理解 UI”的跨越。
* [ ] **跨平台支持 (WIP)**：抽象系统交互层，支持 macOS (Accessibility API) 与 Linux (X11/Wayland)。

---

## ⚠️ 声明 (Disclaimer)

本项目仅作为“计算机视觉与代理架构”的学术/技术交流产物。在使用本工具自动化操作第三方软件时，请务必遵守目标软件的用户服务协议。开发者不对因滥用本工具造成的任何后果负责。