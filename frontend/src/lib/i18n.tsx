"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

export type Lang = "vi" | "en" | "ko";

const STORAGE_KEY = "lodestar.lang";

const DICT = {
  // Brand
  brand_subtitle: {
    vi: "Shinhan SOL · Coach",
    en: "Shinhan SOL · Coach",
    ko: "신한 SOL · 코치",
  },
  app_title: {
    vi: "Shinhan Financial Coach",
    en: "Shinhan Financial Coach",
    ko: "신한 금융 코치",
  },
  app_subtitle: {
    vi: "SOL Vietnam — AI Personal Financial Coach",
    en: "SOL Vietnam — AI Personal Financial Coach",
    ko: "SOL 베트남 — AI 개인 금융 코치",
  },

  // Tabs
  tab_feed: { vi: "Bảng tin", en: "Feed", ko: "피드" },
  tab_plan: { vi: "Kế hoạch", en: "Plan", ko: "계획" },
  tab_products: { vi: "Sản phẩm", en: "Products", ko: "상품" },
  nav_aria: { vi: "Điều hướng chính", en: "Main navigation", ko: "주요 탐색" },

  // Hero
  greeting_hello: { vi: "Xin chào", en: "Hello", ko: "안녕하세요" },
  stat_income: { vi: "Thu nhập", en: "Income", ko: "수입" },
  stat_spending: { vi: "Chi tiêu", en: "Spending", ko: "지출" },
  stat_remaining: { vi: "Còn lại", en: "Remaining", ko: "잔액" },

  // Theme toggle
  theme_aria: { vi: "Đổi giao diện", en: "Change theme", ko: "테마 변경" },
  theme_light: { vi: "Sáng", en: "Light", ko: "라이트" },
  theme_dark: { vi: "Tối", en: "Dark", ko: "다크" },
  theme_system: { vi: "Theo hệ thống", en: "System", ko: "시스템" },

  // Language toggle
  lang_aria: { vi: "Đổi ngôn ngữ", en: "Change language", ko: "언어 변경" },
  lang_vi: { vi: "Tiếng Việt", en: "Vietnamese", ko: "베트남어" },
  lang_en: { vi: "Tiếng Anh", en: "English", ko: "영어" },
  lang_ko: { vi: "Tiếng Hàn", en: "Korean", ko: "한국어" },

  // Layout mode toggle
  layout_toggle_aria: { vi: "Đổi bố cục", en: "Change layout", ko: "레이아웃 변경" },
  layout_app: { vi: "Chế độ ứng dụng", en: "App view", ko: "앱 보기" },
  layout_web: { vi: "Chế độ web", en: "Web view", ko: "웹 보기" },

  // Insight feed + cards
  compliance_banner: {
    vi: "Lodestar cung cấp thông tin tham khảo, không phải tư vấn tài chính.",
    en: "Lodestar provides reference information only, not financial advice.",
    ko: "Lodestar는 참고 정보를 제공할 뿐이며 금융 자문이 아닙니다.",
  },
  stream_status_aria: {
    vi: "Trạng thái luồng insight",
    en: "Insight stream status",
    ko: "인사이트 스트림 상태",
  },
  stream_live: { vi: "Đang hoạt động", en: "Live", ko: "라이브" },
  stream_offline: { vi: "Ngoại tuyến", en: "Offline", ko: "오프라인" },

  // Recent transactions strip
  recent_transactions: {
    vi: "Giao dịch gần đây",
    en: "Recent activity",
    ko: "최근 거래",
  },
  recent_transactions_empty: {
    vi: "Chưa có giao dịch.",
    en: "No transactions yet.",
    ko: "아직 거래가 없습니다.",
  },
  recent_transactions_more: {
    vi: "Xem thêm {count}",
    en: "Show {count} more",
    ko: "{count}개 더 보기",
  },
  recent_transactions_less: {
    vi: "Thu gọn",
    en: "Show less",
    ko: "접기",
  },

  // Agentic analysing skeleton
  coach_analysing_title: {
    vi: "Coach đang phân tích…",
    en: "Coach is analysing…",
    ko: "코치가 분석 중…",
  },
  coach_analysing_desc: {
    vi: "Agent đang kiểm tra các quy tắc và lịch sử giao dịch. Nếu có điều đáng chú ý, một thẻ sẽ xuất hiện ở đây.",
    en: "Agent is running checks against the rule set and recent history. If something's worth knowing, a card will land here.",
    ko: "에이전트가 규칙과 최근 거래를 검토 중입니다. 주목할 만한 것이 있으면 여기에 카드가 표시됩니다.",
  },
  coach_silent_toast: {
    vi: "Coach không thấy gì đáng chú ý từ giao dịch này.",
    en: "Coach saw nothing notable in that transaction.",
    ko: "이 거래에서 코치가 특별히 주목할 만한 점을 찾지 못했습니다.",
  },

  // Demo panel
  demo_open: { vi: "Mô phỏng", en: "Simulate", ko: "시뮬레이션" },
  demo_close: { vi: "Đóng", en: "Close", ko: "닫기" },
  demo_panel_title: {
    vi: "Mô phỏng hoạt động",
    en: "Simulate activity",
    ko: "활동 시뮬레이션",
  },
  demo_panel_desc: {
    vi: "Inject giao dịch để xem Coach phản ứng thời gian thực.",
    en: "Inject a transaction and watch the Coach react in real time.",
    ko: "거래를 주입하면 코치가 실시간으로 반응합니다.",
  },
  demo_custom_header: {
    vi: "Tùy chỉnh",
    en: "Custom transaction",
    ko: "직접 입력",
  },
  demo_field_merchant: { vi: "Đơn vị / Merchant", en: "Merchant", ko: "가맹점" },
  demo_field_amount: {
    vi: "Số tiền (âm = chi tiêu)",
    en: "Amount (negative = outflow)",
    ko: "금액 (음수 = 지출)",
  },
  demo_field_category: { vi: "Danh mục", en: "Category", ko: "카테고리" },
  demo_inject: { vi: "Ghi giao dịch", en: "Inject", ko: "주입" },
  demo_toast_agent_reasoning: {
    vi: "Đã ghi {merchant}. Coach đang phân tích…",
    en: "{merchant} recorded. Coach is analysing…",
    ko: "{merchant} 기록됨. 코치가 분석 중…",
  },
  demo_toast_error: {
    vi: "Không ghi được giao dịch.",
    en: "Could not record the transaction.",
    ko: "거래를 기록하지 못했습니다.",
  },
  demo_reset_button: {
    vi: "Đặt lại bản demo",
    en: "Reset demo",
    ko: "데모 초기화",
  },
  demo_reset_hint: {
    vi: "Xoá các thẻ và giao dịch mô phỏng đã thêm. Lịch sử gốc giữ nguyên.",
    en: "Clear insight cards and simulated transactions. Baseline history is kept.",
    ko: "인사이트 카드와 시뮬레이션 거래를 지웁니다. 기본 기록은 유지됩니다.",
  },
  demo_reset_toast_ok: {
    vi: "Đã đặt lại. Bảng sẵn sàng cho lượt mô phỏng tiếp theo.",
    en: "Reset done. Feed is ready for a fresh simulation.",
    ko: "초기화 완료. 다음 시뮬레이션 준비가 되었습니다.",
  },
  demo_reset_toast_err: {
    vi: "Không đặt lại được bản demo.",
    en: "Could not reset the demo.",
    ko: "데모를 초기화하지 못했습니다.",
  },

  // Simulate drawer — preset groups and hints
  demo_group_everyday: {
    vi: "Hằng ngày",
    en: "Everyday",
    ko: "일상",
  },
  demo_group_baby: {
    vi: "Sự kiện — em bé",
    en: "Life event — baby",
    ko: "라이프 이벤트 — 출산",
  },
  demo_group_anomalies: {
    vi: "Bất thường",
    en: "Anomalies",
    ko: "이상 징후",
  },
  demo_group_income_home: {
    vi: "Thu nhập + Nhà ở",
    en: "Income + Home",
    ko: "소득 + 주택",
  },
  demo_hint_first_baby: {
    vi: "Tín hiệu đầu tiên về em bé",
    en: "1st baby-merchant",
    ko: "첫 번째 출산 관련 가맹점",
  },
  demo_hint_second_baby: {
    vi: "Tín hiệu thứ hai — kích hoạt sự kiện cuộc sống",
    en: "2nd — should trigger life_event",
    ko: "두 번째 — life_event 발동",
  },
  demo_hint_third_baby: {
    vi: "Tín hiệu thứ ba — củng cố",
    en: "3rd baby signal (reinforces)",
    ko: "세 번째 — 신호 강화",
  },
  demo_hint_recurring_change: {
    vi: "Kích hoạt recurring_change",
    en: "should trigger recurring_change",
    ko: "recurring_change 발동",
  },
  demo_hint_big_shopping: {
    vi: "Chi tiêu mua sắm lớn",
    en: "Big shopping spend",
    ko: "대규모 쇼핑 지출",
  },
  demo_hint_payday: {
    vi: "Kích hoạt payday",
    en: "Should trigger payday",
    ko: "payday 발동",
  },
  demo_hint_home_purchase: {
    vi: "Tín hiệu mua nhà",
    en: "Home purchase signal",
    ko: "주택 구매 신호",
  },

  // Memory panel (demo narration — inspect lessons + reflections + cohort)
  memory_title: {
    vi: "Bộ nhớ của Coach",
    en: "Coach memory",
    ko: "코치 메모리",
  },
  memory_open: {
    vi: "Xem bộ nhớ",
    en: "Inspect memory",
    ko: "메모리 확인",
  },
  memory_description: {
    vi: "Bài học, phản hồi và tổng hợp cohort mà Coach đã tích lũy cho khách hàng này.",
    en: "Lessons, reflections and cohort aggregates the Coach has accumulated for this customer.",
    ko: "코치가 이 고객에 대해 축적한 교훈, 성찰 및 코호트 집계.",
  },
  memory_section_lessons: {
    vi: "Bài học ({count})",
    en: "Lessons ({count})",
    ko: "교훈 ({count})",
  },
  memory_section_reflections: {
    vi: "Phản hồi ({count})",
    en: "Reflections ({count})",
    ko: "성찰 ({count})",
  },
  memory_section_cohort: {
    vi: "Cohort ({key}) — {count} mẫu",
    en: "Cohort ({key}) — {count} patterns",
    ko: "코호트 ({key}) — {count}개 패턴",
  },
  memory_empty: {
    vi: "Chưa có bài học nào được ghi. Tương tác với một thẻ để Coach bắt đầu học.",
    en: "No lessons yet. Engage with a card so Coach starts learning.",
    ko: "아직 저장된 교훈이 없습니다. 카드를 탭해 코치가 학습하도록 하세요.",
  },
  memory_loading: {
    vi: "Đang tải bộ nhớ…",
    en: "Loading memory…",
    ko: "메모리 로딩 중…",
  },
  memory_error: {
    vi: "Không tải được bộ nhớ Coach.",
    en: "Could not load Coach memory.",
    ko: "코치 메모리를 불러오지 못했습니다.",
  },
  memory_close: { vi: "Đóng", en: "Close", ko: "닫기" },
  memory_quadrant_earned_reward: {
    vi: "Phần thưởng xứng đáng",
    en: "Earned reward",
    ko: "정당한 보상",
  },
  memory_quadrant_bad_luck: {
    vi: "Không may",
    en: "Bad luck",
    ko: "불운",
  },
  memory_quadrant_dumb_luck: {
    vi: "May mắn vô tình",
    en: "Dumb luck",
    ko: "운 좋은 결과",
  },
  memory_quadrant_just_desserts: {
    vi: "Tất yếu",
    en: "Just desserts",
    ko: "자업자득",
  },
  memory_confidence: { vi: "Độ tin cậy", en: "Confidence", ko: "확신도" },
  memory_importance: { vi: "Tầm quan trọng", en: "Importance", ko: "중요도" },
  memory_evolved: { vi: "Lần tiến hóa", en: "Evolved", ko: "진화" },

  // Generic error toasts for silent list-fetch failures
  feed_fetch_error: {
    vi: "Không tải được bảng tin Coach.",
    en: "Could not load the Coach feed.",
    ko: "코치 피드를 불러오지 못했습니다.",
  },
  goals_fetch_error: {
    vi: "Không tải được mục tiêu tiết kiệm.",
    en: "Could not load savings goals.",
    ko: "저축 목표를 불러오지 못했습니다.",
  },
  products_fetch_error: {
    vi: "Không tải được danh sách sản phẩm.",
    en: "Could not load products.",
    ko: "상품을 불러오지 못했습니다.",
  },
  transactions_fetch_error: {
    vi: "Không tải được giao dịch gần đây.",
    en: "Could not load recent activity.",
    ko: "최근 거래를 불러오지 못했습니다.",
  },

  // Tool call indicator
  chat_tool_running: {
    vi: "Đang gọi công cụ {name}…",
    en: "Calling tool {name}…",
    ko: "{name} 도구 호출 중…",
  },
  chat_tool_generic: {
    vi: "Đang sử dụng công cụ",
    en: "Using a tool",
    ko: "도구 사용 중",
  },

  // Qwen badge
  powered_by: { vi: "Vận hành bởi", en: "Powered by", ko: "제공" },

  // Chat suggestion prompts (sent to the LLM, rendered as chips)
  chat_prompt_next: {
    vi: "Tôi nên làm gì tiếp theo?",
    en: "What should I do next?",
    ko: "다음에 무엇을 해야 할까요?",
  },
  chat_prompt_scenario: {
    vi: "Nếu tôi mua nhà 2 tỷ thì sao?",
    en: "What if I buy a 2B VND home?",
    ko: "20억 VND 주택을 산다면 어떻게 될까요?",
  },
  chat_prompt_product: {
    vi: "Có sản phẩm nào phù hợp không?",
    en: "Are there any products that fit?",
    ko: "적합한 상품이 있나요?",
  },

  // Product search suggestion chips (sent to the bge-m3 retriever)
  products_suggestion_credit: {
    vi: "thẻ tín dụng cho lương 10 triệu",
    en: "credit card for 10M income",
    ko: "월급 천만 동 신용카드",
  },
  products_suggestion_home_loan: {
    vi: "vay mua nhà",
    en: "home loan",
    ko: "주택 담보 대출",
  },
  products_suggestion_life_insurance: {
    vi: "bảo hiểm nhân thọ",
    en: "life insurance",
    ko: "생명 보험",
  },
  card_cta: { vi: "Xem chi tiết", en: "View details", ko: "자세히 보기" },
  card_action_header: {
    vi: "Có thể cân nhắc",
    en: "You could consider",
    ko: "고려할 만한 사항",
  },
  dismiss_aria: { vi: "Bỏ qua", en: "Dismiss", ko: "닫기" },
  dismiss_success: {
    vi: "Đã bỏ qua. Coach sẽ ghi nhận phản hồi.",
    en: "Dismissed. Coach will note your feedback.",
    ko: "닫혔습니다. 코치가 피드백을 기록합니다.",
  },
  dismiss_error: {
    vi: "Không thể bỏ qua insight. Vui lòng thử lại.",
    en: "Could not dismiss. Please try again.",
    ko: "닫을 수 없습니다. 다시 시도해주세요.",
  },
  feed_empty_title: { vi: "Chưa có insight nào", en: "No insights yet", ko: "아직 인사이트가 없습니다" },
  feed_empty_desc: {
    vi: "Coach đang theo dõi giao dịch của bạn. Quay lại sau ít phút.",
    en: "Coach is watching your transactions. Check back in a few minutes.",
    ko: "코치가 거래 내역을 확인 중입니다. 잠시 후 다시 확인해주세요.",
  },

  // Severity labels
  sev_life_event: { vi: "Sự kiện cuộc sống", en: "Life event", ko: "라이프 이벤트" },
  sev_anomaly: { vi: "Bất thường", en: "Anomaly", ko: "이상 징후" },
  sev_milestone: { vi: "Mốc quan trọng", en: "Milestone", ko: "마일스톤" },
  sev_info: { vi: "Thông tin", en: "Information", ko: "정보" },
  sev_product: { vi: "Sản phẩm", en: "Product", ko: "상품" },

  // Insight detail
  back_to_feed: { vi: "Quay lại bảng tin", en: "Back to feed", ko: "피드로 돌아가기" },
  insight_not_found: {
    vi: "Không tìm thấy insight. Có thể đã bị bỏ qua.",
    en: "Insight not found — it may have been dismissed.",
    ko: "인사이트를 찾을 수 없습니다. 이미 닫힌 상태일 수 있습니다.",
  },

  // Chat
  chat_thinking: { vi: "Coach đang suy nghĩ…", en: "Coach is thinking…", ko: "코치가 생각 중입니다…" },
  chat_placeholder: { vi: "Hỏi Coach…", en: "Ask Coach…", ko: "코치에게 질문하세요…" },
  chat_send_aria: { vi: "Gửi", en: "Send", ko: "보내기" },
  chat_error: {
    vi: "Xin lỗi, đã xảy ra lỗi. Vui lòng thử lại.",
    en: "Sorry, something went wrong. Please try again.",
    ko: "죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.",
  },
  chat_empty_prompt: {
    vi: "Hỏi Coach điều gì đó — ví dụ tôi nên chuẩn bị tài chính ra sao, hoặc mô phỏng kịch bản mua nhà.",
    en: "Ask Coach anything — for example how to prepare financially, or simulate a home-purchase scenario.",
    ko: "코치에게 무엇이든 물어보세요 — 예: 재정 준비 방법, 주택 구매 시나리오 시뮬레이션.",
  },

  // Goals view
  goals_heading: { vi: "Mục tiêu tiết kiệm", en: "Savings goals", ko: "저축 목표" },
  goals_new: { vi: "Tạo mục tiêu", en: "New goal", ko: "새 목표" },
  goals_empty_title: { vi: "Chưa có mục tiêu", en: "No goals yet", ko: "아직 목표가 없습니다" },
  goals_empty_desc: {
    vi: "Tạo một mục tiêu tiết kiệm để Coach giúp bạn theo dõi tiến độ.",
    en: "Create a savings goal so Coach can track your progress.",
    ko: "저축 목표를 만들면 코치가 진행 상황을 추적합니다.",
  },
  goals_deadline: { vi: "Hạn", en: "Deadline", ko: "기한" },
  goals_dialog_title: { vi: "Mục tiêu mới", en: "New goal", ko: "새 목표" },
  goals_dialog_desc: {
    vi: "Đặt mục tiêu tiết kiệm và theo dõi tiến độ.",
    en: "Set a savings goal and watch your progress.",
    ko: "저축 목표를 설정하고 진행 상황을 확인하세요.",
  },
  goals_field_name: { vi: "Tên mục tiêu", en: "Goal name", ko: "목표 이름" },
  goals_field_name_placeholder: {
    vi: "Ví dụ: Quỹ khẩn cấp",
    en: "e.g. Emergency fund",
    ko: "예: 비상 자금",
  },
  goals_field_amount: { vi: "Số tiền mục tiêu (VND)", en: "Target amount (VND)", ko: "목표 금액 (VND)" },
  goals_field_date: { vi: "Ngày hoàn thành", en: "Target date", ko: "목표 날짜" },
  goals_cancel: { vi: "Huỷ", en: "Cancel", ko: "취소" },
  goals_save: { vi: "Lưu mục tiêu", en: "Save goal", ko: "목표 저장" },
  goals_saving: { vi: "Đang lưu…", en: "Saving…", ko: "저장 중…" },
  goals_created: { vi: "Đã tạo mục tiêu mới", en: "New goal created", ko: "새 목표가 생성되었습니다" },
  goals_create_error: {
    vi: "Không tạo được mục tiêu. Thử lại sau.",
    en: "Could not create goal. Please retry.",
    ko: "목표를 생성할 수 없습니다. 다시 시도해주세요.",
  },

  // Scenario simulator
  sim_heading: { vi: "Mô phỏng kịch bản", en: "Scenario simulation", ko: "시나리오 시뮬레이션" },
  sim_subheading: {
    vi: "Lodestar phân tích tác động trên cả bốn đơn vị Shinhan.",
    en: "Lodestar analyses impact across all four Shinhan entities.",
    ko: "Lodestar는 신한의 4개 계열사 전반에 미치는 영향을 분석합니다.",
  },
  sim_card_title: { vi: "Mô phỏng tài chính", en: "Financial simulation", ko: "재무 시뮬레이션" },
  sim_card_title_home: { vi: "Nếu tôi mua nhà…", en: "What if I buy a home…", ko: "주택을 구매한다면…" },
  sim_card_title_career: { vi: "Nếu tôi đổi việc…", en: "What if I change careers…", ko: "이직한다면…" },
  sim_card_title_baby: { vi: "Nếu tôi có em bé…", en: "What if we have a baby…", ko: "출산하게 된다면…" },
  sim_card_desc: {
    vi: "Lodestar mô phỏng tác động trên cả bốn đơn vị Shinhan.",
    en: "Lodestar simulates the impact across all four Shinhan entities.",
    ko: "Lodestar가 신한 4개 계열사 전반의 영향을 시뮬레이션합니다.",
  },
  sim_scenario_label: {
    vi: "Kịch bản",
    en: "Scenario",
    ko: "시나리오",
  },
  sim_scenario_home: {
    vi: "Mua nhà",
    en: "Home purchase",
    ko: "주택 구매",
  },
  sim_scenario_career: {
    vi: "Đổi việc",
    en: "Career change",
    ko: "이직",
  },
  sim_scenario_baby: {
    vi: "Có em bé",
    en: "New baby",
    ko: "출산",
  },
  sim_field_new_income: {
    vi: "Thu nhập mới (VND/tháng)",
    en: "New monthly income (VND)",
    ko: "새 월 소득 (VND)",
  },
  sim_field_new_income_hint: {
    vi: "Ví dụ 16,000,000 cho tăng lương lên 16 triệu.",
    en: "e.g. 16,000,000 for a raise to 16M.",
    ko: "예: 월 1,600만 VND로 인상 시 16,000,000.",
  },
  sim_field_baby_cost: {
    vi: "Chi phí hàng tháng cho em bé (VND)",
    en: "Monthly baby cost (VND)",
    ko: "월별 육아비 (VND)",
  },
  sim_field_baby_cost_hint: {
    vi: "Bao gồm sữa, y tế và chăm sóc. Mặc định 8,000,000.",
    en: "Formula, medical and childcare. Defaults to 8,000,000.",
    ko: "분유, 의료 및 육아. 기본값 8,000,000.",
  },
  sim_price: { vi: "Giá nhà (VND)", en: "Property price (VND)", ko: "주택 가격 (VND)" },
  sim_price_hint: {
    vi: "Ví dụ 2,000,000,000 cho nhà 2 tỷ.",
    en: "e.g. 2,000,000,000 for a 2B VND home.",
    ko: "예: 20억 VND 주택의 경우 2,000,000,000.",
  },
  sim_down: { vi: "Tỷ lệ đặt cọc", en: "Down payment %", ko: "계약금 비율" },
  sim_term: { vi: "Kỳ (tháng)", en: "Term (months)", ko: "기간 (개월)" },
  sim_rate: { vi: "Lãi (%)", en: "Rate (%)", ko: "금리 (%)" },
  sim_run: { vi: "Chạy mô phỏng", en: "Run simulation", ko: "시뮬레이션 실행" },
  sim_running: { vi: "Đang mô phỏng…", en: "Simulating…", ko: "시뮬레이션 중…" },
  sim_error: {
    vi: "Mô phỏng thất bại. Vui lòng thử lại.",
    en: "Simulation failed. Please retry.",
    ko: "시뮬레이션에 실패했습니다. 다시 시도해주세요.",
  },
  sim_error_title: { vi: "Lỗi", en: "Error", ko: "오류" },
  sim_result_title: { vi: "Kết quả tổng hợp", en: "Combined result", ko: "종합 결과" },
  sim_before: { vi: "Trước", en: "Before", ko: "이전" },
  sim_after: { vi: "Sau", en: "After", ko: "이후" },
  entity_bank: { vi: "Ngân hàng", en: "Bank", ko: "은행" },
  entity_finance: { vi: "Tài chính tiêu dùng", en: "Consumer finance", ko: "소비자 금융" },
  entity_securities: { vi: "Chứng khoán", en: "Securities", ko: "증권" },
  entity_life: { vi: "Bảo hiểm nhân thọ", en: "Life insurance", ko: "생명보험" },

  // Products
  products_heading: { vi: "Sản phẩm Shinhan", en: "Shinhan products", ko: "신한 상품" },
  products_subheading: {
    vi: "Tìm kiếm thẻ tín dụng, vay, bảo hiểm và đầu tư bằng tiếng Việt.",
    en: "Search credit cards, loans, insurance and investments.",
    ko: "신용카드, 대출, 보험 및 투자 상품을 검색하세요.",
  },
  products_search_placeholder: {
    vi: "Tìm sản phẩm bằng tiếng Việt…",
    en: "Search products…",
    ko: "상품 검색…",
  },
  products_search_button: { vi: "Tìm", en: "Search", ko: "검색" },
  products_empty_title: {
    vi: "Không tìm thấy sản phẩm",
    en: "No products found",
    ko: "상품을 찾을 수 없습니다",
  },
  products_empty_desc: {
    vi: 'Thử từ khoá khác như "thẻ tín dụng" hoặc "vay mua nhà".',
    en: 'Try terms like "thẻ tín dụng" (credit card) or "vay mua nhà" (home loan).',
    ko: '"thẻ tín dụng"(신용카드) 또는 "vay mua nhà"(주택담보대출) 같은 키워드를 시도해보세요.',
  },
  products_min_income: { vi: "Thu nhập tối thiểu", en: "Min income", ko: "최소 소득" },
  product_entity_bank: { vi: "Ngân hàng", en: "Bank", ko: "은행" },
  product_entity_finance: { vi: "Tài chính", en: "Finance", ko: "금융" },
  product_entity_securities: { vi: "Chứng khoán", en: "Securities", ko: "증권" },
  product_entity_life: { vi: "Bảo hiểm", en: "Insurance", ko: "보험" },

  // Chart renderer
  chart_unsupported: {
    vi: 'Không hỗ trợ biểu đồ "{type}"',
    en: 'Chart type "{type}" is not supported',
    ko: '"{type}" 차트 유형은 지원되지 않습니다',
  },
  chart_label_amount: { vi: "Số tiền", en: "Amount", ko: "금액" },
  chart_label_value: { vi: "Giá trị", en: "Value", ko: "값" },
} as const;

