from __future__ import annotations

import argparse

from app.db.session import get_session, init_db
from app.services.ingestion.ingestion_service import IngestionService


def main() -> None:
    parser = argparse.ArgumentParser(description="Reindex resumes for a role bucket")
    parser.add_argument("--role", required=True, help="Role bucket to index")
    parser.add_argument("--reindex", action="store_true", help="Recreate vector collection before indexing")
    args = parser.parse_args()
    init_db()
    with get_session() as session:
        service = IngestionService(session)
        result = service.ingest_role_bucket(args.role, reindex=args.reindex)
        print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
