from typing import Optional

from pydantic import BaseModel, Field


class AnalyzePeriod(BaseModel):
    from_ts: Optional[int] = Field(None, alias="from", description="조회 시작 시각 (Unix ms)")
    to: Optional[int] = Field(None, description="조회 종료 시각 (Unix ms)")


class AnalyzeQueryContext(BaseModel):
    rDate: Optional[int] = Field(None, description="요청 시각 (Unix ms)")
    period: Optional[AnalyzePeriod] = Field(None, description="조회 기간")
    timezone: Optional[str] = Field(None, description="시각 해석 타임존")
    sessionTimeoutSec: Optional[int] = Field(
        None,
        ge=0,
        description="장기 미수신 판단 기준(초)",
    )
    flushIntervalSec: Optional[int] = Field(
        None,
        ge=0,
        description="Redis flush 기대 주기(초)",
    )


class AnalyzeStateRequest(BaseModel):
    queryCtx: Optional[AnalyzeQueryContext] = Field(
        None,
        description="LLM 분석 보조 메타데이터",
    )
