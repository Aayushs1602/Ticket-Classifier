
# classifier.py
import re
import os
import random
from typing import List, Dict, Tuple

# Optional ML model integration (if you trained a classifier)
try:
    import joblib
    HAS_JOBLIB = True
except Exception:
    HAS_JOBLIB = False

# Optional local LLM rephrasing (instruction-tuned)
USE_LOCAL_LLM = False
try:
    from transformers import pipeline
    # Instruction-tuned small model for nicer paraphrase (optional)
    LLM_MODEL_NAME = "google/flan-t5-small"  # small, instruction-tuned
    LLM_PIPELINE = None
    USE_LOCAL_LLM = True
except Exception:
    LLM_PIPELINE = None
    USE_LOCAL_LLM = False


# ---------- Keywords & weights (tunable) ----------
AI_KEYWORDS = {
    "error": 2, "exception": 3, "traceback": 3, "crash": 3,
    "nullpointer": 4, "typeerror": 3, "stack trace": 3,
    "failed test": 2, "segfault": 4, "bug": 2, "assertion": 2,
    "timeout": 1, "memory leak": 3, "model failure": 3, "exception:": 3
}

WF_KEYWORDS = {
    "config": 3, "configuration": 3, "permission": 3, "access": 3,
    "api key": 3, "authentication": 3, "login": 2, "dashboard": 2,
    "connectivity": 2, "integration": 2, "rate limit": 2, "timeout": 1,
    "credential": 3, "quota": 2, "network": 2
}

# Regex patterns to detect stack traces or code-like snippets
STACKTRACE_PATTERNS = [
    r"traceback \(most recent call last\):",
    r"at \w+\.\w+\(",
    r"exception:",
    r"stack trace"
]


# ---------- Helpers ----------
def _word_match(text: str, phrase: str) -> bool:
    """Safe word-boundary match of phrase in text."""
    # escape the phrase for regex, allow spaces
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


def extract_matches_and_scores(summary: str) -> Tuple[List[str], List[str], int, int]:
    s = summary.lower()
    ai_matches = []
    wf_matches = []
    ai_score = 0
    wf_score = 0

    # match AI keywords
    for k, w in AI_KEYWORDS.items():
        if _word_match(s, k):
            ai_matches.append(k)
            ai_score += w

    # match WF keywords
    for k, w in WF_KEYWORDS.items():
        if _word_match(s, k):
            wf_matches.append(k)
            wf_score += w

    # stacktrace boost
    for pat in STACKTRACE_PATTERNS:
        if re.search(pat, s):
            ai_matches.append("stacktrace_pattern")
            ai_score += 3

    return ai_matches, wf_matches, ai_score, wf_score


def severity_multiplier(severity: str) -> float:
    sev = (severity or "").lower()
    return {"low": 0.9, "medium": 1.0, "high": 1.2}.get(sev, 1.0)


def channel_influence(channel: str) -> Tuple[int, int]:
    """Return (ai_boost, wf_boost) based on channel heuristics."""
    ch = (channel or "").lower()
    if ch == "chat":
        return (0, 1)  # quick troubleshooting often workflow
    if ch == "phone":
        return (0, 1)
    if ch == "email":
        return (1, 0)
    # default neutral for web/other
    return (0, 0)


# ---------- Deterministic reasoning & checklist ----------
def generate_structured_reasoning(ticket: Dict, decision: str,
                                  ai_matches: List[str], wf_matches: List[str],
                                  ai_score: int, wf_score: int) -> str:
    summary = ticket.get("summary", "").strip()
    severity = ticket.get("severity", "unknown").lower()
    channel = ticket.get("channel", "unknown")

    evidences = []
    if ai_matches:
        evidences.append(f"code-related keywords detected ({', '.join(ai_matches)})")
    if wf_matches:
        evidences.append(f"config/workflow keywords detected ({', '.join(wf_matches)})")
    evidences.append(f"severity={severity}")
    evidences.append(f"ai_score={ai_score}, wf_score={wf_score}")

    evidence_str = "; ".join(evidences)
    reason = (
        f"Decision: {decision}. Reason: the ticket summary '{summary}' shows {evidence_str}. "
        f"Based on the higher score, {decision} is recommended."
    )
    return reason


def generate_dynamic_checklist(ticket: Dict, decision: str,
                               ai_matches: List[str], wf_matches: List[str]) -> List[str]:
    """
    Return 3-6 prioritized actionable steps, augmented by matched keywords.
    Deterministic and human-readable.
    """
    base_ai = [
        "Reproduce the failure in staging and capture logs/stack trace.",
        "Attach stack trace, failing input, and last known good commit.",
        "Run unit/integration tests for the implicated module.",
        "Generate proposed code patch and run CI.",
        "Deploy patch to sandbox and monitor relevant metrics."
    ]
    base_wf = [
        "Verify configuration in the admin dashboard and confirm values.",
        "Check and validate user permissions and roles.",
        "Confirm connectivity and API credential status.",
        "Re-run the workflow end-to-end in staging.",
        "Update troubleshooting docs and inform support team."
    ]

    extra = []
    s = ticket.get("summary", "").lower()
    if _word_match(s, "api key") or _word_match(s, "apikey") or _word_match(s, "api-key"):
        extra.append("Validate API key (existence, expiry, scope); rotate/regenerate if needed.")
    if any(k in ai_matches for k in ["nullpointer", "typeerror", "segfault", "memory leak"]):
        extra.append("Pinpoint failing code line via stack trace and review recent commits.")
    if _word_match(s, "permission") or _word_match(s, "access"):
        extra.append("Check user/group memberships and any recent IAM changes.")
    if _word_match(s, "timeout") and decision == "AI_PATCH":
        extra.append("Review retry/backoff logic and error handling in code.")
    if _word_match(s, "timeout") and decision == "VIBE_WORKFLOW":
        extra.append("Inspect network and gateway configs for throttling or rate limits.")

    steps = base_ai if decision == "AI_PATCH" else base_wf
    # deterministic ordering: keep base steps then extras
    combined = steps + extra
    # deduplicate while preserving order
    seen = set()
    ordered = []
    for item in combined:
        if item not in seen:
            seen.add(item)
            ordered.append(item)

    # limit to 5 steps for brevity
    return ordered[:5]


