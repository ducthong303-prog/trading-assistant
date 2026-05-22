# .claude/ — Claude Code Project Config

Dự án-specific Claude Code configuration.

## Files

| File | Mô tả |
|------|--------|
| `settings.local.json` | Project settings (không trading hooks) |
| `commands/` | Custom slash commands (/new-video, /generate-images, v.v.) |

## Commands

| Command | Chức năng |
|---------|-----------|
| `/new-video` | Khởi động full production pipeline |
| `/generate-images` | Tạo prompt ảnh từ script |
| `/generate-thumb` | Tạo thumbnail (3 var × 2 ver) |
| `/export-video` | Publishing checklist |
| `/competitor-check` | Phân tích kênh đối thủ |

## Nguyên tắc

- **KHÔNG** symlink từ trading-system
- **KHÔNG** TradingView MCP
- **KHÔNG** trading hooks
- Project này = VIDEO PRODUCTION STUDIO
