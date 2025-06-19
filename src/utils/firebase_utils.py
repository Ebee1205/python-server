# utils/firebase_utils.py

from google.cloud import firestore
from google.cloud.exceptions import GoogleCloudError
from typing import Dict, List, Any, Optional
import json

# 'firebase_' prefix

# 단일 문서 조회
# - collection_path: 컬렉션 경로 (예: 'users')
# - document_id: 문서 ID
# - return: 문서 데이터 딕셔너리 또는 None
async def firebase_get_document(ctx, collection_path: str, document_id: str) -> Optional[Dict[str, Any]]:
    """단일 문서를 조회합니다."""
    try:
        client = ctx.firebase_handler.get_client()
        doc_ref = client.collection(collection_path).document(document_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            ctx.log.debug("DB-firestore", f"== GET {collection_path}/{document_id} > found")
            return data
        else:
            ctx.log.debug("DB-firestore", f"== GET {collection_path}/{document_id} > not found")
            return None
            
    except GoogleCloudError as e:
        ctx.log.error("DB-firestore", f"-- GET error: {collection_path}/{document_id}, {str(e)}")
        return None

# 단일 문서 저장/업데이트
# - merge: True면 기존 필드 유지하고 새 필드만 추가/업데이트, False면 문서 전체 교체
# - return: 성공 시 True, 실패 시 False
async def firebase_set_document(ctx, collection_path: str, document_id: str, data: Dict[str, Any], merge: bool = True) -> bool:
    """단일 문서를 저장하거나 업데이트합니다."""
    try:
        client = ctx.firebase_handler.get_client()
        doc_ref = client.collection(collection_path).document(document_id)
        
        if merge:
            doc_ref.set(data, merge=True)
            ctx.log.debug("DB-firestore", f"!! SET (merge) {collection_path}/{document_id}")
        else:
            doc_ref.set(data)
            ctx.log.debug("DB-firestore", f"!! SET (replace) {collection_path}/{document_id}")
        
        return True
        
    except GoogleCloudError as e:
        ctx.log.error("DB-firestore", f"-- SET error: {collection_path}/{document_id}, {str(e)}")
        return False

# 문서 삭제
# - return: 성공 시 True, 실패 시 False
async def firebase_delete_document(ctx, collection_path: str, document_id: str) -> bool:
    """단일 문서를 삭제합니다."""
    try:
        client = ctx.firebase_handler.get_client()
        doc_ref = client.collection(collection_path).document(document_id)
        doc_ref.delete()
        
        ctx.log.debug("DB-firestore", f"!! DELETE {collection_path}/{document_id}")
        return True
        
    except GoogleCloudError as e:
        ctx.log.error("DB-firestore", f"-- DELETE error: {collection_path}/{document_id}, {str(e)}")
        return False

# 컬렉션 쿼리 (필터링)
# - filters: 필터 조건 리스트 [{'field': 'age', 'op': '>=', 'value': 18}]
# - order_by: 정렬 필드 (예: 'created_at')
# - limit: 결과 개수 제한
# - return: 문서 리스트 또는 빈 리스트
async def firebase_query_collection(ctx, collection_path: str, filters: List[Dict[str, Any]] = None, 
                                  order_by: str = None, limit: int = None, desc: bool = False) -> List[Dict[str, Any]]:
    """컬렉션을 쿼리합니다."""
    try:
        client = ctx.firebase_handler.get_client()
        query = client.collection(collection_path)
        
        # 필터 적용
        if filters:
            for filter_condition in filters:
                field = filter_condition['field']
                op = filter_condition['op']
                value = filter_condition['value']
                query = query.where(field, op, value)
        
        # 정렬 적용
        if order_by:
            direction = firestore.Query.DESCENDING if desc else firestore.Query.ASCENDING
            query = query.order_by(order_by, direction=direction)
        
        # 제한 적용
        if limit:
            query = query.limit(limit)
        
        # 쿼리 실행
        docs = query.stream()
        results = []
        
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['_id'] = doc.id  # 문서 ID 추가
            results.append(doc_data)
        
        ctx.log.debug("DB-firestore", f"== QUERY {collection_path} > {len(results)} results")
        return results
        
    except GoogleCloudError as e:
        ctx.log.error("DB-firestore", f"-- QUERY error: {collection_path}, {str(e)}")
        return []

# 문서 존재 여부 확인
# - return: 존재하면 True, 없으면 False
async def firebase_document_exists(ctx, collection_path: str, document_id: str) -> bool:
    """문서 존재 여부를 확인합니다."""
    try:
        client = ctx.firebase_handler.get_client()
        doc_ref = client.collection(collection_path).document(document_id)
        doc = doc_ref.get()
        
        exists = doc.exists
        ctx.log.debug("DB-firestore", f"== EXISTS {collection_path}/{document_id} > {exists}")
        return exists
        
    except GoogleCloudError as e:
        ctx.log.error("DB-firestore", f"-- EXISTS error: {collection_path}/{document_id}, {str(e)}")
        return False

# 문서에 새 필드 추가 (기존 필드 유지)
# - return: 성공 시 True, 실패 시 False
async def firebase_update_fields(ctx, collection_path: str, document_id: str, updates: Dict[str, Any]) -> bool:
    """문서의 특정 필드만 업데이트합니다."""
    try:
        client = ctx.firebase_handler.get_client()
        doc_ref = client.collection(collection_path).document(document_id)
        doc_ref.update(updates)
        
        ctx.log.debug("DB-firestore", f"!! UPDATE {collection_path}/{document_id} > {list(updates.keys())}")
        return True
        
    except GoogleCloudError as e:
        ctx.log.error("DB-firestore", f"-- UPDATE error: {collection_path}/{document_id}, {str(e)}")
        return False

# 배치 작업 (여러 문서를 한 번에 처리)
# - operations: 작업 리스트 [{'type': 'set', 'collection': 'users', 'doc_id': '1', 'data': {...}}]
# - return: 성공 시 True, 실패 시 False
async def firebase_batch_operations(ctx, operations: List[Dict[str, Any]]) -> bool:
    """배치 작업을 수행합니다."""
    try:
        client = ctx.firebase_handler.get_client()
        batch = client.batch()
        
        for op in operations:
            op_type = op['type']
            collection_path = op['collection']
            doc_id = op['doc_id']
            doc_ref = client.collection(collection_path).document(doc_id)
            
            if op_type == 'set':
                merge = op.get('merge', True)
                batch.set(doc_ref, op['data'], merge=merge)
            elif op_type == 'update':
                batch.update(doc_ref, op['data'])
            elif op_type == 'delete':
                batch.delete(doc_ref)
        
        batch.commit()
        ctx.log.debug("DB-firestore", f"!! BATCH > {len(operations)} operations")
        return True
        
    except GoogleCloudError as e:
        ctx.log.error("DB-firestore", f"-- BATCH error: {str(e)}")
        return False

# 자동 ID로 문서 생성
# - return: 성공 시 생성된 문서 ID, 실패 시 None
async def firebase_add_document(ctx, collection_path: str, data: Dict[str, Any]) -> Optional[str]:
    """자동 생성된 ID로 문서를 추가합니다."""
    try:
        client = ctx.firebase_handler.get_client()
        doc_ref = client.collection(collection_path).document()
        doc_ref.set(data)
        
        doc_id = doc_ref.id
        ctx.log.debug("DB-firestore", f"!! ADD {collection_path}/{doc_id}")
        return doc_id
        
    except GoogleCloudError as e:
        ctx.log.error("DB-firestore", f"-- ADD error: {collection_path}, {str(e)}")
        return None