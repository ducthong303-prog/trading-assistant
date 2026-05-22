# brain/prompts/ — Shared Prompt Library

**Single source of truth** cho mọi style, color, và competitor data.

## Files

| File | Mô tả | Được dùng bởi |
|------|-------|---------------|
| `style-signature.md` | Visual constitution — watercolor, ink, background, character design, typography, negative prompts | CẢ 3 skills |
| `color-palette.md` | Exact hex codes + usage matrix | image + thumbnail skills |
| `competitor-brief.md` | Đối thủ (Deep Made Simple 144K, Bible Made Simple 9.3K, Plain Truth 6K) + 6 pattern viral rates | script + thumbnail skills |

## Quy tắc

1. **Đây là nguồn DUY NHẤT.** Không skill nào được tự define lại màu sắc, font, hay style.
2. **Cập nhật ở đây trước.** Muốn đổi style → sửa file này → mọi skill tự động theo.
3. **Không xoá.** Style cũ có thể lưu version trong comment nếu cần rollback.
