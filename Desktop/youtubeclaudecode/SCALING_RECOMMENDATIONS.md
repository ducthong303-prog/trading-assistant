# SCALING_RECOMMENDATIONS.md — Future Growth Roadmap

> **Current state:** 1 channel (bible-explainer), 1 video in production
> **Target:** Multi-channel YouTube AI Factory

---

## Phase 1: Stabilize Single Channel (Now)

### Hoàn thiện video đầu tiên
- [ ] Hoàn thành sản xuất video "Fear Not"
- [ ] Đăng lên YouTube
- [ ] A/B test 3 thumbnails (7-14 ngày)
- [ ] Ghi nhận CTR, retention, subscriber gain
- [ ] Document winning pattern

### Tối ưu workflow
- [ ] Đo thời gian thực tế mỗi bước
- [ ] Xác định bottleneck
- [ ] Tinh chỉnh prompt templates dựa trên kết quả thực tế
- [ ] Build thư viện reusable Canva templates

### Target metrics
- Video #1: CTR >5%, retention >50%
- Production time: <6 hours total
- Cost: <$20/video (ElevenLabs + Google Flow)

---

## Phase 2: Scale bible-explainer (Month 2-4)

### Tăng tần suất
- Mục tiêu: 4 videos/tháng (weekly upload)
- Pipeline: luôn có 2 videos trong production pipeline
- Batch image generation (tạo ảnh cho nhiều video cùng lúc)

### Automation nâng cao
- [ ] ElevenLabs API auto-generation (ko manual copy-paste)
- [ ] YouTube Analytics auto-pull (theo dõi CTR không cần mở dashboard)
- [ ] A/B test auto-tracker (tự động chọn winner sau 14 ngày)
- [ ] Competitor weekly scan script

### Content đa dạng
- Series 1: "Every X Explained" (main)
- Series 2: "Bible Character Deep Dives"
- Series 3: "Hebrew/Greek Word Studies" (shorts)

### Target metrics
- 10 videos published
- Channel CTR avg >7%
- Subscribers: 1K+

---

## Phase 3: Multi-Channel (Month 4-8)

### Thêm kênh mới

```bash
# Kênh 2: Christian History
mkdir -p channels/christian-history/{scripts,images,thumbnails,audio,video,publishing}

# Kênh 3: Bible Biographies  
mkdir -p channels/bible-biographies/{scripts,images,thumbnails,audio,video,publishing}

# Kênh 4: Theology Explained
mkdir -p channels/theology-explained/{scripts,images,thumbnails,audio,video,publishing}
```

### Chiến lược kênh

| Kênh | Niche | Style | Audience |
|------|-------|-------|----------|
| bible-explainer | "Every X Explained" series | Watercolor illustration | General Christian |
| christian-history | Church history, martyrs, creeds | Darker watercolor palette | Seminary-educated |
| bible-biographies | Character deep dives | Portrait-focused watercolor | Bible study groups |
| theology-explained | Doctrines, concepts | Explainer/infographic style | New believers |

### Shared infrastructure
- Tất cả dùng chung `brain/prompts/` (style, colors)
- Mỗi kênh có template variant riêng trong `brain/templates/[channel]/`
- Cross-promotion giữa các kênh (end screens, cards)
- Unified analytics dashboard

### Target metrics
- 4 channels, mỗi kênh 2-4 videos/tháng
- Tổng: 8-16 videos/tháng
- Revenue: YouTube AdSense + potential sponsors

---

## Phase 4: AI Factory (Month 8+)

### Full automation
- Idea generation từ trending topics
- Script first-draft auto (human review only)
- Image batch generation queue
- Thumbnail auto A/B test rotation
- Publishing scheduler

### Team structure
- 1 AI Operator (quản lý pipeline, review output)
- 1 Video Editor (assembly, motion graphics)
- 1 Content Strategist (topics, SEO, thumbnails)
- AI handles: script draft, image generation, thumbnail variants, TTS

### Custom tooling
- Web dashboard quản lý multi-channel
- Content calendar với AI suggestion
- Analytics aggregation (cross-channel)
- Revenue tracking

### Target metrics
- 10+ channels hoặc 1 mega-channel
- 100+ videos published
- Subscribers: 100K+ total
- Revenue: Sustainable income từ YouTube

---

## Kiến trúc hỗ trợ scaling

```
Hiện tại (v3.0):
  brain/ → channels/bible-explainer/

Phase 3:
  brain/ → channels/bible-explainer/
         → channels/christian-history/
         → channels/bible-biographies/
         → channels/theology-explained/

Phase 4:
  brain/ → channels/channel-01..10/
  automation/ → CI/CD pipeline
  dashboards/ → analytics + management
```

Không cần refactor architecture khi scale — `channels/` structure đã được thiết kế cho multi-channel từ đầu.

---

## Cost Projections

| Phase | Monthly Cost | Revenue Potential |
|-------|-------------|-------------------|
| 1 (single channel, 4 vids) | ~$80 (ElevenLabs $20 + Flow $50 + Claude $10) | $0-50 (AdSense) |
| 2 (single channel, 16 vids) | ~$200 | $50-200 |
| 3 (4 channels, 32 vids) | ~$500 | $200-1000 |
| 4 (AI factory) | ~$1000-2000 | $1000-5000+ |
