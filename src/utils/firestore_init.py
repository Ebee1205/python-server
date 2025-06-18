# src/utils/firestore_init.py

def init_firestore_schema(ctx):
    """
    Firestore에 다음 구조를 초기화합니다:

    /tasks               (컬렉션)            ← 문서를 따로 만들지 않고 비워둡니다.
    /stats/ALL           (문서)
    /stats/lint
    /stats/transform
    /stats/sweep
    /stats/single
    /stats/batch
    """
    # ctx에서 초기화된 Firestore 클라이언트 가져오기
    db = ctx.fb_handler.get_client()

    stats_docs = ["ALL", "lint", "transform", "sweep", "single", "batch"]
    stats_coll = db.collection("stats")

    for name in stats_docs:
        # 문서가 없으면 생성, 있으면 count 필드만 병합(set merge)
        stats_coll.document(name).set({"count": 0}, merge=True)
        ctx.log.debug(f"[DB-firestore]     Initialized stats/{name} with count=0")

    # 전체 stats 초기화 완료 로그
    ctx.log.debug("[DB-firestore]     Completed initialization of 'stats' collection documents")

    # (옵션) tasks 컬렉션에 빈 상태 표시용 문서 추가
    # db.collection("tasks").document("_init").set({"initialized": True})
    # ctx.log.info("[DB-firestore] Created tasks/_init placeholder document")