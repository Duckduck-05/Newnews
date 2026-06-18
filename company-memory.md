# Company Memory — cross-agent decisions

## 2026-06-19 Engineering: Personal Morning Intelligence Agent — full pipeline build (§1-9 brief) | Context: khi tiếp tục/maintain dự án newnews, hoặc build pipeline multi-source + LLM tương tự

- Build toàn bộ pipeline trong 1 lần (bước 2-9 của §12 brief), theo yêu cầu operator "làm hết, không dừng giữa chừng". Mọi stage thiếu API key (Gemini/DeepSeek/Telegram/ProductHunt) đều graceful-degrade: log warning rõ "thiếu key X", KHÔNG crash, vẫn chạy hết các stage còn lại.
- Quyết định kỹ thuật quan trọng nhất phát hiện giữa quá trình build: Stage 1 filter PHẢI cắt top-N theo TỪNG type (research/funding/product/deep_tech/outside) thay vì cắt top-N toàn cục trước khi phân bổ theo cơ cấu — nếu không, 1 nguồn có bias điểm hệ thống (GitHub Trending luôn +5 "freshness" vì không có ngày publish per-repo) sẽ áp đảo và loại sạch funding/deep_tech trước khi Stage 1 LLM ranking/allocation kịp chọn.
- verify.py (Stage 1.5) tính confidence 🟢🟡🔴 bằng if/else code thuần, KHÔNG hỏi LLM — LLM chỉ dùng để rank/chọn item, không bao giờ quyết mức tin cậy. Cross-reference triển khai bằng so khớp token tiêu đề giữa item cùng batch Stage 0 (rẻ, xác định được, không cần gọi search thật).
- 22 unit test (tests/test_verify.py, test_memory.py, test_source_registry.py) đều pass, gồm test bắt buộc theo acceptance criteria: item tier 3 không cross-confirm phải ép 🔴.
- "outside" type không có nguồn fetcher riêng — giải quyết bằng tag_outside_candidates() trong pipeline.py: retag item match outside_lane_domains nhưng KHÔNG match thesis chính, sau Stage 1 filter trước khi allocation.
- Toàn bộ secrets đọc qua env/GitHub Secrets, README có hướng dẫn lấy từng key + cảnh báo data privacy Gemini free tier (không feed dữ liệu cá nhân).
