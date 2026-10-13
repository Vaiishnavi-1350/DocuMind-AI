# ============================================================
# DOCUMIND AI - MAIN APPLICATION
# ============================================================
#
# Phase 8.3
# Logging + Error Handling
#
# Architecture:
#
# FastAPI
#   |
#   +-- Authentication
#   |
#   +-- Subscription
#   |
#   +-- Payment
#   |
#   +-- Document Upload
#   |      |
#   |      +-- PDF
#   |      +-- Ingestion
#   |      +-- BGE-M3
#   |      +-- Qdrant
#   |
#   +-- Document Management
#   |
#   +-- Chat
#          |
#          +-- Hybrid Retrieval
#          +-- RRF
#          +-- Reranker
#          +-- Gemini
#
# ============================================================

from __future__ import annotations

import logging
import shutil
import uuid

from pathlib import Path
from datetime import datetime, timedelta

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends,
    Form,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer

from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.database.database import (
    get_db,
    User,
    Document,
    ChatMessage,
    Payment,
)

from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

from app.rag.ingest import ingest_pdf
from app.rag.qdrant import (
    delete_document as delete_qdrant_document,
)
from app.rag.pipeline import ask_question


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("documind")

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

logger.info("DocuMind AI logging initialized.")


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="DocuMind AI",
    description=(
        "AI-powered document "
        "intelligence platform"
    ),
    version="2.0.0",
)


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_DIR = Path("frontend")

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    logger.debug(
        "Health check requested."
    )

    return {
        "status": "healthy"
    }


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = Path(
    "data/uploads"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# OAUTH2
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


# ============================================================
# REQUEST MODELS
# ============================================================

class RegisterRequest(BaseModel):

    email: str
    password: str


class QuestionRequest(BaseModel):

    question: str


class PaymentVerifyRequest(BaseModel):

    order_id: str
    payment_id: str


class PaymentWebhookRequest(BaseModel):

    payment_id: str
    status: str


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(

    token: str = Depends(
        oauth2_scheme
    ),

    db: Session = Depends(
        get_db
    ),

):

    user_id = decode_access_token(
        token
    )

    if not user_id:

        logger.warning(
            "Authentication failed: invalid or expired token."
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if not user:

        logger.warning(
            "Authentication failed: user not found."
        )

        raise HTTPException(
            status_code=401,
            detail="User not found.",
        )

    return user

# ============================================================
# SUBSCRIPTION CHECK
# ============================================================

def check_subscription_active(
    user: User,
    db: Session,
):

    # --------------------------------------------------------
    # BACKFILL EXPIRY FOR LEGACY PREMIUM USERS
    # --------------------------------------------------------

    if (
        user.plan == "premium"
        and user.subscription_status == "active"
        and user.subscription_expires_at is None
    ):

        start_date = (
            user.subscription_started_at
            or datetime.utcnow()
        )

        user.subscription_started_at = start_date

        user.subscription_expires_at = (
            start_date + timedelta(days=30)
        )

        db.commit()

        logger.info(
            "Legacy Premium subscription expiry created. "
            "user_id=%s expires_at=%s",
            user.id,
            user.subscription_expires_at,
        )

    # --------------------------------------------------------
    # NORMAL ACTIVE CHECK
    # --------------------------------------------------------

    if user.subscription_status != "active":

        logger.warning(
            "Inactive subscription access attempt. "
            "user_id=%s plan=%s status=%s",
            user.id,
            user.plan,
            user.subscription_status,
        )

        raise HTTPException(
            status_code=403,
            detail="Your subscription is not active.",
        )

    # --------------------------------------------------------
    # EXPIRY CHECK
    # --------------------------------------------------------

    if (
        user.subscription_expires_at
        and datetime.utcnow()
        >= user.subscription_expires_at
    ):

        logger.info(
            "Premium subscription expired. "
            "user_id=%s expires_at=%s",
            user.id,
            user.subscription_expires_at,
        )

        # Downgrade to Free
        user.plan = "free"

        user.subscription_status = "expired"

        user.question_limit = 20

        user.document_limit = 3

        user.max_file_size_mb = 5

        db.commit()

        raise HTTPException(
            status_code=403,
            detail=(
                "Your Premium subscription has expired. "
                "Please renew your Premium plan to continue."
            ),
        )
# ============================================================
# REGISTER
# ============================================================

@app.post(
    "/api/auth/register"
)
def register(

    request: RegisterRequest,

    db: Session = Depends(
        get_db
    ),

):

    email = request.email.strip().lower()

    password = request.password

    if not email:

        raise HTTPException(
            status_code=400,
            detail="Email is required.",
        )

    if len(password) < 8:

        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain "
                "at least 8 characters."
            ),
        )

    existing_user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if existing_user:

        logger.info(
            "Registration rejected: email already exists."
        )

        raise HTTPException(
            status_code=409,
            detail="Email is already registered.",
        )

    user_id = str(
        uuid.uuid4()
    )

    user = User(

        id=user_id,

        email=email,

        password_hash=hash_password(
            password
        ),

        plan="free",

        subscription_status="active",

        questions_used=0,

        question_limit=20,

        document_limit=3,

        max_file_size_mb=5,

        subscription_started_at=(
            datetime.utcnow()
        ),

        subscription_expires_at=None,
    )

    try:

        db.add(user)

        db.commit()

        db.refresh(user)

        logger.info(
            "User registered successfully. user_id=%s",
            user.id,
        )

    except Exception:

        db.rollback()

        logger.exception(
            "User registration failed."
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to create the account. "
                "Please try again."
            ),
        )

    return {

        "message":
            "Account created successfully.",

        "user_id":
            user.id,

        "email":
            user.email,
    }


