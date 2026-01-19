from app.db.session import Base, engine
import app.db.models  


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()