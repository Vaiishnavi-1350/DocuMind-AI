from sqlalchemy.engine import make_url
from app.config import DATABASE_URL as CONFIG_DATABASE_URL
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
# DATABASE CONFIGURATION
# =========================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_URL = CONFIG_DATABASE_URL

database_url = make_url(DATABASE_URL)

# Create the directory automatically for SQLite.
if database_url.drivername.startswith("sqlite"):

    database_name = database_url.database

    if database_name and database_name != ":memory:":

        DATABASE_PATH = Path(database_name)

        if not DATABASE_PATH.is_absolute():
            DATABASE_PATH = BASE_DIR / DATABASE_PATH

        DATABASE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        database_url = database_url.set(
            database=str(DATABASE_PATH)
        )

    else:
        DATABASE_PATH = None

else:
    DATABASE_PATH = None

# =========================================
# DATABASE ENGINE
# =========================================

connect_args = {}

if database_url.drivername.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }

engine = create_engine(
    database_url,
    connect_args=connect_args
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

    document_type = Column(
    String,
    nullable=False,
    default="pdf",
    server_default="pdf"
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

    active_ingestion_version = Column(
        String,
        nullable=True,
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
# DOCUMENT TYPE MIGRATION
# =========================================

def migrate_document_type_column():

    inspector = inspect(engine)

    if "documents" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("documents")
    }

    if "document_type" not in existing_columns:

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    ALTER TABLE documents
                    ADD COLUMN document_type
                    VARCHAR NOT NULL DEFAULT 'pdf'
                    """
                )
            )

        print(
            "Database migration completed: "
            "documents.document_type added."
        )
# =========================================
# INGESTION VERSION MIGRATION
# =========================================
def migrate_active_ingestion_version_column():

    inspector = inspect(engine)

    if "documents" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("documents")
    }

    if "active_ingestion_version" not in existing_columns:

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    ALTER TABLE documents
                    ADD COLUMN active_ingestion_version
                    VARCHAR
                    """
                )
            )

        print(
            "Database migration completed: "
            "documents.active_ingestion_version added."
        )


# =========================================
# RUN DATABASE MIGRATIONS
# =========================================

migrate_user_subscription_columns()

migrate_document_type_column()

migrate_active_ingestion_version_column()

# =========================================
# DATABASE DEPENDENCY
# =========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()