# ============================================================
# LOGIN
# ============================================================

@app.post(
    "/api/auth/login"
)
def login(

    username: str = Form(...),

    password: str = Form(...),

    db: Session = Depends(
        get_db
    ),

):

    email = username.strip().lower()

    user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if not user:

        logger.warning(
            "Login failed: invalid credentials."
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not verify_password(
        password,
        user.password_hash,
    ):

        logger.warning(
            "Login failed: invalid password."
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    try:

        access_token = create_access_token(
            user.id
        )

    except Exception:

        logger.exception(
            "JWT token creation failed."
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to complete login. "
                "Please try again."
            ),
        )

    logger.info(
        "User login successful. user_id=%s",
        user.id,
    )

    return {

        "access_token":
            access_token,

        "token_type":
            "bearer",

        "user": {

            "id":
                user.id,

            "email":
                user.email,
        },
    }


# ============================================================
# CURRENT USER
# ============================================================

@app.get(
    "/api/auth/me"
)
def current_user(

    user: User = Depends(
        get_current_user
    ),

):

    return {

        "id":
            user.id,

        "email":
            user.email,

        "plan":
            user.plan,

        "subscription_status":
            user.subscription_status,

        "questions_used":
            user.questions_used,

        "question_limit":
            user.question_limit,

        "document_limit":
            user.document_limit,

        "max_file_size_mb":
            user.max_file_size_mb,
        "subscription_started_at":
            user.subscription_started_at,

        "subscription_expires_at":
            user.subscription_expires_at,
    }


# ============================================================
# SUBSCRIPTION INFORMATION
# ============================================================

@app.get(
    "/api/subscription"
)
def get_subscription(

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    try:

        questions_used = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.user_id == user.id
            )
            .count()
        )

        documents_used = (
            db.query(Document)
            .filter(
                Document.user_id == user.id
            )
            .count()
        )

        user.questions_used = questions_used

        db.commit()

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to retrieve subscription information. "
            "user_id=%s",
            user.id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve subscription "
                "information."
            ),
        )

    return {

        "plan":
            user.plan,

        "subscription_status":
            user.subscription_status,

        "questions_used":
            questions_used,

        "question_limit":
            user.question_limit,

        "documents_used":
            documents_used,

        "document_limit":
            user.document_limit,

        "max_file_size_mb":
            user.max_file_size_mb,

        "subscription_started_at":
            user.subscription_started_at,

        "subscription_expires_at":
            user.subscription_expires_at,
    }
# ============================================================
# ACTIVATE PREMIUM PLAN
# ============================================================

