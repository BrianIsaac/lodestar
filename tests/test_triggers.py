"""Tests for deterministic trigger rules and compliance filter."""

from datetime import date, timedelta

from lodestar.agents.compliance import ComplianceClass, apply_compliance, classify_output
from lodestar.agents.triggers import (
    TriggerType,
    check_budget_threshold,
    check_life_event_pattern,
    check_payday_detected,
    check_recurring_change,
    check_velocity_anomaly,
)
from lodestar.models import Transaction


def _make_txn(customer_id: str = "C001", amount: float = -100_000,
              category: str = "food", merchant: str = "Grab Food",
              days_ago: int = 0) -> Transaction:
    """Helper to create a test transaction."""
    return Transaction(
        transaction_id=f"TX-{days_ago}-{amount}",
        customer_id=customer_id,
        account_id="ACC-001",
        date=(date.today() - timedelta(days=days_ago)).isoformat(),
        amount=amount,
        category=category,
        merchant=merchant,
        description=f"CT DEN {merchant}",
    )


class TestTriggerRules:
    """Test each trigger rule against synthetic patterns."""

    def test_velocity_anomaly_fires(self) -> None:
        txns = []
        for m in range(3):
            txns.append(_make_txn(amount=-200_000, category="food", days_ago=30 * m + 15))
        txns.append(_make_txn(amount=-800_000, category="food", days_ago=1))

        result = check_velocity_anomaly(txns, "C001")
        assert result is not None
        assert result.trigger_type == TriggerType.VELOCITY_ANOMALY

    def test_velocity_anomaly_no_fire_normal(self) -> None:
        txns = [_make_txn(amount=-200_000, category="food", days_ago=i * 30 + 15) for i in range(4)]
        result = check_velocity_anomaly(txns, "C001")
        assert result is None

    def test_recurring_change_fires(self) -> None:
        txns = [
            _make_txn(merchant="Viettel", amount=-100_000, category="bills", days_ago=90),
            _make_txn(merchant="Viettel", amount=-100_000, category="bills", days_ago=60),
            _make_txn(merchant="Viettel", amount=-100_000, category="bills", days_ago=30),
            _make_txn(merchant="Viettel", amount=-150_000, category="bills", days_ago=1),
        ]
        result = check_recurring_change(txns, "C001")
        assert result is not None
        assert result.trigger_type == TriggerType.RECURRING_CHANGE
        assert "Viettel" in result.description

    def test_payday_detected(self) -> None:
        txns = [_make_txn(amount=12_000_000, category="salary", merchant="Payroll", days_ago=1)]
        result = check_payday_detected(txns, "C001")
        assert result is not None
        assert result.trigger_type == TriggerType.PAYDAY_DETECTED
        assert result.context["amount"] == 12_000_000

    def test_payday_not_detected_old(self) -> None:
        txns = [_make_txn(amount=12_000_000, category="salary", merchant="Payroll", days_ago=10)]
        result = check_payday_detected(txns, "C001")
        assert result is None

    def test_budget_threshold_fires(self) -> None:
        # Use day 1 and later in the same month to avoid cross-month issues
        today = date.today()
        base = today.replace(day=max(1, today.day - 1))
        txns = [
            Transaction(
                transaction_id="TX-salary", customer_id="C001", account_id="ACC-001",
                date=base.isoformat(), amount=10_000_000, category="salary", merchant="Payroll",
            ),
            Transaction(
                transaction_id="TX-food", customer_id="C001", account_id="ACC-001",
                date=today.isoformat(), amount=-4_000_000, category="food", merchant="Grab",
            ),
            Transaction(
                transaction_id="TX-shop", customer_id="C001", account_id="ACC-001",
                date=today.isoformat(), amount=-3_000_000, category="shopping", merchant="Shopee",
            ),
            Transaction(
                transaction_id="TX-bill", customer_id="C001", account_id="ACC-001",
                date=today.isoformat(), amount=-2_000_000, category="bills", merchant="Viettel",
            ),
        ]
        result = check_budget_threshold(txns, "C001")
        assert result is not None
        assert result.trigger_type == TriggerType.BUDGET_THRESHOLD

    def test_life_event_baby(self) -> None:
        txns = [
            _make_txn(merchant="Kids Plaza", category="shopping", days_ago=10),
            _make_txn(merchant="Con Cưng", category="shopping", days_ago=5),
        ]
        result = check_life_event_pattern(txns, "C001")
        assert result is not None
        assert result.trigger_type == TriggerType.LIFE_EVENT
        assert result.context["event_type"] == "baby"

    def test_life_event_home(self) -> None:
        txns = [
            _make_txn(merchant="Công ty BĐS Vinhomes", category="bills", days_ago=10),
            _make_txn(merchant="Nội thất IKEA VN", category="bills", days_ago=5),
        ]
        result = check_life_event_pattern(txns, "C001")
        assert result is not None
        assert result.context["event_type"] == "home_purchase"

class TestComplianceFilter:
    """Test compliance classification and gating."""

    def test_information_passes(self) -> None:
        text = "Tổng chi tiêu tháng 3: 12,500,000 VND. Ăn uống chiếm 33.6%."
        cls = classify_output(text)
        assert cls == ComplianceClass.INFORMATION

    def test_guidance_gets_disclaimer(self) -> None:
        text = "Bạn có thể cân nhắc mở tài khoản tiết kiệm có kỳ hạn."
        result, cls = apply_compliance(text)
        assert cls == ComplianceClass.GUIDANCE
        assert "thông tin tham khảo" in result

    def test_advice_blocked(self) -> None:
        text = "Bạn nên mua bảo hiểm nhân thọ Shinhan Life Protect ngay."
        result, cls = apply_compliance(text)
        assert cls == ComplianceClass.ADVICE
        assert "chuyên viên Shinhan" in result
        assert "nên mua" not in result

    def test_english_advice_blocked(self) -> None:
        text = "I recommend you invest in the Shinhan Bond Fund."
        result, cls = apply_compliance(text)
        assert cls == ComplianceClass.ADVICE

    def test_product_info_passes(self) -> None:
        text = "Thẻ tín dụng Shinhan Cashback có lãi suất 24%/năm, hoàn tiền 1%."
        cls = classify_output(text)
        assert cls == ComplianceClass.INFORMATION
