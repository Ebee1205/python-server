import time

from fastapi import HTTPException

from src.app_context import AppContext
from src.utils.db_utils import execute_query
from src.service.tag.tag_schema import (
	TagCreateRequest,
	TagItem,
	TagListResponse,
	TagUpdateRequest,
)


def _row_to_tag_item(row: tuple) -> TagItem:
	return TagItem(
		id=row[0],
		userId=row[1],
		parentCode=row[2],
		code=row[3],
		tagName=row[4],
		cDate=row[5],
		uDate=row[6],
	)


def list_tags(
	ctx: AppContext,
	page: int = 1,
	limit: int = 20,
	parent_code: str | None = None,
) -> TagListResponse:
	"""태그 목록 조회"""
	if ctx.log:
		ctx.log.debug(f"Tag list requested | page={page} limit={limit} parent_code={parent_code}")

	if not ctx.db_handler:
		raise HTTPException(status_code=500, detail="Database not initialized")

	offset = (page - 1) * limit

	if parent_code is not None:
		count_sql = "SELECT COUNT(*) FROM tb_tag WHERE parentCode = %s"
		count_params = (parent_code,)
		list_sql = """
			SELECT id, userId, parentCode, code, tagName, cDate, uDate
			FROM tb_tag
			WHERE parentCode = %s
			ORDER BY cDate ASC
			LIMIT %s OFFSET %s
		"""
		list_params = (parent_code, limit, offset)
	else:
		count_sql = "SELECT COUNT(*) FROM tb_tag"
		count_params = ()
		list_sql = """
			SELECT id, userId, parentCode, code, tagName, cDate, uDate
			FROM tb_tag
			ORDER BY cDate ASC
			LIMIT %s OFFSET %s
		"""
		list_params = (limit, offset)

	count_rows = execute_query(ctx.db_handler, count_sql, count_params)
	total = count_rows[0][0] if count_rows else 0

	rows = execute_query(ctx.db_handler, list_sql, list_params)
	items = [_row_to_tag_item(row) for row in rows]

	return TagListResponse(items=items, total=total, page=page, limit=limit)


def get_tag(ctx: AppContext, tag_id: int) -> TagItem:
	"""태그 상세 조회"""
	if ctx.log:
		ctx.log.debug(f"Tag get requested | tag_id={tag_id}")

	if not ctx.db_handler:
		raise HTTPException(status_code=500, detail="Database not initialized")

	sql = """
		SELECT id, userId, parentCode, code, tagName, cDate, uDate
		FROM tb_tag
		WHERE id = %s
	"""
	rows = execute_query(ctx.db_handler, sql, (tag_id,))
	if not rows:
		raise HTTPException(status_code=404, detail="Tag not found")

	return _row_to_tag_item(rows[0])


def create_tag(ctx: AppContext, payload: TagCreateRequest) -> TagItem:
	"""태그 생성"""
	if ctx.log:
		ctx.log.debug(f"Tag create requested | code={payload.code}")

	if not ctx.db_handler:
		raise HTTPException(status_code=500, detail="Database not initialized")

	# code 중복 확인
	dup_rows = execute_query(ctx.db_handler, "SELECT id FROM tb_tag WHERE code = %s", (payload.code,))
	if dup_rows:
		raise HTTPException(status_code=400, detail="Tag code already exists")

	# parentCode 존재 확인
	if payload.parentCode is not None:
		parent_rows = execute_query(ctx.db_handler, "SELECT code FROM tb_tag WHERE code = %s", (payload.parentCode,))
		if not parent_rows:
			raise HTTPException(status_code=400, detail="Parent tag code not found")

	now = int(time.time())

	sql = """
		INSERT INTO tb_tag (userId, parentCode, code, tagName, cDate, uDate)
		VALUES (%s, %s, %s, %s, %s, %s)
	"""
	params = (payload.userId, payload.parentCode, payload.code, payload.tagName, now, now)

	conn = ctx.db_handler.get_connection()
	new_id: int | None = None
	try:
		with conn.cursor() as cursor:
			cursor.execute(sql, params)
			new_id = cursor.lastrowid
		conn.commit()
	except Exception as e:
		conn.rollback()
		if ctx.log:
			ctx.log.error(f"Failed to create tag: {e}")
		raise HTTPException(status_code=500, detail="Failed to create tag")

	return TagItem(
		id=new_id,
		userId=payload.userId,
		parentCode=payload.parentCode,
		code=payload.code,
		tagName=payload.tagName,
		cDate=now,
		uDate=now,
	)


def update_tag(ctx: AppContext, payload: TagUpdateRequest) -> TagItem:
	"""태그 수정"""
	if ctx.log:
		ctx.log.debug(f"Tag update requested | id={payload.id}")

	if not ctx.db_handler:
		raise HTTPException(status_code=500, detail="Database not initialized")

	rows = execute_query(
		ctx.db_handler,
		"SELECT id, userId, parentCode, code, tagName, cDate, uDate FROM tb_tag WHERE id = %s",
		(payload.id,),
	)
	if not rows:
		raise HTTPException(status_code=404, detail="Tag not found")

	# parentCode 존재 확인
	if payload.parentCode is not None:
		parent_rows = execute_query(ctx.db_handler, "SELECT code FROM tb_tag WHERE code = %s", (payload.parentCode,))
		if not parent_rows:
			raise HTTPException(status_code=400, detail="Parent tag code not found")

	fields = []
	params = []
	if payload.parentCode is not None:
		fields.append("parentCode = %s")
		params.append(payload.parentCode)
	if payload.tagName is not None:
		fields.append("tagName = %s")
		params.append(payload.tagName)

	if not fields:
		raise HTTPException(status_code=400, detail="No fields to update")

	now = int(time.time())
	fields.append("uDate = %s")
	params.append(now)
	params.append(payload.id)

	sql = f"UPDATE tb_tag SET {', '.join(fields)} WHERE id = %s"
	conn = ctx.db_handler.get_connection()
	try:
		with conn.cursor() as cursor:
			cursor.execute(sql, params)
		conn.commit()
	except Exception as e:
		conn.rollback()
		if ctx.log:
			ctx.log.error(f"Failed to update tag: {e}")
		raise HTTPException(status_code=500, detail="Failed to update tag")

	updated_rows = execute_query(
		ctx.db_handler,
		"SELECT id, userId, parentCode, code, tagName, cDate, uDate FROM tb_tag WHERE id = %s",
		(payload.id,),
	)
	return _row_to_tag_item(updated_rows[0])
def delete_tag(ctx: AppContext, tag_id: int) -> dict:
	"""태그 삭제"""
	if ctx.log:
		ctx.log.debug(f"Tag delete requested | tag_id={tag_id}")

	if not ctx.db_handler:
		raise HTTPException(status_code=500, detail="Database not initialized")

	rows = execute_query(ctx.db_handler, "SELECT id FROM tb_tag WHERE id = %s", (tag_id,))
	if not rows:
		raise HTTPException(status_code=404, detail="Tag not found")

	conn = ctx.db_handler.get_connection()
	try:
		with conn.cursor() as cursor:
			cursor.execute("DELETE FROM tb_tag WHERE id = %s", (tag_id,))
		conn.commit()
	except Exception as e:
		conn.rollback()
		if ctx.log:
			ctx.log.error(f"Failed to delete tag: {e}")
		raise HTTPException(status_code=500, detail="Failed to delete tag")

	return {"id": tag_id, "deleted": True}