# ---------- Optional: local LLM paraphrase (nice prose, optional) ----------
def _maybe_load_llm_pipeline():
    global LLM_PIPELINE
    if not USE_LOCAL_LLM:
        return None
    if LLM_PIPELINE is None:
        try:
            # text2text-generation is appropriate for instruction-tuned T5-style models
            LLM_PIPELINE = pipeline("text2text-generation", model=LLM_MODEL_NAME)
        except Exception as e:
            print("Warning: could not initialize local LLM pipeline:", e)
            LLM_PIPELINE = None
    return LLM_PIPELINE


def rephrase_with_local_llm(text: str) -> str:
    pipe = _maybe_load_llm_pipeline()
    if not pipe:
        return text
    try:
        # Keep it deterministic-ish and short
        out = pipe(text, max_length=200, do_sample=False)
        return out[0]["generated_text"].strip()
    except Exception as e:
        print("Warning: local LLM rephrase failed:", e)
        return text


# ---------- Top-level classifier -----------

def classify_ticket(ticket: Dict, use_trained_model: bool = False,
                    use_llm_rephrase: bool = False) -> Dict:
    """
    Main entrypoint.

    - If a trained sklearn classifier exists (vectorizer.pkl + classifier.pkl) and
      use_trained_model=True, it will be used for the high-level decision.
    - Otherwise, a weighted heuristic decides.
    - Deterministic reasoning & checklist are always produced.
    - Optionally the reasoning can be rephrased via an instruction-tuned local model.
    """
    summary = ticket.get("summary", "")
    severity = ticket.get("severity", "medium")
    channel = ticket.get("channel", "web")

    # Try to use trained model if requested and available
    model_decision = None
    if use_trained_model and HAS_JOBLIB and os.path.exists("vectorizer.pkl") and os.path.exists("classifier.pkl"):
        try:
            vec = joblib.load("vectorizer.pkl")
            clf = joblib.load("classifier.pkl")
            text = summary + " | " + severity + " | " + channel
            X = vec.transform([text])
            model_decision = clf.predict(X)[0]
        except Exception as e:
            print("Warning: failed to load/use trained model:", e)
            model_decision = None

    # Heuristic fallback:
    ai_matches, wf_matches, ai_score, wf_score = extract_matches_and_scores(summary)
    # apply severity multiplier
    mult = severity_multiplier(severity)
    ai_score = int(ai_score * mult)
    wf_score = int(wf_score * mult)

    # channel influence
    ai_boost, wf_boost = channel_influence(channel)
    ai_score += ai_boost
    wf_score += wf_boost

    # Final decision:
    if model_decision:
        decision = model_decision
    else:
        if ai_score > wf_score:
            decision = "AI_PATCH"
        elif wf_score > ai_score:
            decision = "VIBE_WORKFLOW"
        else:
            # tie-breaker: prefer VIBE_WORKFLOW for credential/config issues;
            # otherwise prefer AI_PATCH if any AI keywords existed
            if any(k in summary.lower() for k in ["api key", "permission", "config", "authentication"]):
                decision = "VIBE_WORKFLOW"
            elif ai_matches and not wf_matches:
                decision = "AI_PATCH"
            else:
                # default conservative: VIBE_WORKFLOW
                decision = "VIBE_WORKFLOW"

    reasoning = generate_structured_reasoning(ticket, decision, ai_matches, wf_matches, ai_score, wf_score)
    checklist = generate_dynamic_checklist(ticket, decision, ai_matches, wf_matches)

    if use_llm_rephrase:
        reasoning = rephrase_with_local_llm(reasoning)
        # optionally rephrase each checklist item
        try:
            pipe = _maybe_load_llm_pipeline()
            if pipe:
                # create a short prompt to rephrase checklist concisely
                new_items = []
                for item in checklist:
                    prompt = f"Rephrase this troubleshooting step concisely and clearly: \"{item}\""
                    out = pipe(prompt, max_length=80, do_sample=False)
                    new_items.append(out[0]["generated_text"].strip())
                checklist = new_items
        except Exception:
            pass

    return {
        "decision": decision,
        "reasoning": reasoning,
        "checklist": checklist,
        "meta": {
            "ai_matches": ai_matches,
            "wf_matches": wf_matches,
            "ai_score": ai_score,
            "wf_score": wf_score
        }
    }


# ---------- quick demo if run as script ----------
if __name__ == "__main__":
    samples = [
        {"channel": "email", "severity": "high", "summary": "Payment module crashes with NullPointerException"},
        {"channel": "chat", "severity": "medium", "summary": "User unable to access dashboard due to wrong config"},
        {"channel": "web", "severity": "high", "summary": "Script failed due to missing API key"},
    ]

    for s in samples:
        out = classify_ticket(s, use_trained_model=False, use_llm_rephrase=False)
        print("Input:", s)
        print("Output:", out)
        print("-" * 80)
