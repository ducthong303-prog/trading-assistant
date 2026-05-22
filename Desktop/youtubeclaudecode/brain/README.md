# brain/ — Shared AI Logic

Đây là "bộ não" của toàn bộ hệ thống — chứa mọi prompt, template, và workflow được dùng chung.

**Nguyên tắc:** Mọi skill (script/image/thumbnail) tham chiếu từ đây. KHÔNG duplicate.

## Cấu trúc

```
brain/
├── prompts/       ← Single source of truth: style, colors, competitors
├── templates/     ← Reusable structures cho script/image/thumbnail
├── workflows/     ← Multi-step workflow definitions (full production, fast paths)
└── skills/        ← Reserved cho symlink tới root SKILL.md (future)
```

## Cách dùng

Các file trong `brain/prompts/` được pre-load bởi CLAUDE.md. Khi một skill được kích hoạt, nó tham chiếu đến brain/ thay vì tự định nghĩa lại style/colors.

## File authoritative

| File | Vai trò |
|------|---------|
| `prompts/style-signature.md` | Visual constitution — MỌI prompt ảnh/thumbnail phải tuân theo |
| `prompts/color-palette.md` | Exact hex codes, không còn màu mâu thuẫn giữa các skill |
| `prompts/competitor-brief.md` | Đối thủ + pattern viral rates |
| `templates/script-template.md` | Cấu trúc script chuẩn |
| `templates/image-prompt-template.md` | Template prompt ảnh |
| `templates/thumbnail-brief.md` | 6 patterns thumbnail + typography specs |
| `workflows/full-production.md` | Pipeline 9 bước end-to-end |
