from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    DateTime,
    Text,
    inspect,
    text,
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)

from datetime import datetime

from pathlib import Path


# =========================================
# DATABASE DIRECTORY
# =========================================

DATABASE_DIR = Path("data")

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================
# DATABASE URL
# =========================================

DATABASE_URL = (
    "sqlite:///./data/documind.db"
)


# =========================================
# DATABASE ENGINE
# =========================================

engine = create_engine(

    DATABASE_URL,

    connect_args={
        "check_same_thread": False
    }
)


# =========================================
# SESSION
# =========================================

SessionLocal = sessionmaker(

    autocommit=False,

    autoflush=False,

    bind=engine
)


# =========================================
# BASE
# =========================================

Base = declarative_base()


# =========================================
# USER MODEL
# =========================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        String,
        primary_key=True,
        index=True
    )

    email = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    password_hash = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # =====================================
    # SUBSCRIPTION
    # =====================================

    plan = Column(
        String,
        default="free",
        nullable=False
    )

    subscription_status = Column(
        String,
        default="active",
        nullable=False
    )

    # =====================================
    # USAGE LIMITS
    # =====================================

    questions_used = Column(
        Integer,
        default=0,
        nullable=False
    )

    question_limit = Column(
        Integer,
        default=20,
        nullable=False
    )

    document_limit = Column(
        Integer,
        default=3,
        nullable=False
    )

    max_file_size_mb = Column(
        Integer,
        default=5,
        nullable=False
    )

    # =====================================
    # SUBSCRIPTION DATES
    # =====================================

    subscription_started_at = Column(
        DateTime,
        nullable=True
    )

    subscription_expires_at = Column(
        DateTime,
        nullable=True
    )


# =========================================
# DOCUMENT MODEL
# =========================================

class Document(Base):

    __tablename__ = "documents"

    id = Column(
        String,
        primary_key=True,
        index=True
    )

    user_id = Column(
        String,
        nullable=False,
        index=True
    )

    filename = Column(
        String,
        nullable=False
    )

    file_path = Column(
        String,
        nullable=False
    )

    pages = Column(
        Integer,
        nullable=False
    )

    chunks = Column(
        Integer,
        nullable=False
    )

    status = Column(
        String,
        default="ready"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# =========================================
# CHAT HISTORY MODEL
# =========================================

class ChatMessage(Base):

    __tablename__ = "chat_messages"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = Column(
        String,
        nullable=False,
        index=True
    )

    document_id = Column(
        String,
        nullable=False,
        index=True
    )

    question = Column(
        Text,
        nullable=False
    )

    answer = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

# =========================================
# PAYMENT MODEL
# =========================================

class Payment(Base):

    __tablename__ = "payments"

    id = Column(
        String,
        primary_key=True,
        index=True
    )

    user_id = Column(
        String,
        nullable=False,
        index=True
    )

    payment_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    order_id = Column(
        String,
        nullable=True
    )

    amount = Column(
        Integer,
        nullable=False
    )

    currency = Column(
        String,
        default="INR",
        nullable=False
    )

    status = Column(
        String,
        default="created",
        nullable=False
    )

    plan = Column(
        String,
        default="premium",
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    paid_at = Column(
        DateTime,
        nullable=True
    )

# =========================================
# CREATE TABLES
# =========================================
#
# Existing tables are preserved.
#
# SQLAlchemy will create the new "payments"
# table if it does not already exist.
#
# =========================================

Base.metadata.create_all(bind=engine)
# =========================================
# DATABASE MIGRATION
# =========================================
#
# Existing SQLite databases do not
# automatically receive newly added
# SQLAlchemy columns.
#
# This function safely adds missing
# subscription columns to the existing
# users table.
#
# =========================================

def migrate_user_subscription_columns():

    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():

        return

    existing_columns = {

        column["name"]

        for column in inspector.get_columns(
            "users"
        )

    }

    columns_to_add = {

        "plan":
            "VARCHAR DEFAULT 'free'",

        "subscription_status":
            "VARCHAR DEFAULT 'active'",

        "questions_used":
            "INTEGER DEFAULT 0",

        "question_limit":
            "INTEGER DEFAULT 20",

        "document_limit":
            "INTEGER DEFAULT 3",

        "max_file_size_mb":
            "INTEGER DEFAULT 5",

        "subscription_started_at":
            "DATETIME",

        "subscription_expires_at":
            "DATETIME"

    }

    with engine.begin() as connection:

        for column_name, column_definition in columns_to_add.items():

            if column_name not in existing_columns:

                connection.execute(

                    text(
                        f"""
                        ALTER TABLE users
                        ADD COLUMN {column_name}
                        {column_definition}
                        """
                    )

                )


# =========================================
# RUN MIGRATION
# =========================================
migrate_user_subscription_columns()
# =========================================
# DATABASE DEPENDENCY
# =========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()