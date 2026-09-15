# Screenshot → Editable PPTX

端到端 pipeline：截圖 → 100% 可編輯、群組化、可縮放的 PowerPoint 投影片。

## v1.0.0 — 首次發布

### 核心方法

```
截圖 → SYSTEM.md 量測 → python-pptx 重建 → 自檢驗證
```

**不依賴雲端 API**，本地執行。10 步驟 + 32 條規則的 SYSTEM.md 是此專案的核心 IP。

### 範例輸出

| 範例 | 原始截圖 | 可編輯 PPTX | 元素數 | 位置偏差 |
|------|---------|-------------|--------|---------|
| [ADK agent workflow](examples/adk-workflow/) | 7 cards | ✅ | 42+ shapes | <3% |
| Single Agent | 1 page | ✅ | 20+ shapes | 已驗證 |

### 驗證結果 (ADK workflow)

```
✅ 7/7 cards 完整
✅ PIL 取色: #4583EC #F5C144 #DD3A33
✅ Vision pixel 驗證: 卡片位置偏差 <3%
✅ 文字無斷行 (r=0.28", Pt(6))
✅ shadow.inherit=False 扁平設計
```

### 快速開始

```bash
# 1. 安裝依賴
python3 -m pip install python-pptx Pillow

# 2. 執行範例
cd examples/adk-workflow
python3 ../../projects/adk-workflow/reconstruct_run.py

# 3. 自訂截圖 → 依 SYSTEM.md 規則建構
```

### SYSTEM.md — 通用量測法

| Step | 功能 |
|------|------|
| 1-4 | 容器/顏色/比例/文字 |
| 5-7 | 形狀/陰影/圖標 |
| 8-10 | 文字適配/自檢/diff |
| A-AH | 32 條修正規則 |

### 探索過的方法

| 方法 | 狀態 | 原因 |
|------|------|------|
| OpenCV HoughCircles | ❌ | 圖表太複雜 |
| OpenCV HSV masking | ❌ | 雜訊多 |
| SiliconFlow Qwen3-VL | ❌ | 網路被封 |
| RapidLayout (ONNX) | ❌ | 文件版面，非形狀 |
| **SYSTEM.md + python-pptx** | ✅ | 本地、精準、可重複 |

### 下一步

- 整合本地 ONNX 圖表形狀偵測模型（需訓練）
- 加入 ppt-master SVG→PPTX grouping
- 批次處理多張截圖

### 授權

MIT