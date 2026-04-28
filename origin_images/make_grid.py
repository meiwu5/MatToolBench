"""
生成配色对比拼接图
运行: python make_grid.py
输出: palette_grid.png
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── 配置 ──────────────────────────────────────────────────────
IMAGE_DIR  = Path(__file__).parent / "FTIR"   # 图片来源目录
OUTPUT     = Path(__file__).parent / "ftir_grid.png"

COLS       = 3          # 每行几张
THUMB_W    = 700        # 每张缩略图宽度
THUMB_H    = 520        # 每张缩略图高度
LABEL_H    = 48         # 编号标签栏高度
PADDING    = 20         # 格子间距
BG         = (245, 245, 245)
# ──────────────────────────────────────────────────────────────

def try_font(size):
    for name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()

def main():
    images = sorted(IMAGE_DIR.glob("*.png"))
    if not images:
        print(f"未找到图片：{IMAGE_DIR}")
        return

    n    = len(images)
    cols = min(COLS, n)
    rows = (n + cols - 1) // cols

    cell_w = THUMB_W + PADDING
    cell_h = THUMB_H + LABEL_H + PADDING
    canvas = Image.new("RGB",
                       (cols * cell_w + PADDING, rows * cell_h + PADDING),
                       BG)
    draw      = ImageDraw.Draw(canvas)
    font_lbl  = try_font(28)

    for idx, path in enumerate(images):
        row, col = divmod(idx, cols)
        x0 = PADDING + col * cell_w
        y0 = PADDING + row * cell_h

        # 编号标签背景
        draw.rectangle([x0, y0, x0 + THUMB_W, y0 + LABEL_H],
                       fill=(50, 50, 50))
        draw.text((x0 + 12, y0 + 8),
                  f"#{idx + 1}  {path.stem}",
                  font=font_lbl, fill=(255, 255, 255))

        # 缩略图
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
            px = x0 + (THUMB_W - img.width)  // 2
            py = y0 + LABEL_H + (THUMB_H - img.height) // 2
            canvas.paste(img, (px, py))
        except Exception as e:
            draw.text((x0 + 10, y0 + LABEL_H + 10),
                      f"[加载失败]\n{e}", font=font_lbl, fill=(200, 0, 0))

        # 边框
        draw.rectangle([x0, y0, x0 + THUMB_W, y0 + LABEL_H + THUMB_H],
                       outline=(180, 180, 180), width=2)

    canvas.save(OUTPUT, dpi=(150, 150))
    print(f"已保存 → {OUTPUT}  ({n} 张，{cols} 列 × {rows} 行)")

if __name__ == "__main__":
    main()
