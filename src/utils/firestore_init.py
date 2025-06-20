# src/utils/firestore_init.py

def init_firestore_schema(ctx):
    """
    Firestore에 다음 구조를 초기화합니다:

    /stats/ALL           (문서)
    /stats/lint
    /stats/transform
    /stats/sweep
    /stats/single
    /stats/batch

    /pattern/template    (컬렉션)
    /pattern/results     (컬렉션)
    """
    # ctx에서 초기화된 Firestore 클라이언트 가져오기
    db = ctx.fb_handler.get_client()

    # stats 초기화
    stats_docs = ["ALL", "lint", "transform", "sweep", "single", "batch"]
    stats_coll = db.collection("stats")

    for name in stats_docs:
        stats_coll.document(name).set({"count": 0}, merge=True)

    ctx.log.debug("DB-firestore", "Completed initialization of 'stats' collection documents")

    # (옵션) pattern/template 및 pattern/results 컬렉션 초기화용 _init 문서 생성
    # db.collection("pattern").collection("template").document("_init").set({"initialized": True})
    # ctx.log.debug("[DB-firestore]     Created pattern/template/_init placeholder document")

    # (옵션) db.collection("pattern").collection("results").document("_init").set({"initialized": True})
    # ctx.log.debug("[DB-firestore]     Created pattern/results/_init placeholder document")

    # (옵션) tasks 컬렉션에 빈 상태 표시용 문서 추가
    # db.collection("tasks").document("_init").set({"initialized": True})
    # ctx.log.info("[DB-firestore] Created tasks/_init placeholder document")
