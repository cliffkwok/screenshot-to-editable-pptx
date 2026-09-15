# Screenshot → Editable PPTX

端到端 pipeline：任何截圖 → 100% 可編輯、群組化、可縮放、文字自適應的 PowerPoint 投影片。

## Pipeline

```
截圖 → [editppt 重建] → [svg2pptx 圖標] → [ppt-master 美化] → [SYSTEM.md 驗證]
```

| 層 | 工具 | 角色 |
|----|------|------|
| 1. OCR + 量測 | editppt + PaddleOCR | 文字定位、字型、顏色 |
| 2. 結構重建 | editppt prepare/run | 形狀重建、分層 |
| 3. 圖標複製 | svg2pptx | SVG → PPT 可編輯形狀 |
| 4. 美化 | ppt-master (Beautify) | 品牌模板、動畫 |
| 5. 驗證 | SYSTEM.md | 自檢 diff、比例驗證 |

## 快速開始

```bash
# 1. 安裝依賴
bash config/setup.sh

# 2. 設定 API
editppt config --paddle-ocr-token <token>
editppt config --api-key <key> --base-url <url> --model <model>

# 3. 執行
bash pipeline.sh <screenshot.png>
```

## 為什麼這些工具一起用

| 工具 | 強項 | 互補 |
|------|------|------|
| **editppt** | 截圖→結構化重建（最精準） | ppt-master 補美化 |
| **ppt-master** | 模板/美化/動畫 | editppt 補重建 |
| **svg2pptx** | SVG → 可編輯形狀 | 兩者都可用 |
| **SYSTEM.md** | 通用量測法 10 steps + 31 rules | 品質保證 |

## 規則庫

所有量測、複製、驗證規則集中在 [SYSTEM.md](SYSTEM.md)。每次修正都寫入規則，確保下次不重複犯錯。

## 授權

MIT