@app.post(
    "/api/subscription/upgrade"
)
def upgrade_to_premium(

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    # ========================================================
    # ALREADY PREMIUM
    # ========================================================

    if user.plan == "premium":

        # ----------------------------------------------------
        # Check whether a payment record already exists
        # ----------------------------------------------------

        existing_payment = (
            db.query(Payment)
            .filter(
                Payment.user_id == user.id,
                Payment.plan == "premium",
                Payment.status.in_([
                    "paid",
                    "success"
                ])
            )
            .order_by(
                Payment.created_at.desc()
            )
            .first()
        )

        # ----------------------------------------------------
        # LEGACY PREMIUM USER
        #
        # Older versions of DocuMind activated Premium
        # directly without creating a Payment record.
        #
        # Create ONE demo payment record so Billing History
        # correctly represents the Premium activation.
        # ----------------------------------------------------

        if not existing_payment:

            try:

                order_id = (
                    "DEMO_ORDER_"
                    + str(uuid.uuid4())
                )

                payment_id = (
                    "DEMO_PAYMENT_"
                    + str(uuid.uuid4())
                )

                legacy_payment = Payment(

                    id=str(uuid.uuid4()),

                    user_id=user.id,

                    payment_id=payment_id,

                    order_id=order_id,

                    amount=499,

                    currency="INR",

                    status="paid",

                    plan="premium",

                    paid_at=datetime.utcnow(),
                )

                db.add(
                    legacy_payment
                )

                db.commit()

                db.refresh(
                    legacy_payment
                )

                logger.info(
                    "Legacy Premium payment history "
                    "record created. "
                    "user_id=%s payment_id=%s",
                    user.id,
                    payment_id,
                )

            except Exception:

                db.rollback()

                logger.exception(
                    "Failed to create legacy Premium "
                    "payment history record. "
                    "user_id=%s",
                    user.id,
                )

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Unable to create Premium "
                        "payment history."
                    ),
                )

        return {

            "message":
                "You are already on the Premium plan.",

            "plan":
                user.plan,

            "subscription_status":
                user.subscription_status,

        }

    # ========================================================
    # CREATE PREMIUM SUBSCRIPTION
    # ========================================================

    try:

        # ----------------------------------------------------
        # PREMIUM USER SETTINGS
        # ----------------------------------------------------

        user.plan = "premium"

        user.subscription_status = "active"

        user.question_limit = 500

        user.document_limit = 50

        user.max_file_size_mb = 25

        subscription_start = datetime.utcnow()

        user.subscription_started_at = subscription_start

        user.subscription_expires_at = (
            subscription_start + timedelta(days=30)
        )

        # ----------------------------------------------------
        # CREATE DEMO PAYMENT RECORD
        # ----------------------------------------------------

        order_id = (
            "DEMO_ORDER_"
            + str(uuid.uuid4())
        )

        payment_id = (
            "DEMO_PAYMENT_"
            + str(uuid.uuid4())
        )

        payment = Payment(

            id=str(uuid.uuid4()),

            user_id=user.id,

            payment_id=payment_id,

            order_id=order_id,

            amount=499,

            currency="INR",

            status="paid",

            plan="premium",

            paid_at=datetime.utcnow(),
        )

        db.add(
            payment
        )

        # ----------------------------------------------------
        # SAVE EVERYTHING
        # ----------------------------------------------------

        db.commit()

        db.refresh(
            user
        )

        db.refresh(
            payment
        )

        logger.info(
            "Premium plan activated with demo payment. "
            "user_id=%s payment_id=%s",
            user.id,
            payment.payment_id,
        )

    except Exception:

        db.rollback()

        logger.exception(
            "Premium upgrade failed. "
            "user_id=%s",
            user.id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to activate Premium. "
                "Please try again."
            ),
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "message":
            "Premium plan activated successfully.",

        "demo_mode":
            True,

        "payment_id":
            payment.payment_id,

        "order_id":
            payment.order_id,

        "amount":
            payment.amount,

        "currency":
            payment.currency,

        "plan":
            user.plan,

        "subscription_status":
            user.subscription_status,

        "question_limit":
            user.question_limit,

        "document_limit":
            user.document_limit,

        "max_file_size_mb":
            user.max_file_size_mb,
    }


# ============================================================
# CREATE PAYMENT
# ============================================================

@app.post(
    "/api/payment/create"
)
def create_payment(

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    if user.plan == "premium":

        return {

            "message":
                "You are already on the Premium plan.",

            "plan":
                user.plan,
        }

    order_id = (
        "DEMO_ORDER_"
        + str(uuid.uuid4())
    )

    payment_id = (
        "DEMO_PAYMENT_"
        + str(uuid.uuid4())
    )

    amount = 499

    try:

        payment = Payment(

            id=str(uuid.uuid4()),

            user_id=user.id,

            payment_id=payment_id,

            order_id=order_id,

            amount=amount,

            currency="INR",

            status="created",

            plan="premium",
        )

        db.add(payment)

        db.commit()

        db.refresh(payment)

        logger.info(
            "Demo payment created. "
            "user_id=%s payment_id=%s",
            user.id,
            payment_id,
        )

    except Exception:

        db.rollback()

        logger.exception(
            "Payment creation failed. user_id=%s",
            user.id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to create payment. "
                "Please try again."
            ),
        )

    return {

        "message":
            "Demo payment created successfully.",

        "demo_mode":
            True,

        "order_id":
            order_id,

        "payment_id":
            payment_id,

        "amount":
            amount,

        "currency":
            "INR",

        "plan":
            "premium",

        "status":
            "created",
    }


