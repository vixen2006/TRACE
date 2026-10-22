"""
Single-agent bounded execution loop.
The LLM decides which tool to call; Python executes, validates, and enforces limits.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Optional
from uuid import UUID

from openai import AsyncOpenAI

from app.agent.prompts import SYSTEM_PROMPT, TOOL_CALL_GUIDANCE
from app.agent.state import AgentReport, AgentRunState, ContributionClaim, EvidenceGap, RunStatus
from app.agent.tools import TOOL_REGISTRY, TOOL_SCHEMAS
from app.core.config import settings


class AgentOrchestrator:
    """
    Bounded agent execution loop.
    - Max tool calls: settings.agent_max_tool_calls
    - Max seconds: settings.agent_max_seconds
    - No direct DB access or shell execution by the LLM
    - Every tool call validated before execution
    """

    def __init__(self, encrypted_token: str, github_handle: str):
        self.client = AsyncOpenAI(api_key=settings.llm_api_key)
        self.encrypted_token = encrypted_token
        self.github_handle = github_handle

    async def run(
        self, state: AgentRunState
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Execute the agent loop, yielding SSE-compatible event dicts.
        Caller persists state and streams events to the frontend.
        """
        state.status = RunStatus.running
        start_time = time.monotonic()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + TOOL_CALL_GUIDANCE},
            {
                "role": "user",
                "content": (
                    f"Goal: {state.goal}\n"
                    f"Date range: {state.date_range.get('start')} to {state.date_range.get('end')}\n"
                    f"User GitHub handle: {self.github_handle}\n"
                    "Investigate and produce a verified engineering report."
                ),
            },
        ]

        yield {"event": "run_started", "run_id": state.run_id, "goal": state.goal}

        while True:
            # ── Enforce execution limits ──────────────────────────────────────
            elapsed = time.monotonic() - start_time
            if state.tool_call_count >= settings.agent_max_tool_calls:
                yield {"event": "limit_reached", "reason": "max_tool_calls", "count": state.tool_call_count}
                break
            if elapsed > settings.agent_max_seconds:
                yield {"event": "limit_reached", "reason": "timeout", "elapsed_seconds": int(elapsed)}
                break

            # ── Call the LLM ──────────────────────────────────────────────────
            try:
                response = await self.client.chat.completions.create(
                    model=settings.llm_model,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                    temperature=0,
                )
            except Exception as exc:
                state.status = RunStatus.failed
                state.error = str(exc)
                yield {"event": "error", "message": str(exc)}
                return

            choice = response.choices[0]
            messages.append(choice.message.model_dump(exclude_none=True))

            # ── No tool call → model is done ──────────────────────────────────
            if not choice.message.tool_calls:
                yield {"event": "model_finished", "content": choice.message.content or ""}
                break

            # ── Execute each tool call ────────────────────────────────────────
            for tc in choice.message.tool_calls:
                tool_name = tc.function.name
                yield {"event": "tool_started", "tool": tool_name, "call_id": tc.id}

                # Authorization: only registered tools may be called
                if tool_name not in TOOL_REGISTRY:
                    result = {"error": f"Tool '{tool_name}' is not registered."}
                    yield {"event": "tool_error", "tool": tool_name, "error": result["error"]}
                else:
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                        # Inject runtime context that the LLM should not supply
                        fn = TOOL_REGISTRY[tool_name]
                        kwargs: dict = {}
                        if tool_name in {"list_repositories", "fetch_pull_requests", "get_pr_details",
                                         "fetch_commits", "fetch_reviews", "fetch_issues"}:
                            kwargs["encrypted_token"] = self.encrypted_token
                        if tool_name == "validate_contribution":
                            kwargs["github_handle"] = self.github_handle

                        result = await fn(state=state, **args, **kwargs)
                        yield {"event": "tool_completed", "tool": tool_name, "summary": str(result)[:200]}

                    except Exception as exc:
                        result = {"error": str(exc)}
                        yield {"event": "tool_error", "tool": tool_name, "error": str(exc)}

                # Feed result back to the model
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })

        # ── Build report from final model message ─────────────────────────────
        report = self._build_report(state, messages)
        state.status = RunStatus.completed
        yield {"event": "run_completed", "run_id": state.run_id, "report": report.model_dump(mode="json")}

    def _build_report(self, state: AgentRunState, messages: list) -> AgentReport:
        """Assemble the final structured report from validated claims in state."""
        shipped = [c for c in state.claims if c.status == "shipped"]
        in_progress = [c for c in state.claims if c.status == "in_progress"]
        decisions = [c for c in state.claims if c.contribution_role == "decision_maker"]
        problems = [c for c in state.claims if c.contribution_role == "problem_solver"]

        return AgentReport(
            run_id=state.run_id,
            period_start=None,
            period_end=None,
            report_type="weekly_summary",
            shipped=shipped,
            in_progress=in_progress,
            decisions=decisions,
            problems_solved=problems,
            evidence_gaps=state.unresolved_gaps,
            summary_text=f"Investigated {state.tool_call_count} data points. "
                         f"{len(shipped)} shipped, {len(in_progress)} in progress. "
                         f"{len(state.unresolved_gaps)} evidence gaps flagged.",
            confidence_overall=sum(c.confidence for c in state.claims) / max(len(state.claims), 1),
            generated_at=datetime.now(timezone.utc),
        )
