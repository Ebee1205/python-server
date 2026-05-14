from typing import Optional

from pydantic import BaseModel, Field


class TagListRequest(BaseModel):
	"""태그 목록 조회 요청 스키마"""
	page: int = Field(1, ge=1, description="페이지 번호")
	limit: int = Field(20, ge=1, le=100, description="페이지 크기")
	parentCode: Optional[str] = Field(None, description="상위 태그 코드 필터")


class TagGetRequest(BaseModel):
	"""태그 상세 조회 요청 스키마"""
	id: int = Field(..., description="태그 ID")


class TagCreateRequest(BaseModel):
	"""태그 생성 요청 스키마"""
	userId: int = Field(..., description="태그 생성자 ID")
	parentCode: Optional[str] = Field(None, description="상위 태그 코드")
	code: str = Field(..., description="태그 식별 코드")
	tagName: str = Field(..., description="태그 표시 명칭")


class TagUpdateRequest(BaseModel):
	"""태그 수정 요청 스키마"""
	id: int = Field(..., description="태그 ID")
	parentCode: Optional[str] = Field(None, description="상위 태그 코드")
	tagName: Optional[str] = Field(None, description="태그 표시 명칭")


class TagDeleteRequest(BaseModel):
	"""태그 삭제 요청 스키마"""
	id: int = Field(..., description="태그 ID")


class TagItem(BaseModel):
	"""태그 아이템 스키마"""
	id: int = Field(..., description="태그 ID")
	userId: int = Field(..., description="태그 생성자 ID")
	parentCode: Optional[str] = Field(None, description="상위 태그 코드")
	code: str = Field(..., description="태그 식별 코드")
	tagName: str = Field(..., description="태그 표시 명칭")
	cDate: int = Field(..., description="생성 날짜 Unix timestamp")
	uDate: int = Field(..., description="수정 날짜 Unix timestamp")

	class Config:
		from_attributes = True


class TagListResponse(BaseModel):
	"""태그 목록 응답 스키마"""
	items: list[TagItem]
	total: int = Field(..., description="전체 개수")
	page: int = Field(..., description="현재 페이지")
	limit: int = Field(..., description="페이지 크기")

	class Config:
		from_attributes = True
