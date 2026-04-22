# Auto-rocokingdom 开发手册

本手册旨在指导开发者如何在重构后的架构下扩展功能。项目采用了 **事件总线 (Event Bus)** + **策略模式 (Strategy)** + **集中状态管理 (State Store)** 的架构，实现了检测逻辑与动作执行的完全解耦。

---

## 1. 架构概览

- **State (`src/state.py/BotState`)**: 唯一的全局状态源。
    - 记录当前状态 (`RobotState`) 和上一个有效状态 (`last_non_none_state`)。
    - **改进：移除粘性决策**。系统现在优先信任当前帧的实时分析结果，而非持久化之前的决策，从而实现更精准的状态修正。
- **Events (`src/events.py`)**: 定义系统中发生的信号。
    - `BattleDetectedEvent`: 提供检测到的全图、坐标、匹配分数等元数据。
- **Detector (`src/detector.py`)**: 感知层。
    - **全 SIFT 驱动**：使用 `vision.py` 提供的特征匹配函数定位图标，彻底抛弃了传统的像素缩放逻辑。实现真正分辨率无关。
- **Strategies (`src/strategies/`)**: 执行层。
    - **静默观察者（StatStrategy）**：演示了如何实现一个只记录数据而不产生任何物理交互的“统计模式”。
- **Bot (`src/bot.py`)**: 编排层。负责初始化组件、连接事件总线、启动主循环。

---

## 2. 核心机制：全场景 SIFT 与 状态机生命周期

### 分辨率无关性 (Resolution Independence)
在 2026/4/22 更新后，项目移除了 `ref_width` 和 `ref_height`。
- **原理**：SIFT 特征匹配对尺度和旋转具有不变性。无论游戏窗口是 1080P 还是 2K，识别算法都能在画面内锁定特征点，无需手动适配缩放比例。
- **开发者需知**：在添加新模板时，请尽量选择纹理丰富、对比度高的小图，以增加特征点数量。

### 实时状态分析流 (Real-time Analysis)
不同于早期的“一旦进入战斗就锁死状态”的逻辑，现在的状态机遵循以下循环：
1.  **逐帧捕获**：每隔 `poll_interval_sec` 截取一帧。
2.  **深度采样**：利用 SIFT 定位血条 ROI，提取中心区域的 **BGR 中值**（使用中值代替平均值以抵抗环境光干扰）。
3.  **距离计算**：计算测得颜色到所有 `hp_charge_targets`（蓄能目标，如粉色/紫色）和 `hp_escape_bgr`（逃跑目标，绿色）的最小欧氏距离。
4.  **状态修正 (Self-Correction)**：
    - 如果当前状态与实时颜色分析冲突（例如：当前为逃跑但在这一帧看到了确定的蓄能颜色），系统会立即**切换并修正**状态，以防止单帧遮挡或波动导致的决策错误。

---

## 3. 如何添加新功能？

扩展功能的典型工作流通常涉及以下四个步骤：

### 第一步：定义新事件 (Optional)
如果你需要一个新的信号（例如“血量低”或“任务完成”），在 `src/events.py` 中添加一个 `dataclass`。

```python
# src/events.py
@dataclass
class LowHealthEvent:
    percentage: float
    timestamp: float
```

### 第二步：添加检测逻辑 (New Condition)
在 `src/detector.py` 中识别新的画面特征，并发布事件。

1.  **修改检测逻辑**：在 `BattleDetector.process_frame` 中，通过 `vision.detect_state_icon` 分析图像。
2.  **触发事件**：当条件满足时，通过 `self.event_bus.publish()` 发布事件。

### 第三步：创建新的动作策略 (New Strategy)
在 `src/strategies/` 目录下创建一个新文件（如 `stat.py`）。

1.  **继承自 `ActionStrategy`**。
2.  **实现 `on_battle_detected` 回调**。

### 第四步：注册到工厂
为了让用户能选到这个新模式，需要在 `src/strategies/__init__.py` 的工厂函数中进行注册。并在 `src/bot.py` 的 `prompt_mode` 中给用户添加一个选项。

---

## 4. 最佳实践建议

1.  **不要在 Strategy 里写复杂的检测**：Strategy 应该是“盲目”的执行者。它只通过 `Event` 拿数据，通过 `State` 看状态。
2.  **保持 Detector 纯净**：Detector 只负责识别和发信号，永远不要在 Detector 里调用 `press_once` 或 `click_at`。
3.  **使用 `log_audit`**：在 Strategy 执行动作时，调用 `src.utils.log_audit` 记录事件，方便用户复盘。
4.  **组合优于继承**：如同 `SmartStrategy` 那样，可以通过组合现有的 `BattleStrategy` 和 `EscapeStrategy` 来实现更复杂的行为。

---

## 5. 调试建议 (2026/4/22 新增)

- **BGR 追踪**：通过 `runtime.log` 中的 `Match Info` 查看血条的实时颜色取值。
- **距离调试**：查看 `dist_valid` 与 `dist_escape` 的比值。如果两者距离接近，说明环境光或背景噪音干扰较大，可能需要收紧 `hp_color_tolerance`（容差）。
- **SIFT 调试**：开启 `debug_save_images = True`，系统会自动将匹配到的 SIFT 结果（带红色选区框）保存至 `logs/debug_images` 目录下，用于确认定位是否准确。
