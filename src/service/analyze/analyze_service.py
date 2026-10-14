# src/service/analyze/analyze_service.py

import asyncio
import json
import time

from fastapi import HTTPException

from src.app_context import AppContext
from src.llm.providers.llm_provider import LLMProviderError
from src.service.analyze.prompts.analyze_prompt import (
    STATE_ANALYSIS_PROMPT_TEMPLATE,
    STATE_ANALYSIS_SYSTEM_INSTRUCTION,
    MOCK_UP_RESPONSE
)
from src.service.session.session_schema import SessionStatus
from src.service.state import state_service


def _build_query_context(
    ctx: AppContext,
    query_context: dict | None = None,
) -> dict:
    now_ms = int(time.time() * 1000)

    base_context = {
        "rDate": now_ms,
        "timezone": getattr(ctx.cfg, "timezone", None) or "Asia/Seoul",
        "sessionTimeoutSec": 60,
        "sessionStatus": {
            str(SessionStatus.READY.value): {
                "code": "READY",
                "description": "세션 생성 후 진행 또는 종료 대기 상태",
            },
            str(SessionStatus.COMPLETED.value): {
                "code": "COMPLETED",
                "description": "사용자의 정상 종료 요청으로 완료된 세션",
            },
            str(SessionStatus.AUTO_TERM.value): {
                "code": "AUTO_TERM",
                "description": "데이터 미수신 등의 종료 조건으로 자동 종료된 세션",
            },
            str(SessionStatus.FAILED.value): {
                "code": "FAILED",
                "description": "처리 실패 상태로 기록된 세션",
            },
        },
    }

    merged = {
        **base_context,
        **(query_context or {}),
    }

    if merged.get("period") is None:
        merged.pop("period", None)

    return merged


def _to_pretty_json(data: dict) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def _build_state_analysis_prompt(
    state_summary: dict,
    session_state: dict,
    query_context: dict | None = None,
) -> str:
    return STATE_ANALYSIS_PROMPT_TEMPLATE.format(
        summary_json=_to_pretty_json(state_summary),
        session_json=_to_pretty_json(session_state),
        context_json=_to_pretty_json(query_context or {}),
    )


async def analyze_state(
    ctx: AppContext,
    query_context: dict | None = None,
) -> dict:
    if not ctx.db_handler:
        raise HTTPException(
            status_code=500,
            detail="Database not initialized",
        )

    llm_manager = getattr(ctx, "llm_manager", None)

    if llm_manager is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "LLM manager is not initialized. "
                "Check llm config and startup init."
            ),
        )

    state_summary, session_state = await asyncio.gather(
        asyncio.to_thread(state_service.get_state_summary, ctx),
        asyncio.to_thread(state_service.get_session_state, ctx),
    )

    analysis_context = _build_query_context(
        ctx,
        query_context,
    )

    prompt = _build_state_analysis_prompt(
        state_summary=state_summary,
        session_state=session_state,
        query_context=analysis_context,
    )

    try:
        analysis = await llm_manager.generate(
            prompt,
            system_instruction=STATE_ANALYSIS_SYSTEM_INSTRUCTION,
            temperature=0.1,
            max_output_tokens=768,
            thinking_level="low",
        )

    except Exception as exc:
        analysis = MOCK_UP_RESPONSE
        
    except LLMProviderError as exc:
        analysis = MOCK_UP_RESPONSE

    # except LLMProviderError as exc:
    #     raise HTTPException(
    #         status_code=502,
    #         detail=f"LLM provider error ({exc.code}): {exc}",
    #     ) from exc

    # except Exception as exc:
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"AI analysis failed: {exc}",
    #     ) from exc

    return {
        "analysis": analysis,
        # "source": {
        #     "stateSummary": state_summary,
        #     "sessionState": session_state,
        # },
        "analysisContext": analysis_context,
        "llm": {
            "provider": llm_manager.provider_name,
            "model": llm_manager.model_name,
        },
    }