export type StringKey = keyof typeof DICT;

interface Ctx {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: StringKey, vars?: Record<string, string>) => string;
}

const LangCtx = createContext<Ctx | null>(null);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("vi");

  // Restore saved preference after mount. Synchronous setState is required
  // here to avoid a visible flash when the stored language differs from the
  // server-rendered default — next-themes uses the same pattern.
  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved === "vi" || saved === "en" || saved === "ko") {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setLangState(saved);
      }
    } catch {
      // localStorage unavailable — keep default
    }
  }, []);

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // ignore
    }
  }, []);

  const t = useCallback(
    (key: StringKey, vars?: Record<string, string>) => {
      const entry = DICT[key];
      const raw = entry[lang] ?? entry.vi ?? key;
      if (!vars) return raw;
      return Object.keys(vars).reduce(
        (out, name) => out.replace(new RegExp(`\\{${name}\\}`, "g"), vars[name]),
        raw
      );
    },
    [lang]
  );

  const value = useMemo<Ctx>(() => ({ lang, setLang, t }), [lang, setLang, t]);

  return <LangCtx.Provider value={value}>{children}</LangCtx.Provider>;
}

export function useT(): Ctx {
  const ctx = useContext(LangCtx);
  if (!ctx) throw new Error("useT must be used within <LanguageProvider>");
  return ctx;
}
