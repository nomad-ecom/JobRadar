from app.db import init_db, get_sessionmaker
from app.services.pipeline import crawl_and_match


def main() -> None:
    init_db()
    session = get_sessionmaker()()
    try:
        runs = crawl_and_match(session)
    finally:
        session.close()
    for run in runs:
        print(f"{run.source}\t{run.status}\tfound={run.jobs_found}\tnew={run.jobs_new}\t{run.message}")


if __name__ == "__main__":
    main()
