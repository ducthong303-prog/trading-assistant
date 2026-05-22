---
name: video-bible-explainer
description: Sản xuất video Bible Explainer hoàn chỉnh từ 1 câu lệnh. Script → Ảnh KieAI 4o → TTS ElevenLabs → Render FFmpeg → Auto-cleanup. Trigger: "làm video về [chủ đề]", "sản xuất video [chủ đề]", "tạo video [chủ đề]".
---

# Video Bible Explainer v1.0

> **1 câu lệnh → 1 file MP4. Mọi thứ khác tự động dọn dẹp.**

---

## TRIGGER

```
"làm video về [chủ đề]"
"sản xuất video [chủ đề]"
"tạo video [chủ đề]"
```

---

## PRE-FLIGHT (BẮT BUỘC — chạy trước mọi thứ)

Trước khi generate bất kỳ thứ gì, kiểm tra:

```
[ ] KieAI API key hợp lệ?     → gọi GET /api/v1/... với key
[ ] KieAI còn credit?          → kiểm tra response không 402/429
[ ] ElevenLabs API key hợp lệ? → gọi GET /v1/voices
[ ] ElevenLabs còn credit?     → kiểm tra response không 402
[ ] FFmpeg đã cài?             → which ffmpeg
[ ] Disk space > 2GB?          → df -h .
```

**NẾU BẤT KỲ CHECK NÀO FAIL → DỪNG NGAY, báo lỗi cụ thể.**

---

## PIPELINE 5 STAGE

### Stage 1: SCRIPT
- Generate script 3,500-4,000 từ, 3-Act, TTS-ready
- Dùng `brain/prompts/style-signature.md` cho style reference
- Output: script text + 28 image prompts + TTS text (clean prose)
- Lưu tạm vào `channels/bible-explainer/video/{topic}/working/`

### Stage 2: IMAGES (KieAI GPT-4o)
- Provider: `KieAI4oClient` — POST `https://api.kie.ai/api/v1/gpt4o-image/generate`
- Size: `"3:2"` (sẽ crop thành 16:9 khi render)
- Batch: 5 ảnh/lần, mỗi ảnh qua webhook callback riêng
- Verify: **kiểm tra content-type** — nếu là `text/html` → RETRY
- Retry: tối đa 1 lần/ảnh, nếu vẫn fail → báo lỗi

### Stage 3: TTS (ElevenLabs trực tiếp)
- Voice: Mike (`ewxUvnyvvOehYjKjUVKC`) — cố định
- Split script thành ~6 chunks, mỗi chunk ~4000 ký tự
- Gọi ElevenLabs API sync: `POST /v1/text-to-speech/{voice_id}`
- Verify: file > 10s duration

### Stage 4: RENDER (FFmpeg Hardware)
- VideoToolbox HW encoder (nhanh 20x so với software)
- Scale đơn giản: `scale=1920:1080` (KHÔNG zoompan — quá chậm)
- Crop 3:2 → 16:9: `crop=1920:1080`
- Ghép audio AAC 320kbps
- Output: `channels/bible-explainer/video/{topic}/{topic}_FINAL.mp4`
- **Verify: kiểm tra có cả video VÀ audio stream**

### Stage 5: CLEANUP (tự động, không hỏi)
- Xoá toàn bộ thư mục `working/` (temp segments, prompts, intermediate files)
- Xoá ảnh trong `images/{topic}/`
- Xoá audio chunks trong `audio/{topic}/`
- Xoá manifest
- **CHỈ GIỮ LẠI:** `{topic}_FINAL.mp4` + 1 dòng production log

---

## PRODUCTION LOG

Sau mỗi video, ghi 1 dòng vào `channels/bible-explainer/video/production_log.jsonl`:

```json
{"date": "2026-05-22", "topic": "every-time-jesus-wept", "duration_sec": 1440, "images": 28, "tts_chunks": 4, "render_time_sec": 180, "file": "every-time-jesus-wept_FINAL.mp4"}
```

---

## FAILURE MODES

1. **Pre-flight fail** → dừng ngay, báo thiếu gì
2. **Ảnh fail** → retry 1 lần, nếu vẫn fail → báo lỗi + dừng
3. **TTS fail** → retry chunk đó 3 lần, nếu vẫn fail → báo lỗi
4. **Render fail** → kiểm tra disk space, thử lại
5. **Verify fail** → không xoá temp, giữ lại để debug

---

## NGUYÊN TẮC

- **Không hỏi** — chạy hết pipeline, chỉ dừng nếu fail
- **Không giữ rác** — cleanup luôn sau khi verify OK
- **Verify từng stage** — không bao giờ skip verify
- **Pre-flight first** — không generate gì khi chưa check API