# ============================================================
# VERIFY DEMO PAYMENT
# ============================================================

@app.post(
    "/api/payment/verify"
)
def verify_payment(

    request: PaymentVerifyRequest,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    payment = (
        db.query(Payment)
        .filter(
            Payment.order_id == request.order_id,
            Payment.payment_id == request.payment_id,
            Payment.user_id == user.id,
        )
        .first()
    )

    if not payment:

        raise HTTPException(
            status_code=404,
            detail="Payment not found.",
        )

    if payment.status == "paid":

        return {

            "message":
                "Payment already verified.",

            "payment_id":
                payment.payment_id,

            "plan":
                user.plan,

            "subscription_status":
                user.subscription_status,
        }

    try:

        payment.status = "paid"

        payment.paid_at = datetime.utcnow()

        user.plan = "premium"

        user.subscription_status = "active"

        user.question_limit = 500

        user.document_limit = 50

        user.max_file_size_mb = 25

        subscription_start = datetime.utcnow()

        user.subscription_started_at = subscription_start

        user.subscription_expires_at = (
            subscription_start + timedelta(days=30)
        )

        db.commit()

        db.refresh(user)

        logger.info(
            "Demo payment verified. "
            "user_id=%s payment_id=%s",
            user.id,
            payment.payment_id,
        )

    except Exception:

        db.rollback()

        logger.exception(
            "Payment verification failed. "
            "user_id=%s payment_id=%s",
            user.id,
            request.payment_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to verify payment. "
                "Please try again."
            ),
        )

    return {

        "message":
            "Demo payment successful.",

        "demo_mode":
            True,

        "payment_id":
            payment.payment_id,

        "order_id":
            payment.order_id,

        "amount":
            payment.amount,

        "currency":
            payment.currency,

        "plan":
            user.plan,

        "subscription_status":
            user.subscription_status,

        "question_limit":
            user.question_limit,

        "document_limit":
            user.document_limit,

        "max_file_size_mb":
            user.max_file_size_mb,
    }


# ============================================================
# SIMULATE SUCCESSFUL PAYMENT
# ============================================================

@app.post(
    "/api/payment/simulate-success/{payment_id}"
)
def simulate_payment_success(

    payment_id: str,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    payment = (
        db.query(Payment)
        .filter(
            Payment.payment_id == payment_id,
            Payment.user_id == user.id,
        )
        .first()
    )

    if not payment:

        raise HTTPException(
            status_code=404,
            detail="Payment not found.",
        )

    if payment.status == "paid":

        return {

            "message":
                "Payment already completed.",

            "payment_id":
                payment.payment_id,

            "plan":
                user.plan,
        }

    try:

        payment.status = "paid"

        payment.paid_at = datetime.utcnow()

        user.plan = "premium"

        user.subscription_status = "active"

        user.question_limit = 500

        user.document_limit = 50

        user.max_file_size_mb = 25

        subscription_start = datetime.utcnow()

        user.subscription_started_at = subscription_start

        user.subscription_expires_at = (
            subscription_start + timedelta(days=30)
        )

        db.commit()

        db.refresh(user)

        logger.info(
            "Demo payment simulated successfully. "
            "user_id=%s payment_id=%s",
            user.id,
            payment.payment_id,
        )

    except Exception:

        db.rollback()

        logger.exception(
            "Payment simulation failed. "
            "user_id=%s payment_id=%s",
            user.id,
            payment_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to complete payment. "
                "Please try again."
            ),
        )

    return {

        "message":
            "Payment successful.",

        "payment_id":
            payment.payment_id,

        "payment_status":
            payment.status,

        "plan":
            user.plan,

        "subscription_status":
            user.subscription_status,

        "question_limit":
            user.question_limit,

        "document_limit":
            user.document_limit,

        "max_file_size_mb":
            user.max_file_size_mb,
    }
# ============================================================
# FIX LEGACY PREMIUM PAYMENT
# ============================================================

