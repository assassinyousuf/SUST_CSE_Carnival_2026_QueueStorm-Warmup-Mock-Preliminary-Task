"""
Tests for QueueStorm. Run with:  python -m pytest -q   (or)   python tests/test_samples.py

Covers the 5 public sample cases, the agent_summary safety rule, full
response-schema integrity, and a few extra edge cases (Bangla, refund vs
wrong-transfer collisions, malformed input).
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

EXPECTED_FIELDS = {
    "ticket_id", "case_type", "severity", "department",
    "agent_summary", "human_review_required", "confidence",
}
CASE_TYPES = {"wrong_transfer", "payment_failed", "refund_request",
              "phishing_or_social_engineering", "other"}
SEVERITIES = {"low", "medium", "high", "critical"}
DEPARTMENTS = {"customer_support", "dispute_resolution", "payments_ops", "fraud_risk"}

FORBIDDEN = re.compile(r"(share|send|give|enter|tell|provide|your)\s+\w*\s*(pin|otp|password|cvv|card number)", re.I)

client = app.test_client()


def post(message, ticket_id="T-TEST", **extra):
    body = {"ticket_id": ticket_id, "message": message, **extra}
    resp = client.post("/sort-ticket", data=json.dumps(body), content_type="application/json")
    return resp.status_code, resp.get_json()


# ----- The 5 public sample cases -------------------------------------------
PUBLIC_SAMPLES = [
    ("I sent 3000 to wrong number", "wrong_transfer", "high"),
    ("Payment failed but balance deducted", "payment_failed", "high"),
    ("Someone called asking my OTP, is that bKash?", "phishing_or_social_engineering", "critical"),
    ("Please refund my last transaction, I changed my mind", "refund_request", "low"),
    ("App crashed when I opened it", "other", "low"),
]


def run():
    passed, failed = 0, 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  PASS  {name}")
        else:
            failed += 1
            print(f"  FAIL  {name}  {detail}")

    print("\n== Health endpoint ==")
    r = client.get("/health")
    check("GET /health returns 200", r.status_code == 200, f"got {r.status_code}")
    check("health body has status ok", r.get_json().get("status") == "ok")

    print("\n== Public sample cases ==")
    for msg, exp_type, exp_sev in PUBLIC_SAMPLES:
        code, body = post(msg)
        check(f"[200] {msg[:38]!r}", code == 200, f"got {code}")
        check(f"case_type == {exp_type}", body.get("case_type") == exp_type,
              f"got {body.get('case_type')}")
        check(f"severity  == {exp_sev}", body.get("severity") == exp_sev,
              f"got {body.get('severity')}")

    print("\n== Response schema integrity ==")
    _, body = post("I sent 5000 taka to a wrong number this morning, please help me get it back",
                   ticket_id="T-001")
    check("all fields present", set(body) == EXPECTED_FIELDS, f"got {set(body)}")
    check("ticket_id echoed", body["ticket_id"] == "T-001")
    check("case_type in enum", body["case_type"] in CASE_TYPES)
    check("severity in enum", body["severity"] in SEVERITIES)
    check("department in enum", body["department"] in DEPARTMENTS)
    check("human_review is bool", isinstance(body["human_review_required"], bool))
    check("confidence is float 0..1", isinstance(body["confidence"], (int, float))
          and 0.0 <= body["confidence"] <= 1.0)

    print("\n== Safety rule: agent_summary never asks for credentials ==")
    risky = [
        "Someone called asking my OTP, is that bKash?",
        "An agent told me to share my PIN and password to fix my account",
        "I got an SMS asking for my card number and CVV",
        "Please verify my OTP",
    ]
    for msg in risky:
        _, body = post(msg)
        summ = body["agent_summary"]
        check(f"summary safe for {msg[:34]!r}", not FORBIDDEN.search(summ), f"-> {summ!r}")

    print("\n== Routing / department checks ==")
    _, b = post("I sent 3000 to wrong number")
    check("wrong_transfer -> dispute_resolution", b["department"] == "dispute_resolution")
    _, b = post("Payment failed but balance deducted")
    check("payment_failed -> payments_ops", b["department"] == "payments_ops")
    _, b = post("Someone called asking my OTP")
    check("phishing -> fraud_risk", b["department"] == "fraud_risk")
    check("phishing -> human_review true", b["human_review_required"] is True)
    _, b = post("App crashed when I opened it")
    check("other -> customer_support", b["department"] == "customer_support")

    print("\n== Edge cases ==")
    # Refund + wrong-transfer collision should resolve to wrong_transfer.
    _, b = post("I sent money to the wrong number, please refund it")
    check("wrong+refund -> wrong_transfer", b["case_type"] == "wrong_transfer",
          f"got {b['case_type']}")
    # Bangla phishing.
    _, b = post("কেউ আমার ওটিপি চাইছে, এটা কি বিকাশ?")
    check("bangla OTP -> phishing", b["case_type"] == "phishing_or_social_engineering",
          f"got {b['case_type']}")
    # Contested refund -> disputes + higher severity.
    _, b = post("I want a refund, the product was never delivered and the merchant refuses")
    check("contested refund -> dispute_resolution", b["department"] == "dispute_resolution")
    check("contested refund -> high severity", b["severity"] == "high", f"got {b['severity']}")
    # Malformed input.
    code, _ = post("", ticket_id="T-9")
    check("empty message -> 400", code == 400, f"got {code}")
    r = client.post("/sort-ticket", data="not json", content_type="application/json")
    check("non-json body -> 400", r.status_code == 400, f"got {r.status_code}")
    r = client.post("/sort-ticket", data=json.dumps({"message": "hi"}), content_type="application/json")
    check("missing ticket_id -> 400", r.status_code == 400, f"got {r.status_code}")

    print(f"\n{'='*46}\n  RESULT: {passed} passed, {failed} failed\n{'='*46}")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
