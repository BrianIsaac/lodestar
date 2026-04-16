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
  card_cta: { vi: "Xem chi tiết", en: "View details", ko: "자세히 보기" },
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
  sim_card_title: { vi: "Nếu tôi mua nhà…", en: "What if I buy a home…", ko: "주택을 구매한다면…" },
  sim_card_desc: {
    vi: "Lodestar mô phỏng tác động trên cả bốn đơn vị Shinhan.",
    en: "Lodestar simulates the impact across all four Shinhan entities.",
    ko: "Lodestar가 신한 4개 계열사 전반의 영향을 시뮬레이션합니다.",
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