@app.post("/api/payment/fix-legacy")
def fix_legacy_payment(

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    # --------------------------------------------------------
    # Only for Premium users
    # --------------------------------------------------------

    if user.plan != "premium":

        raise HTTPException(
            status_code=400,
            detail="User is not on Premium plan."
        )

    # --------------------------------------------------------
    # Check whether payment already exists
    # --------------------------------------------------------

    existing_payment = (
        db.query(Payment)
        .filter(
            Payment.user_id == user.id
        )
        .order_by(
            Payment.created_at.desc()
        )
        .first()
    )

    if existing_payment:

        return {
            "message": "Payment already exists.",
            "payment_id":
                existing_payment.payment_id,
            "status":
                existing_payment.status,
            "amount":
                existing_payment.amount,
            "plan":
                existing_payment.plan,
        }

    # --------------------------------------------------------
    # CREATE LEGACY DEMO PAYMENT
    # --------------------------------------------------------

    try:

        payment = Payment(

            id=str(uuid.uuid4()),

            user_id=user.id,

            payment_id=(
                "DEMO_PAYMENT_"
                + str(uuid.uuid4())
            ),

            order_id=(
                "DEMO_ORDER_"
                + str(uuid.uuid4())
            ),

            amount=499,

            currency="INR",

            status="paid",

            plan="premium",

            paid_at=datetime.utcnow(),
        )

        db.add(payment)

        db.commit()

        db.refresh(payment)

        logger.info(
            "Legacy payment created successfully. "
            "user_id=%s payment_id=%s",
            user.id,
            payment.payment_id,
        )

        return {

            "message":
                "Legacy Premium payment created successfully.",

            "payment_id":
                payment.payment_id,

            "order_id":
                payment.order_id,

            "amount":
                payment.amount,

            "currency":
                payment.currency,

            "status":
                payment.status,

            "plan":
                payment.plan,
        }

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to create legacy payment. "
            "user_id=%s",
            user.id,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to create payment record."
        )
# ============================================================
# PAYMENT HISTORY
# ============================================================

@app.get(
    "/api/payment/history"
)
def get_payment_history(

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    try:

        # ----------------------------------------------------
        # GET EXISTING PAYMENT RECORDS
        # ----------------------------------------------------

        payments = (
            db.query(Payment)
            .filter(
                Payment.user_id == user.id
            )
            .order_by(
                Payment.created_at.desc()
            )
            .all()
        )

        # ----------------------------------------------------
        # DEMO ENVIRONMENT SELF-HEAL
        #
        # If the account is already Premium but there is no
        # payment record, create one payment-history record.
        #
        # This handles older/legacy Premium activations that
        # upgraded the User table without creating Payment row.
        # ----------------------------------------------------

        if not payments and user.plan == "premium":

            logger.warning(
                "Premium user has no payment history. "
                "Creating legacy demo payment record. "
                "user_id=%s",
                user.id,
            )

            legacy_payment_id = (
                "DEMO_PAYMENT_"
                + str(uuid.uuid4())
            )

            legacy_order_id = (
                "DEMO_ORDER_"
                + str(uuid.uuid4())
            )

            started_at = (
                user.subscription_started_at
                or datetime.utcnow()
            )

            legacy_payment = Payment(

                id=str(
                    uuid.uuid4()
                ),

                user_id=user.id,

                payment_id=legacy_payment_id,

                order_id=legacy_order_id,

                amount=499,

                currency="INR",

                status="paid",

                plan="premium",

                created_at=started_at,

                paid_at=started_at,
            )

            db.add(
                legacy_payment
            )

            db.commit()

            db.refresh(
                legacy_payment
            )

            payments = [
                legacy_payment
            ]

            logger.info(
                "Legacy Premium payment history created. "
                "user_id=%s payment_id=%s",
                user.id,
                legacy_payment.payment_id,
            )

        # ----------------------------------------------------
        # RETURN PAYMENT HISTORY
        # ----------------------------------------------------

        return [

            {

                "payment_id":
                    payment.payment_id,

                "order_id":
                    payment.order_id,

                "amount":
                    payment.amount,

                "amount_in_rupees":
                    payment.amount,

                "currency":
                    payment.currency,

                "status":
                    payment.status,

                "plan":
                    payment.plan,

                "created_at": (
                    payment.created_at.isoformat()
                    if payment.created_at
                    else None
                ),

                "paid_at": (
                    payment.paid_at.isoformat()
                    if payment.paid_at
                    else None
                ),
            }

            for payment in payments

        ]

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to retrieve payment history. "
            "user_id=%s",
            user.id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve payment history."
            ),
        )
# ============================================================
# PAYMENT WEBHOOK SIMULATION
# ============================================================

