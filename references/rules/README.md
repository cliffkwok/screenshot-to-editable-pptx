# Rule categories (learn once → apply forever)

**How this works for you:** when something is wrong, name the category (or just say what’s wrong). The agent updates **that file only**, then re-runs the pre-delivery checklist. You do not re-teach the whole system.

| Category | File | Gate / check |
|----------|------|----------------|
| **Measure** | [01-measure.md](01-measure.md) | Neighbor pads; no leftover-space placement |
| **Color** | [02-color.md](02-color.md) | PIL sample + `color_probes` in `verify_pptx` |
| **Shape** | [03-shape.md](03-shape.md) | Geometry fidelity (oval≠octagon, 3D, radius) |
| **Text** | [04-text.md](04-text.md) | Wrap-from-photo; mid-word wraps = defects |
| **Lines / icons** | [05-lines-icons.md](05-lines-icons.md) | Stroke role, arrows, top-level groups |
| **Delivery** | [06-delivery.md](06-delivery.md) | Checklist + three automated gates |

**Learning log:** every new correction is appended to [LEARNINGS.md](LEARNINGS.md) with `category:` + one-line rule. That line is then promoted into the matching category file if it is reusable.

**Index law (all categories):** measure every element against its neighbors. Nothing is placed by leftover space. Fix one instance → fix all siblings → update the category file.

Parent skill: [../../SKILL.md](../../SKILL.md) · Cursor rule: `screenshot-to-editable-ppt` · Full checklist: [../pre-delivery-checklist.md](../pre-delivery-checklist.md)
