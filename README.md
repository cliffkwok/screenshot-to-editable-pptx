# Screenshot → Editable PPTX

端到端 pipeline：任何截圖 → 100% 可編輯、群組化、可縮放的 PowerPoint 投影片。

## Pipeline v2

```
截圖 → [editppt OCR] → [python-pptx 重建] → [SYSTEM.md 驗證] → [Step 10 diff]
```

## 測試結果 (Single Agent)

| Step | 狀態 |
|------|------|
| editppt OCR | ✅ 1 page, text hints |
| python-pptx 重建 | ✅ 12 text + 11 graphic regions |
| SYSTEM.md 驗證 | ✅ **8/10 rules passing** |
| Step 10 diff | ⚠ 手動 vision 比對 |

## 快速開始

```bash
# 1. 安裝依賴
bash config/setup.sh

# 2. 設定 API
editppt config --paddle-ocr-token <token>
editppt config --api-key <key> --base-url <url> --model <model>

# 3. 執行
bash pipeline.sh <project_name> <screenshot.png>
```

## SYSTEM.md 規則庫

10 個通用量測步驟 + 31 條修正規則 (A-AE)，每次修正寫入規則。

| 類別 | 規則數 | 涵蓋 |
|------|--------|------|
| 量測 | Steps 1-4 | 容器/顏色/比例/文字大小 |
| 形狀 | Rules AB-AD | shape type 驗證, 組合形狀 |
| 文字 | Rules AC-AH | 對齊, 垂直位置, SHAPE_TO_FIT_TEXT |
| 陰影 | Rule S | flat design 禁用 |
| 線條 | Rules T-AF | 顏色/箭頭/LINE→RECTANGLE |
| 自檢 | Steps 9-10, Rules AA-V | diff, 結構化比對, close-up 取證 |

## 工具組合

| 層 | 工具 | 角色 |
|----|------|------|
| 1. OCR | editppt + PaddleOCR | 文字定位、字型 |
| 2. 重建 | python-pptx + SYSTEM.md | 形狀、顏色、位置 |
| 3. 圖標 | svg2pptx | SVG → 可編輯形狀 |
| 4. 美化 | ppt-master | 模板、動畫 |
| 5. 驗證 | SYSTEM.md | 自檢 diff |

## 授權

MIT