@app.post(
    "/api/payment/webhook"
)
def payment_webhook(

    request: PaymentWebhookRequest,

    db: Session = Depends(
        get_db
    ),

):

    allowed_statuses = [
        "paid",
        "failed",
    ]

    if request.status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail="Invalid payment status.",
        )

    payment = (
        db.query(Payment)
        .filter(
            Payment.payment_id == request.payment_id
        )
        .first()
    )

    if not payment:

        raise HTTPException(
            status_code=404,
            detail="Payment not found.",
        )

    try:

        if request.status == "paid":

            payment.status = "paid"

            payment.paid_at = datetime.utcnow()

            user = (
                db.query(User)
                .filter(
                    User.id == payment.user_id
                )
                .first()
            )

            if not user:

                raise HTTPException(
                    status_code=404,
                    detail="Payment user not found.",
                )

            user.plan = "premium"

            user.subscription_status = "active"

            user.question_limit = 500

            user.document_limit = 50

            user.max_file_size_mb = 25

            subscription_start = datetime.utcnow()

            user.subscription_started_at = subscription_start

            user.subscription_expires_at = (
                subscription_start + timedelta(days=30)
            )

            db.commit()

            db.refresh(payment)
            db.refresh(user)

            logger.info(
                "Payment webhook processed. "
                "payment_id=%s user_id=%s",
                payment.payment_id,
                user.id,
            )

            return {

                "message":
                    "Payment webhook processed successfully.",

                "payment_id":
                    payment.payment_id,

                "payment_status":
                    payment.status,

                "user_id":
                    user.id,

                "plan":
                    user.plan,

                "subscription_status":
                    user.subscription_status,
            }

        payment.status = "failed"

        db.commit()

        db.refresh(payment)

        logger.info(
            "Payment failure webhook processed. "
            "payment_id=%s",
            payment.payment_id,
        )

        return {

            "message":
                "Payment failure webhook processed.",

            "payment_id":
                payment.payment_id,

            "payment_status":
                payment.status,
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception:

        db.rollback()

        logger.exception(
            "Payment webhook processing failed. "
            "payment_id=%s",
            request.payment_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to process payment webhook."
            ),
        )


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@app.post(
    "/api/documents/upload"
)
async def upload_document(

    file: UploadFile = File(...),

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    check_subscription_active(user, db,)

    document_count = (
        db.query(Document)
        .filter(
            Document.user_id == user.id
        )
        .count()
    )

    if document_count >= user.document_limit:

        raise HTTPException(
            status_code=403,
            detail=(
                f"Document limit reached. "
                f"Your {user.plan} plan allows "
                f"{user.document_limit} documents."
            ),
        )

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is missing.",
        )

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    document_id = str(
        uuid.uuid4()
    )

    file_path = (
        UPLOAD_DIR
        / f"{document_id}.pdf"
    )

    logger.info(
        "Document upload started. "
        "user_id=%s document_id=%s filename=%s",
        user.id,
        document_id,
        file.filename,
    )

    try:

        # ====================================================
        # FILE SIZE
        # ====================================================

        max_file_size = (
            user.max_file_size_mb
            * 1024
            * 1024
        )

        file.file.seek(
            0,
            2
        )

        file_size = file.file.tell()

        file.file.seek(0)

        if file_size > max_file_size:

            raise HTTPException(
                status_code=413,
                detail=(
                    f"File is too large. "
                    f"Your {user.plan} plan allows "
                    f"{user.max_file_size_mb} MB per PDF."
                ),
            )

        if file_size == 0:

            raise HTTPException(
                status_code=400,
                detail="The uploaded PDF is empty.",
            )

        # ====================================================
        # SAVE PDF
        # ====================================================

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

        logger.info(
            "PDF saved successfully. "
            "document_id=%s size=%s bytes",
            document_id,
            file_size,
        )

        # ====================================================
        # RAG INGESTION
        # ====================================================
        logger.info(
            "DOCUMENT UPLOAD START | document_id=%s | filename=%s",
            document_id,
            file.filename,
        )

        ingestion_result = ingest_pdf(

            pdf_path=file_path,

            document_id=document_id,

            filename=file.filename,
        )
        logger.info(
        "DOCUMENT INGESTION COMPLETE | document_id=%s | pages=%s | chunks=%s",
        document_id,
        ingestion_result["pages"],
        ingestion_result["chunks"],
        )
        pages = ingestion_result["pages"]

        chunks = ingestion_result["chunks"]

        logger.info(
            "Document ingestion completed. "
            "document_id=%s pages=%s chunks=%s",
            document_id,
            pages,
            chunks,
        )

        if pages <= 0:

            raise ValueError(
                "No readable pages were found in the PDF."
            )

        if chunks <= 0:

            raise ValueError(
                "No text chunks were generated from the PDF."
            )

        # ====================================================
        # SAVE DATABASE RECORD
        # ====================================================

        document_record = Document(

            id=document_id,

            user_id=user.id,

            filename=file.filename,

            file_path=str(file_path),

            pages=pages,

            chunks=chunks,

            status="ready",
        )

        db.add(
            document_record
        )

        db.commit()

        db.refresh(
            document_record
        )

        logger.info(
            "Document database record created. "
            "document_id=%s user_id=%s",
            document_id,
            user.id,
        )

        return {

            "message":
                "Document processed successfully.",

            "document_id":
                document_id,

            "filename":
                file.filename,

            "pages":
                pages,

            "chunks":
                chunks,

            "status":
                "ready",
        }

    except HTTPException:

        # ====================================================
        # DATABASE ROLLBACK
        # ====================================================

        db.rollback()

        logger.warning(
            "Document upload rejected. "
            "document_id=%s",
            document_id,
        )

        # ====================================================
        # QDRANT CLEANUP
        # ====================================================

        try:

            delete_qdrant_document(
                document_id
            )

            logger.info(
                "Qdrant rollback completed. "
                "document_id=%s",
                document_id,
            )

        except Exception:

            logger.exception(
                "Qdrant rollback failed. "
                "document_id=%s",
                document_id,
            )

        # ====================================================
        # FILE CLEANUP
        # ====================================================

        if file_path.exists():

            try:

                file_path.unlink()

                logger.info(
                    "Uploaded PDF removed after failure. "
                    "document_id=%s",
                    document_id,
                )

            except Exception:

                logger.exception(
                    "Failed to remove uploaded PDF. "
                    "document_id=%s",
                    document_id,
                )

        raise

    except Exception:

        # ====================================================
        # UNEXPECTED ERROR
        # ====================================================

        db.rollback()

        logger.exception(
            "Unexpected document processing failure. "
            "document_id=%s user_id=%s",
            document_id,
            user.id,
        )

        # ====================================================
        # QDRANT ROLLBACK
        # ====================================================

        try:

            delete_qdrant_document(
                document_id
            )

            logger.info(
                "Qdrant rollback completed after unexpected "
                "error. document_id=%s",
                document_id,
            )

        except Exception:

            logger.exception(
                "Qdrant rollback failed after unexpected "
                "error. document_id=%s",
                document_id,
            )

        # ====================================================
        # PDF CLEANUP
        # ====================================================

        if file_path.exists():

            try:

                file_path.unlink()

            except Exception:

                logger.exception(
                    "Failed to remove uploaded PDF after "
                    "unexpected error. document_id=%s",
                    document_id,
                )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to process the document. "
                "Please try again."
            ),
        )


