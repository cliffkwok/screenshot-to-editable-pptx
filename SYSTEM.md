# 通用截圖量測法

適用於**任何**截圖。不依賴特定設計，只描述量測方法。

---

## 步驟 1: 識別容器與子元素

Vision 分析回答兩個問題：
1. **容器是什麼？**（卡片、面板、區塊）→ 找出它的邊界
2. **子元素有哪些？**（badge、圖標、文字、按鈕、線條）→ 列出清單

PIL 掃描確認容器邊界（找連續的白色/純色區塊）。

## 步驟 2: 提取顏色

對每個子元素，PIL 在該區域中心取樣一次：
```
r, g, b = img.getpixel((center_x, center_y))[:3]
hex = f"#{r:02X}{g:02X}{b:02X}"
```
不靠 vision 猜 hex。不掃全圖。

## 步驟 3: 量測尺寸與位置（比例法）

對每個子元素：
```
element_x% = (element_x - container_x) / container_width × 100
element_y% = (element_y - container_y) / container_height × 100
element_w% = element_width / container_width × 100
element_h% = element_height / container_height × 100
```
所有值都是**相對於容器的百分比**。

PPT 中轉換：
```
ppt_x = container_x + element_x% × container_width
ppt_y = container_y + element_y% × container_height
ppt_w = element_w% × container_width
ppt_h = element_h% × container_height
```

## 步驟 4: 文字大小（比例鏈）

不獨立設字型大小。Vision 分析給出文字間的**比例關係**：
```
header_size : badge_text : card_name : tagline = a : b : c : d
```
若 header = 14pt，則 card_name = 14 × c/a pt。

## 步驟 5: 形狀類型

Vision 分析判斷每個元素的形狀類型：
- pill (radius = 0.5)
- rounded square (radius = 0.1-0.2)
- circle (oval, w == h)
- rectangle (radius = 0.03-0.08)
- line (thin rect, 2-4pt height)

不在程式碼中預設形狀類型。

## 步驟 6: 陰影檢測

Vision 逐元素回答：「有陰影 / 無陰影」。
有陰影的才加 shadow()。不預設任何形狀有陰影。

## 步驟 7: 圖標佔位符

無法複製真實圖標 → 同尺寸白色圓角方塊 + 字母標記。
尺寸和位置與原始一致，用戶可自行替換。

## 步驟 8: 文字適配

```
textbox_w ≥ 元素寬度（讓文字不超出邊界）
若文字可能過長 → tf.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
```

## 步驟 9: 自檢

交付前用 vision 分析自家 PPT 輸出：
1. 任何形狀 bottom > 下方元素 top → BUG（重疊）
2. 任何文字超出容器邊界 → BUG
3. 有陰影的元素 vs 無陰影的元素 → 與原圖比對
4. 顏色 PIL 取樣 vs PPT RGBColor → 一致？

任一未通過 → 修正 → 再檢查。
## 步驟 10: 截圖對比法（產出 vs 原始）

生成 PPT 後，將 PPT 截圖與原始截圖**同時交給 vision** 做差異分析：

"Compare these two images. Image 1 is the ORIGINAL. Image 2 is my PPT output.
List every visual difference: overlap, spacing, font size, shadow, missing elements, color mismatch."

Vision 會列出所有差異 → 一次性修正所有 → 再對比 → 直到差異清單為空才交付。

這條規則解決「肉眼重複檢查」的問題。

## v3 修正教訓

### 規則 S: 扁平設計需禁用預設陰影

python-pptx 的 shape 預設有 shadow。扁平設計（無陰影）必須：
`s.shadow.inherit = False`
在每個 S() 函數中加上這一行。

### 規則 T: 線條顏色與箭頭

- 線條顏色從 PIL 取樣，不要用純黑
- 需要箭頭的線 → 加小三角形 (MSO_SHAPE.ISOSCELES_TRIANGLE) 在線端

### 規則 U: PIL 取樣位置校準

邊框顏色難取樣（太細）。改取樣內部填色，或取樣邊框外側 2px 處。
若 PIL 回傳白色 → 取樣位置錯了，偏移 ±5px 重試。

### 規則 V: 輸出自我診斷

每次修正後，先用 vision 分析自家輸出截圖，確認 bugs 已消除再交付。
不要再回到「用戶肉眼→我修正→用戶肉眼→我修正」的循環。

## 規則 W: Icon 形狀檢測

Vision close-up 分析必須回答：
1. icon 是填滿 (fill) 還是外框 (outline)？
2. 形狀：pill (rad=0.5) / rounded square (rad=0.1-0.2)？
3. 內部子元素：幾個？什麼形狀？
4. 比例：icon 寬度 / 容器寬度 = ？

這四項全對 → icon 才正確。

## 規則 X: 字型與位置對齊檢查

交付前用 vision 檢查 output：
1. 每個文字框的實際 bounding box 與預期比例比對，偏差 > 5% → 修正
2. 文字在容器內是否居中？水平居中／垂直居中？
3. 字型大小比例鏈：title : label : body = a:b:c，與 vision 比例一致？

## 規則 Y: Icon 內部元素顏色逐項比對

Icon 的每個子元素（眼睛、嘴巴、線條）顏色都要從原圖取樣。
不預設 "眼睛就是黑色"。用 PIL 在 close-up 截圖中取樣確認。

## 規則 Z: 原圖直接取證，不靠用戶回饋

每個元素的正確屬性（顏色、填滿/外框、方向、粗細）必須從**原圖**取得：
1. 用 close-up 截圖 → vision 分析
2. vision 回答必須是 binary（填滿/外框、左/右、粗/細）
3. 不預設任何值，不依賴用戶糾正
4. 若 vision 答案矛盾，以**原始 close-up 截圖**為準（非遠景全圖）


## 規則 AA: 結構化屬性比對（自動化 diff）

每次建構後，執行以下 diff：
1. Vision 輸出原圖的**結構化屬性列表**（JSON 格式：每元素 name/shape_type/color/size/pos/has_shadow/font）
2. 我從程式碼提取相同屬性的值
3. 逐項比對，偏差超過 tolerance → 寫入修正清單
4. 一次性修正所有差異 → 再比對 → 直到清單為空

這個過程不依賴用戶肉眼。

## 規則 AB: Shape type 驗證

Vision 結構化數據中的 shape_type 必須嚴格匹配：
- circle → MSO_SHAPE.OVAL (w==h)
- rounded_rectangle → MSO_SHAPE.ROUNDED_RECTANGLE
- rectangle → MSO_SHAPE.RECTANGLE
不匹配 → 形狀錯誤。


## 規則 AC: 文字必須相對父形狀對齊

每個文字框：
- textbox_w = parent_shape_w（全寬）
- textbox_x = parent_shape_x（同左邊界）
- text_align = CENTER（水平居中）
- vertical_anchor = TOP（預設）

不要用獨立的 offset/padding，讓文字直接跟形狀綁定。

## 规则 AD: Icon 可能是多形状组合

简单图标常由多个基本形状组合。不要用单一形状代替。
用 close-up 分析每个子形状：类型、颜色、位置、比例。

## 规则 AE: 小框文字用 SHAPE_TO_FIT_TEXT

小方框内文字用 auto_size = SHAPE_TO_FIT_TEXT 自动居中。
比手动 MSO_ANCHOR 更可靠。

## 规则 AF: Vision 百分比定位验证

交付前用 vision 提取原图的像素位置 → 转百分比 → 与 P() 参数比对：
1. 偏差 > 3% → 修正
2. 卡片框架位置应优先验证（最容易量测）
3. 内部元素（圆、pill）用 close-up 分析确认半径和间距

