"""Explicit local HTTP provider-contract fixtures, not live AI or unit tests."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from resolvedesk.generation_provider import ESCALATION_BODY, deepseek_reply

checks = []
case = {
    "reply": {
        "body": "Project membership is separate from workspace role.",
        "citation_ids": ["authorized-citation"],
        "outcome": "answer",
        "reason": "Review evidence.",
    },
    "status": "completed",
    "usage": {"input_tokens": 100, "output_tokens": 20},
}
requests = []


class ProviderFixture(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        requests.append(request)
        content = (
            [{"type": "refusal", "refusal": "declined"}]
            if case.get("refusal")
            else [{"type": "output_text", "text": json.dumps(case["reply"])}]
        )
        result = {
            "status": case["status"],
            "output": [{"type": "message", "content": content}],
            "usage": case["usage"],
        }
        result = case.get("envelope", result)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    checks.append(label)
    print("PASS", label)


server = ThreadingHTTPServer(("127.0.0.1", 0), ProviderFixture)
thread = Thread(target=server.serve_forever, daemon=True)
thread.start()
context = {
    "ticket": "Synthetic access question",
    "evidence": [
        {
            "citation_id": "authorized-citation",
            "version_id": "internal-source-version",
            "content": "Project membership is separate from workspace role.",
        }
    ],
}
endpoint = f"http://127.0.0.1:{server.server_port}/v1/responses"
try:
    reply, usage = deepseek_reply(context, "resolvedesk-provider-fixture", endpoint=endpoint)
    check(
        reply.citation_ids == ["authorized-citation"] and usage["input_tokens"] == 100,
        "Adapter parses strict reply and usage from actual local HTTP provider fixture",
    )
    sent = requests[-1]
    check(
        sent["model"] == "deepseek-flash"
        and sent["max_output_tokens"] == 2048
        and sent["text"]["format"]["strict"] is True,
        "Transport requests bounded strict structured output for the selected DeepSeek model",
    )
    check(
        "tools" not in sent and json.loads(sent["input"]) == context,
        "Provider receives only read-only scoped context; no mutation or network tools",
    )
    original = json.loads(json.dumps(case))
    case["reply"] = {
        "body": "I've flagged this and refunded your invoice.",
        "citation_ids": [],
        "outcome": "escalation",
        "reason": "No evidence. Human review needed.",
    }
    reply, usage = deepseek_reply(
        {"ticket": "Synthetic refund question", "evidence": []},
        "resolvedesk-provider-fixture",
        endpoint=endpoint,
    )
    check(
        reply.body == ESCALATION_BODY and usage["escalation_template_applied"],
        "Escalation uses application-owned wording without invented completed actions",
    )
    case.clear()
    case.update(original)
    for label, change in [
        (
            "Invented citation rejected",
            {"reply": {**original["reply"], "citation_ids": ["foreign-citation"]}},
        ),
        ("Uncited factual answer rejected", {"reply": {**original["reply"], "citation_ids": []}}),
        (
            "Internal citation IDs in customer reply rejected",
            {"reply": {**original["reply"], "body": "Policy says authorized-citation"}},
        ),
        (
            "Internal source-version IDs in customer reply rejected",
            {"reply": {**original["reply"], "body": "Policy says internal-source-version"}},
        ),
        ("Unknown schema field rejected", {"reply": {**original["reply"], "send_email": True}}),
        ("Incomplete provider response rejected", {"status": "incomplete"}),
        ("Provider refusal rejected", {"refusal": True}),
        ("Unknown provider usage rejected", {"usage": {}}),
        ("Non-object response envelope rejected", {"envelope": []}),
        ("Null output item rejected", {"envelope": {"status": "completed", "output": [None]}}),
        (
            "Null message content rejected",
            {"envelope": {"status": "completed", "output": [{"type": "message", "content": None}]}},
        ),
    ]:
        case.clear()
        case.update(original)
        case.update(change)
        rejected = False
        try:
            deepseek_reply(context, "resolvedesk-provider-fixture", endpoint=endpoint)
        except (ValueError, TypeError):
            rejected = True
        check(rejected, label)
    rejected = False
    try:
        deepseek_reply(context, "not-a-fixture-credential", endpoint=endpoint)
    except ValueError:
        rejected = True
    check(rejected, "Transport fixture cannot receive a real provider credential")
    print(
        f"\n{len(checks)} local HTTP provider-contract assertions passed. Canned boundary responses; no paid requests or model-quality claims."
    )
finally:
    server.shutdown()
    server.server_close()
    thread.join()