# ============================================================
# GET USER DOCUMENTS
# ============================================================

@app.get(
    "/api/documents"
)
def get_documents(

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    try:

        documents = (
            db.query(Document)
            .filter(
                Document.user_id == user.id
            )
            .order_by(
                Document.created_at.desc()
            )
            .all()
        )

    except Exception:

        logger.exception(
            "Failed to retrieve documents. "
            "user_id=%s",
            user.id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve documents."
            ),
        )

    return [

        {

            "document_id":
                document.id,

            "filename":
                document.filename,

            "pages":
                document.pages,

            "chunks":
                document.chunks,

            "status":
                document.status,

            "created_at":
                document.created_at,
        }

        for document in documents

    ]


# ============================================================
# DELETE DOCUMENT
# ============================================================

@app.delete(
    "/api/documents/{document_id}"
)
def delete_document(

    document_id: str,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user.id,
        )
        .first()
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    logger.info(
        "Document deletion started. "
        "document_id=%s user_id=%s",
        document_id,
        user.id,
    )

    try:

        # ====================================================
        # QDRANT
        # ====================================================

        delete_qdrant_document(
            document_id
        )

        # ====================================================
        # PDF
        # ====================================================

        file_path = Path(
            document.file_path
        )

        if file_path.exists():

            file_path.unlink()

        # ====================================================
        # CHAT HISTORY
        # ====================================================

        db.query(
            ChatMessage
        ).filter(

            ChatMessage.document_id
            == document_id,

            ChatMessage.user_id
            == user.id,

        ).delete(
            synchronize_session=False
        )

        # ====================================================
        # DATABASE
        # ====================================================

        db.delete(
            document
        )

        db.commit()

        logger.info(
            "Document deleted successfully. "
            "document_id=%s user_id=%s",
            document_id,
            user.id,
        )

        return {

            "message":
                "Document deleted successfully.",

            "document_id":
                document_id,

            "status":
                "deleted",
        }

    except Exception:

        db.rollback()

        logger.exception(
            "Document deletion failed. "
            "document_id=%s user_id=%s",
            document_id,
            user.id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to delete the document. "
                "Please try again."
            ),
        )


# ============================================================
# CHAT WITH DOCUMENT
# ============================================================

@app.post(
    "/api/chat/{document_id}"
)
def chat_with_document(

    document_id: str,

    request: QuestionRequest,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    check_subscription_active(user , db,)

    # ========================================================
    # QUESTION USAGE
    # ========================================================

    try:

        questions_used = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.user_id == user.id
            )
            .count()
        )

        user.questions_used = questions_used

    except Exception:

        db.rollback()

        logger.exception(
            "Failed to check question usage. "
            "user_id=%s",
            user.id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to check question usage."
            ),
        )

    if user.questions_used >= user.question_limit:

        db.commit()

        logger.warning(
            "Question limit reached. "
            "user_id=%s plan=%s",
            user.id,
            user.plan,
        )

        raise HTTPException(
            status_code=403,
            detail=(
                f"Question limit reached. "
                f"Your {user.plan} plan allows "
                f"{user.question_limit} questions."
            ),
        )

    # ========================================================
    # QUESTION VALIDATION
    # ========================================================

    question = (
        request.question.strip()
    )

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    # ========================================================
    # DOCUMENT OWNERSHIP
    # ========================================================

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user.id,
        )
        .first()
    )

    if not document:

        logger.warning(
            "Chat attempted for unavailable document. "
            "document_id=%s user_id=%s",
            document_id,
            user.id,
        )

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    logger.info(
        "RAG question started. "
        "user_id=%s document_id=%s",
        user.id,
        document_id,
    )

    try:

        # ====================================================
        # RAG PIPELINE
        # ====================================================
        logger.info(
                "CHAT REQUEST START | document_id=%s | question=%s",
                document_id,
                question,
                )
        result = ask_question(

            question=question,

            document_id=document_id,
        )
        logger.info(
        "CHAT REQUEST COMPLETE | document_id=%s | retrieved=%s | context=%s | sources=%s",
        document_id,
        result.get("retrieved_count", 0),
        result.get("context_count", 0),
        len(result.get("sources", [])),
        )
       
        answer = result.get(
            "answer",
            "",
        )

        # ====================================================
        # CHAT HISTORY
        # ====================================================

        chat_message = ChatMessage(

            user_id=user.id,

            document_id=document_id,

            question=question,

            answer=answer,
        )

        db.add(
            chat_message
        )

        user.questions_used += 1

        db.commit()

        logger.info(
            "RAG question completed successfully. "
            "user_id=%s document_id=%s",
            user.id,
            document_id,
        )

        return result

    except HTTPException:

        db.rollback()
        raise

    except Exception:

        db.rollback()

        logger.exception(
            "RAG question failed. "
            "user_id=%s document_id=%s",
            user.id,
            document_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to process your question. "
                "Please try again."
            ),
        )


# ============================================================
# GET CHAT HISTORY
# ============================================================

@app.get(
    "/api/chat/{document_id}/history"
)
def get_chat_history(

    document_id: str,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user.id,
        )
        .first()
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    try:

        messages = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.document_id
                == document_id,

                ChatMessage.user_id
                == user.id,
            )
            .order_by(
                ChatMessage.created_at.asc()
            )
            .all()
        )

    except Exception:

        logger.exception(
            "Failed to retrieve chat history. "
            "user_id=%s document_id=%s",
            user.id,
            document_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve chat history."
            ),
        )

    return {

        "document_id":
            document_id,

        "filename":
            document.filename,

        "history": [

            {

                "id":
                    message.id,

                "question":
                    message.question,

                "answer":
                    message.answer,

                "created_at": (
                    message.created_at.isoformat()
                    if message.created_at
                    else None
                ),
            }

            for message in messages

        ],

        "count":
            len(messages),
    }


# ============================================================
# STARTUP LOG
# ============================================================

@app.on_event("startup")
def startup_event():

    logger.info(
        "======================================================"
    )

    logger.info(
        "DocuMind AI started successfully."
    )

    logger.info(
        "Version: 2.0.0"
    )

    logger.info(
        "======================================================"
    )

# ============================================================
# SHUTDOWN LOG
# ============================================================

@app.on_event("shutdown")
def shutdown_event():

    logger.info(
        "DocuMind AI application shutting down."
    )