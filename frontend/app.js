// =========================================================
// DOCUMIND AI
// FUNCTIONAL SAAS DASHBOARD
// JWT + DASHBOARD + DOCUMENTS + AI ASSISTANT
// + HISTORY + SETTINGS + UPLOAD
// =========================================================

const API_BASE = "";

let selectedFile = null;
let currentDocumentId = null;
let currentDocument = null;
let documents = [];
let currentUser = null;
function getToken() {
    return localStorage.getItem("access_token");
}

function authHeaders() {
    const token = getToken();
    if (!token) {
        return {};
    }
    return {
        "Authorization": `Bearer ${token}`
    };
}

function isAuthenticated() {
    return !!getToken();
}

function requireAuthentication() {
    if (!isAuthenticated()) {
        showAuthentication();
        return false;
    }
    return true;
}
// =========================================================
// AUTHENTICATION
// =========================================================

const landingScreen = document.getElementById("landingScreen");
const authScreen = document.getElementById("authScreen");
const app = document.getElementById("app");

const loginView = document.getElementById("loginView");
const registerView = document.getElementById("registerView");

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");

const loginButton = document.getElementById("loginButton");
const registerButton = document.getElementById("registerButton");

const authSwitchButton =
    document.getElementById("authSwitchButton");

const authSwitchText =
    document.getElementById("authSwitchText");

const authMessage =
    document.getElementById("authMessage");

// =========================================================
// LANDING PAGE ELEMENTS
// =========================================================

const landingSignInButton =
    document.getElementById("landingSignInButton");

const landingCreateAccountButton =
    document.getElementById("landingCreateAccountButton");

const landingHeroCreateButton =
    document.getElementById("landingHeroCreateButton");

const landingHeroSignInButton =
    document.getElementById("landingHeroSignInButton");

const landingCtaButton =
    document.getElementById("landingCtaButton");

// =========================================================
// AUTH MESSAGE
// =========================================================

function showAuthMessage(message, type = "error") {

    authMessage.textContent = message;

    authMessage.className =
        `auth-message ${type}`;

    authMessage.hidden = false;
}

function hideAuthMessage() {

    authMessage.textContent = "";

    authMessage.className =
        "auth-message";

    authMessage.hidden = true;
}
// =========================================================
// LOGIN VIEW
// =========================================================

function showLoginView() {

    loginView.hidden = false;
    registerView.hidden = true;
    authSwitchText.textContent =
        "Don't have an account?";
    authSwitchButton.textContent =
        "Create account";
}
// =========================================================
// REGISTER VIEW
// =========================================================

function showRegisterView() {

    loginView.hidden = true;

    registerView.hidden = false;

    authSwitchText.textContent =
        "Already have an account?";

    authSwitchButton.textContent =
        "Sign in";

}
// =========================================================
// SHOW LOGIN SCREEN
// =========================================================

function showAuthentication() {

    landingScreen.hidden = true;

    authScreen.hidden = false;

    app.hidden = true;

    showLoginView();

}
// =========================================================
// SHOW LANDING PAGE
// =========================================================

function showLandingPage() {

    // Show landing page
    landingScreen.hidden = false;

    // Hide authentication
    authScreen.hidden = true;

    // Hide application/dashboard
    app.hidden = true;

}

// =========================================================
// SHOW DASHBOARD
// =========================================================

function showDashboard() {

    authScreen.hidden = true;

    app.hidden = false;

}
// =========================================================
// LANDING PAGE BUTTONS
// =========================================================

function openLoginFromLanding() {

    showAuthentication();

    hideAuthMessage();

    showLoginView();

}
function openRegisterFromLanding() {

    showAuthentication();

    hideAuthMessage();

    showRegisterView();

}

if (landingSignInButton) {

    landingSignInButton.addEventListener(
        "click",
        openLoginFromLanding
    );

}


if (landingCreateAccountButton) {

    landingCreateAccountButton.addEventListener(
        "click",
        openRegisterFromLanding
    );

}


if (landingHeroSignInButton) {

    landingHeroSignInButton.addEventListener(
        "click",
        openLoginFromLanding
    );

}


if (landingHeroCreateButton) {

    landingHeroCreateButton.addEventListener(
        "click",
        openRegisterFromLanding
    );

}


if (landingCtaButton) {

    landingCtaButton.addEventListener(
        "click",
        openRegisterFromLanding
    );

}

// =========================================================
// SWITCH LOGIN / REGISTER
// =========================================================

authSwitchButton.addEventListener("click", () => {

    hideAuthMessage();

    if (loginView.hidden) {

        showLoginView();

    } else {

        showRegisterView();

    }

});

// =========================================================
// PASSWORD SHOW / HIDE
// =========================================================

document
    .querySelectorAll(".password-toggle")
    .forEach(button => {

        button.addEventListener("click", () => {

            const input =
                document.getElementById(
                    button.dataset.target
                );

            const isPassword =
                input.type === "password";

            input.type =
                isPassword ? "text" : "password";

            button.textContent =
                isPassword ? "Hide" : "Show";

        });

    });


// =========================================================
// LOGIN
// =========================================================

loginForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();

        hideAuthMessage();

        const email =
            document
                .getElementById("loginEmail")
                .value
                .trim()
                .toLowerCase();

        const password =
            document
                .getElementById("loginPassword")
                .value;


        if (!email || !password) {

            showAuthMessage(
                "Please enter your email and password."
            );

            return;
        }


        loginButton.disabled = true;

        loginButton.textContent =
            "Signing in...";


        try {

            const formData =
                new URLSearchParams();

            formData.append(
                "username",
                email
            );

            formData.append(
                "password",
                password
            );


            console.log(
                "Attempting login for:",
                email
            );


            const response =
                await fetch(
                    "/api/auth/login",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/x-www-form-urlencoded"
                        },

                        body: formData
                    }
                );


            const data =
                await response.json();


            console.log(
                "Login response:",
                response.status,
                data
            );


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Invalid email or password."
                );
            }


            // =========================================================
            // SAVE JWT
            // =========================================================

            localStorage.setItem(
                "access_token",
                data.access_token
            );

            // =========================================================
            // START A FRESH CHAT SESSION AFTER LOGIN
            //
            // Do NOT carry the previous active document into
            // the new login session.
            // Document history itself is NOT deleted.
            // =========================================================

            currentDocumentId = null;
            currentDocument = null;

            localStorage.removeItem(
                "currentDocumentId"
            );

            // Clear any visible previous chat
            clearChatState();

            // =========================================================
            // SHOW DASHBOARD
            // =========================================================

            showDashboard();

            // =========================================================
            // LOAD USER + DOCUMENTS
            // =========================================================

            await loadDashboardAfterLogin();


        } catch (error) {

            console.error(
                "Login error:",
                error
            );

            showAuthMessage(
                error.message ||
                "Unable to sign in."
            );

        } finally {

            loginButton.disabled = false;

            loginButton.textContent =
                "Sign In";

        }

    }
);


// =========================================================
// REGISTER
// =========================================================

registerForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();

        hideAuthMessage();


        const email =
            document
                .getElementById("registerEmail")
                .value
                .trim()
                .toLowerCase();

        const password =
            document
                .getElementById("registerPassword")
                .value;

        const confirmPassword =
            document
                .getElementById(
                    "registerConfirmPassword"
                )
                .value;


        if (password.length < 8) {

            showAuthMessage(
                "Password must contain at least 8 characters."
            );

            return;
        }


        if (password !== confirmPassword) {

            showAuthMessage(
                "Passwords do not match."
            );

            return;
        }


        registerButton.disabled = true;

        registerButton.textContent =
            "Creating account...";


        try {

            console.log(
                "Creating account for:",
                email
            );


            const response =
                await fetch(
                    "/api/auth/register",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            email: email,
                            password: password
                        })
                    }
                );


            const data =
                await response.json();


            console.log(
                "Register response:",
                response.status,
                data
            );


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Registration failed."
                );
            }


            // Put email into login
            document.getElementById(
                "loginEmail"
            ).value = email;


            // Switch to login
            showLoginView();


            showAuthMessage(
                "Account created successfully. Please sign in.",
                "success"
            );


            // Clear register password fields
            document.getElementById(
                "registerPassword"
            ).value = "";

            document.getElementById(
                "registerConfirmPassword"
            ).value = "";


        } catch (error) {

            console.error(
                "Registration error:",
                error
            );

            showAuthMessage(
                error.message ||
                "Unable to create account."
            );

        } finally {

            registerButton.disabled = false;

            registerButton.textContent =
                "Create Account";

        }

    }
);

async function loadDashboardAfterLogin() {

    try {

        await loadCurrentUser();

        await loadDocuments();

        showDashboard();

    } catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );

        localStorage.removeItem(
            "access_token"
        );

        showAuthentication();

        showAuthMessage(
            "Session could not be loaded. Please sign in again."
        );

    }

}

// =========================================================
// DOM ELEMENTS
// =========================================================

const fileInput =
    document.getElementById("fileInput");

const chooseFileButton =
    document.getElementById("chooseFileButton");

const uploadButton =
    document.getElementById("uploadButton");

const uploadArea =
    document.getElementById("uploadArea");

const fileInfo =
    document.getElementById("fileInfo");

const fileName =
    document.getElementById("fileName");

const fileStatus =
    document.getElementById("fileStatus");

const chatCard =
    document.getElementById("chatCard");

const questionInput =
    document.getElementById("questionInput");

const askButton =
    document.getElementById("askButton");

const answerArea =
    document.getElementById("answerArea");

const sourcesArea =
    document.getElementById("sourcesArea");

const errorMessage =
    document.getElementById("errorMessage");

const loading =
    document.getElementById("loading");

const loadingText =
    document.getElementById("loadingText");

const dashboardUploadButton =
    document.getElementById(
        "dashboardUploadButton"
    );

const documentsUploadButton =
    document.getElementById(
        "documentsUploadButton"
    );

const viewAllDocuments =
    document.getElementById(
        "viewAllDocuments"
    );


// =========================================================
// MAIN CONTENT SECTIONS
// =========================================================

const main =
    document.querySelector(".main");

const dashboardHeading =
    document.querySelector(".dashboard-heading");

const statsGrid =
    document.querySelector(".stats-grid");

const documentsCard =
    document.querySelector(".documents-card");

const uploadCard =
    document.getElementById("uploadCard");


// =========================================================
// NAVIGATION
// =========================================================

const navItems =
    document.querySelectorAll(".nav-item[data-page]");


function setActiveNav(page) {

    navItems.forEach(item => {

        item.classList.toggle(
            "active",
            item.dataset.page === page
        );

    });
}


function showDashboardPage() {

    setActiveNav("dashboard");

    restoreDashboard();

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


function restoreDashboard() {

    if (dashboardHeading) {
        dashboardHeading.hidden = false;
    }

    if (statsGrid) {
        statsGrid.hidden = false;
    }

    if (documentsCard) {
        documentsCard.hidden = false;
    }

    if (uploadCard) {
        uploadCard.hidden = false;
    }

    if (chatCard) {
        chatCard.hidden = true;
    }

    hideDynamicPage();
}


function hideDashboardSections() {

    if (dashboardHeading) {
        dashboardHeading.hidden = true;
    }

    if (statsGrid) {
        statsGrid.hidden = true;
    }

    if (documentsCard) {
        documentsCard.hidden = true;
    }

    if (uploadCard) {
        uploadCard.hidden = true;
    }

    if (chatCard) {
        chatCard.hidden = true;
    }
}


// =========================================================
// DYNAMIC PAGE CONTAINER
// =========================================================

let dynamicPage = null;


function getDynamicPage() {

    if (!dynamicPage) {

        dynamicPage =
            document.createElement("section");

        dynamicPage.id =
            "dynamicPage";

        dynamicPage.className =
            "card dynamic-page";

        if (main) {
            main.appendChild(dynamicPage);
        }
    }

    return dynamicPage;
}


function hideDynamicPage() {

    if (dynamicPage) {
        dynamicPage.hidden = true;
    }
}


function showDynamicPage(html) {

    const page =
        getDynamicPage();

    page.innerHTML = html;

    page.hidden = false;
}


// =========================================================
// DOCUMENTS PAGE
// =========================================================

async function showDocumentsPage() {

    if (!requireAuthentication()) {
        return;
    }

    setActiveNav("documents");

    hideDashboardSections();

    showDynamicPage(`
        <div class="section-title">

            <span class="section-label">
                LIBRARY
            </span>

            <h2>
                My Documents
            </h2>

            <p>
                Manage your uploaded documents and open them
                in the AI Assistant.
            </p>

        </div>

        <div
            id="fullDocumentsContainer"
            class="documents-container"
        >
            <div class="empty-state">
                Loading documents...
            </div>
        </div>

        <button
            id="pageUploadButton"
            class="primary-button"
            type="button"
        >
            + Upload New Document
        </button>
    `);

    const pageUploadButton =
        document.getElementById(
            "pageUploadButton"
        );

    if (pageUploadButton) {

        pageUploadButton.addEventListener(
            "click",
            () => {

                showDashboardPage();

                setTimeout(() => {

                    if (uploadArea) {

                        uploadArea.scrollIntoView({
                            behavior: "smooth"
                        });

                    }

                }, 100);

            }
        );
    }

    await loadDocuments(
        "fullDocumentsContainer"
    );
}


// =========================================================
// RENDER FULL DOCUMENTS PAGE
// =========================================================

function renderFullDocuments(containerId) {

    const container =
        document.getElementById(containerId);

    if (!container) {
        return;
    }

    if (!documents.length) {

        container.innerHTML = `

            <div class="empty-state">

                <div class="empty-icon">
                    📁
                </div>

                <h3>
                    No documents yet
                </h3>

                <p>
                    Upload your first PDF to start
                    using DocuMind AI.
                </p>

            </div>

        `;

        return;
    }

    container.innerHTML = "";

    documents.forEach(doc => {

        const item =
            document.createElement("div");

        item.className =
            "document-item";

        item.innerHTML = `

            <div class="document-item-icon">
                <svg viewBox="0 0 24 24">
                    <path d="M6 3h9l4 4v14H6z"/>
                    <path d="M14 3v5h5"/>
                    <path d="M9 13h6"/>
                    <path d="M9 17h6"/>
                </svg>
            </div>

            <div class="document-item-info">

                <strong>
                    ${escapeHtml(
            doc.filename || "Document"
        )}
                </strong>

                <span>
                    ${doc.pages || 0} pages
                    •
                    ${doc.chunks || 0} chunks
                </span>

            </div>

            <div class="document-item-status">

                <span class="ready-dot"></span>

                ${escapeHtml(
            doc.status || "Ready"
        )}

            </div>

            <div class="document-item-actions">

                <button
                    class="document-open-button"
                    type="button"
                    title="Open document"
                >
                    →
                </button>

                <button
                        class="document-delete-button"
                        type="button"
                        title="Delete document"
                        aria-label="Delete document"
                    >
                        <svg
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        >
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"></path>
                            <path d="M10 11v6"></path>
                            <path d="M14 11v6"></path>
                            <path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"></path>
                        </svg>

                        <span>Delete</span>
                    </button>

            </div>
        `;

        const openButton =
            item.querySelector(
                ".document-open-button"
            );
        const deleteButton =
            item.querySelector(
                ".document-delete-button"
            );
        if (deleteButton) {

            deleteButton.addEventListener(
                "click",
                event => {

                    deleteDocument(
                        doc,
                        event
                    );

                }
            );
        }

        openButton.addEventListener(
            "click",
            () => {

                openDocument(
                    doc
                );

            }
        );
        if (deleteButton) {

            deleteButton.addEventListener(
                "click",
                event => {

                    deleteDocument(
                        doc,
                        event
                    );

                }
            );
        }
        container.appendChild(item);

    });
}


// =========================================================
// DASHBOARD DOCUMENTS
// =========================================================

function renderDashboardDocuments() {

    const container =
        document.getElementById(
            "documentsContainer"
        );

    if (!container) {
        return;
    }

    if (!documents.length) {

        container.innerHTML = `

            <div
                id="emptyDocuments"
                class="empty-state"
            >

                <div class="empty-icon">
                    📁
                </div>

                <h3>
                    No documents yet
                </h3>

                <p>
                    Upload your first PDF to start
                    using DocuMind AI.
                </p>

            </div>

        `;

        return;
    }

    container.innerHTML = "";

    documents.slice(0, 5).forEach(doc => {

        const item =
            document.createElement("div");

        item.className =
            "document-item";

        item.innerHTML = `

            <div class="document-item-icon">

                <svg viewBox="0 0 24 24">
                    <path d="M6 3h9l4 4v14H6z"/>
                    <path d="M14 3v5h5"/>
                    <path d="M9 13h6"/>
                    <path d="M9 17h6"/>
                </svg>

            </div>

            <div class="document-item-info">

                <strong>
                    ${escapeHtml(
            doc.filename || "Document"
        )}
                </strong>

                <span>
                    ${doc.pages || 0} pages
                    •
                    ${doc.chunks || 0} chunks
                </span>

            </div>

            <div class="document-item-status">

                <span class="ready-dot"></span>

                Ready

            </div>

            <div class="document-item-actions">

                <button
                    class="document-open-button"
                    type="button"
                    title="Open document"
                >
                    →
                </button>

                <button
                    class="document-delete-button"
                    type="button"
                    title="Delete document"
                >
                    Delete
                </button>

            </div>
        `;

        const openButton =
            item.querySelector(
                ".document-open-button"
            );

        openButton.addEventListener(
            "click",
            () => {

                openDocument(doc);

            }
        );
        // =========================================================
        // DELETE BUTTON
        // =========================================================

        const deleteButton =
            item.querySelector(
                ".document-delete-button"
            );

        if (deleteButton) {

            deleteButton.addEventListener(
                "click",
                event => {

                    event.stopPropagation();

                    showDeleteModal(
                        doc
                    );

                }
            );

        }

        container.appendChild(item);

    });
}


// =========================================================
// LOAD DOCUMENTS
// =========================================================

async function loadDocuments(
    customContainer = null
) {

    if (!requireAuthentication()) {
        return;
    }

    try {

        const response =
            await fetch(
                "/api/documents",
                {
                    method: "GET",
                    headers: {
                        ...authHeaders()
                    }
                }
            );

        if (response.status === 401) {

            handleUnauthorized();

            return;
        }

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not load documents."
            );

        }

        documents =
            Array.isArray(data)
                ? data
                : data.documents || [];

        if (customContainer) {

            renderFullDocuments(
                customContainer
            );

        } else {

            renderDashboardDocuments();

        }

        updateStatistics();

    }
    catch (error) {

        console.error(
            "Load documents error:",
            error
        );

        showError(
            error.message ||
            "Unable to load documents."
        );

    }
}

// =========================================================
// CLEAR CHAT STATE
// =========================================================

function clearChatState() {

    // =====================================================
    // CLEAR NEW CHAT HISTORY
    // =====================================================

    const chatHistory =
        document.getElementById(
            "chatHistory"
        );

    if (chatHistory) {

        chatHistory.innerHTML = `
            <div class="empty-state">

                <div class="empty-icon">
                    ✦
                </div>

                <p>
                    Ask anything about your document
                </p>

            </div>
        `;
    }


    // =====================================================
    // CLEAR DYNAMIC CHAT HISTORY
    // =====================================================

    const dynamicHistory =
        document.getElementById(
            "dynamicHistory"
        );

    if (dynamicHistory) {

        dynamicHistory.innerHTML = "";
    }


    // =====================================================
    // CLEAR OLD STATIC CHAT
    // =====================================================

    const historyContainer =
        document.getElementById(
            "chatHistory"
        );

    if (historyContainer) {
        historyContainer.innerHTML = "";
    }


    // =====================================================
    // CLEAR OLD STATIC QUESTION
    // =====================================================

    const userQuestionPreview =
        document.getElementById(
            "userQuestionPreview"
        );

    if (userQuestionPreview) {

        userQuestionPreview.textContent = "";
    }


    // =====================================================
    // CLEAR OLD ANSWER
    // =====================================================

    const answerArea =
        document.getElementById(
            "answerArea"
        );

    if (answerArea) {

        answerArea.innerHTML = "";

        answerArea.hidden = true;
    }


    // =====================================================
    // CLEAR SOURCES
    // =====================================================

    const sourcesArea =
        document.getElementById(
            "sourcesArea"
        );

    if (sourcesArea) {

        sourcesArea.innerHTML = "";

        sourcesArea.hidden = true;
    }


    // =====================================================
    // CLEAR INPUT
    // =====================================================

    if (questionInput) {

        questionInput.value = "";
    }


    const dynamicQuestionInput =
        document.getElementById(
            "dynamicQuestionInput"
        );

    if (dynamicQuestionInput) {

        dynamicQuestionInput.value = "";
    }


    hideError();
}

// =========================================================
// DELETE DOCUMENT
// =========================================================

async function deleteDocument(doc, event) {

    if (event) {
        event.stopPropagation();
    }

    if (!doc || !doc.document_id) {
        console.error("Invalid document:", doc);
        return;
    }

    showDeleteModal(doc);
}


// =========================================================
// DELETE CONFIRMATION MODAL
// =========================================================

function showDeleteModal(doc) {

    if (!doc || !doc.document_id) {
        return;
    }

    const existingModal =
        document.getElementById("deleteDocumentModal");

    if (existingModal) {
        existingModal.remove();
    }

    const modal =
        document.createElement("div");

    modal.id = "deleteDocumentModal";
    modal.className = "delete-modal-overlay";

    modal.innerHTML = `
        <div
            class="delete-modal"
            role="dialog"
            aria-modal="true"
        >

            <button
                type="button"
                class="delete-modal-close"
                aria-label="Close"
            >
                ×
            </button>

            <div class="delete-modal-icon">
                <span>⌫</span>
            </div>

            <h2>
                Delete this document?
            </h2>

            <p class="delete-modal-document">
                ${escapeHtml(
        doc.filename || "Untitled document"
    )}
            </p>

            <p class="delete-modal-description">
                This will permanently delete the document,
                its indexed content, and associated chat history.
            </p>

            <div class="delete-modal-actions">

                <button
                    type="button"
                    class="delete-modal-cancel"
                >
                    Cancel
                </button>

                <button
                    type="button"
                    class="delete-modal-confirm"
                >
                    <span class="delete-confirm-icon">
                        🗑
                    </span>
                    Delete document
                </button>

            </div>

        </div>
    `;

    document.body.appendChild(modal);

    requestAnimationFrame(() => {
        modal.classList.add(
            "delete-modal-visible"
        );
    });

    const closeModal = () => {

        modal.classList.remove(
            "delete-modal-visible"
        );

        setTimeout(() => {

            if (modal.parentNode) {
                modal.remove();
            }

        }, 180);
    };


    // =====================================================
    // CLOSE BUTTON
    // =====================================================

    modal
        .querySelector(".delete-modal-close")
        ?.addEventListener(
            "click",
            closeModal
        );


    // =====================================================
    // CANCEL BUTTON
    // =====================================================

    modal
        .querySelector(".delete-modal-cancel")
        ?.addEventListener(
            "click",
            closeModal
        );


    // =====================================================
    // CONFIRM DELETE
    // =====================================================

    modal
        .querySelector(".delete-modal-confirm")
        ?.addEventListener(
            "click",
            async () => {

                const button =
                    modal.querySelector(
                        ".delete-modal-confirm"
                    );

                if (!button) {
                    return;
                }

                button.disabled = true;

                button.innerHTML = `
                    <span class="delete-spinner"></span>
                    Deleting...
                `;

                try {

                    await performDeleteDocument(
                        doc
                    );

                    closeModal();

                } catch (error) {

                    console.error(
                        "Delete failed:",
                        error
                    );

                    button.disabled = false;

                    button.innerHTML = `
                        <span class="delete-confirm-icon">
                            🗑
                        </span>
                        Delete document
                    `;
                }
            }
        );


    // =====================================================
    // CLICK OUTSIDE
    // =====================================================

    modal.addEventListener(
        "click",
        event => {

            if (
                event.target === modal
            ) {
                closeModal();
            }

        }
    );
}


// =========================================================
// ACTUAL DELETE API REQUEST
// =========================================================

async function performDeleteDocument(doc) {

    if (!doc || !doc.document_id) {

        throw new Error(
            "Invalid document."
        );
    }

    setLoading(
        true,
        "Deleting document..."
    );

    hideError();

    try {

        console.log(
            "Deleting document:",
            doc.document_id
        );

        const response = await fetch(
            `/api/documents/${doc.document_id}`,
            {
                method: "DELETE",
                headers: {
                    ...authHeaders()
                }
            }
        );

        console.log(
            "Delete response:",
            response.status
        );

        if (response.status === 401) {

            handleUnauthorized();

            throw new Error(
                "Unauthorized."
            );
        }

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to delete document."
            );
        }


        // =================================================
        // CLEAR ACTIVE DOCUMENT
        // =================================================

        if (
            currentDocumentId ===
            doc.document_id
        ) {

            currentDocumentId = null;

            currentDocument = null;

            localStorage.removeItem(
                "currentDocumentId"
            );

            clearChatState();
        }


        // =================================================
        // REFRESH DOCUMENT LIST
        // =================================================

        await loadDocuments();


        // =================================================
        // REFRESH FULL DOCUMENT PAGE
        // =================================================

        const fullDocumentsContainer =
            document.getElementById(
                "fullDocumentsContainer"
            );

        if (fullDocumentsContainer) {

            renderFullDocuments(
                "fullDocumentsContainer"
            );
        }


        // =================================================
        // RETURN TO DASHBOARD
        // =================================================

        if (!currentDocumentId) {

            showDashboardPage();

        }


        console.log(
            "Document deleted successfully."
        );

    } finally {

        setLoading(false);

    }
}

// =========================================================
// OPEN DOCUMENT
// =========================================================

function openDocument(doc) {

    if (!doc || !doc.document_id) {
        return;
    }

    // -----------------------------------------------------
    // Clear currently visible conversation
    // -----------------------------------------------------

    clearChatState();

    // -----------------------------------------------------
    // Set selected document
    // -----------------------------------------------------

    currentDocument = doc;

    currentDocumentId =
        doc.document_id;

    // -----------------------------------------------------
    // Persist selected document
    // -----------------------------------------------------

    localStorage.setItem(
        "currentDocumentId",
        currentDocumentId
    );

    console.log(
        "Opened document:",
        currentDocument.filename,
        currentDocumentId
    );

    // -----------------------------------------------------
    // Open assistant
    // -----------------------------------------------------

    openAssistantPage();

}
// =========================================================
// DOCUMIND AI - ENSURE CHAT HISTORY CONTAINER
// =========================================================

function ensureChatHistoryContainer() {

    if (!chatCard) {
        return null;
    }

    // -----------------------------------------------------
    // Already exists
    // -----------------------------------------------------

    let history =
        document.getElementById("chatHistory");

    if (history) {
        return history;
    }


    // -----------------------------------------------------
    // Find the main chat content area
    // -----------------------------------------------------

    const chatContent =
        chatCard.querySelector(".chat-content");


    if (!chatContent) {

        console.error(
            "chat-content not found inside chatCard."
        );

        return null;
    }


    // -----------------------------------------------------
    // Create history container
    // -----------------------------------------------------

    history =
        document.createElement("div");

    history.id =
        "chatHistory";

    history.className =
        "chat-history";


    // -----------------------------------------------------
    // Hide the ORIGINAL static chat messages
    //
    // Important:
    // We only hide messages that are NOT inside
    // our new #chatHistory container.
    // -----------------------------------------------------

    const oldMessages =
        chatContent.querySelectorAll(
            ".chat-message"
        );


    oldMessages.forEach(
        message => {

            if (
                !history.contains(
                    message
                )
            ) {

                message.hidden = true;

            }

        }
    );


    // -----------------------------------------------------
    // Insert history BEFORE the input area
    // -----------------------------------------------------

    if (questionInput) {

        const inputWrapper =
            questionInput.closest(
                ".chat-input"
            ) ||
            questionInput.parentElement;


        if (
            inputWrapper &&
            inputWrapper.parentNode ===
            chatContent
        ) {

            chatContent.insertBefore(
                history,
                inputWrapper
            );

        }
        else {

            chatContent.appendChild(
                history
            );

        }

    }
    else {

        chatContent.appendChild(
            history
        );

    }


    return history;
}
// =========================================================
// CREATE MAIN CHAT HISTORY CONTAINER
// =========================================================

function createChatHistoryContainer() {

    // ---------------------------------------------------------
    // ALREADY EXISTS
    // ---------------------------------------------------------

    let history =
        document.getElementById("chatHistory");

    if (history) {
        return history;
    }

    // ---------------------------------------------------------
    // CHAT CARD CHECK
    // ---------------------------------------------------------

    if (!chatCard) {

        console.error(
            "chatCard not found."
        );

        return null;
    }

    // ---------------------------------------------------------
    // FIND CHAT CONTENT
    // ---------------------------------------------------------

    const chatContent =
        chatCard.querySelector(".chat-content");

    if (!chatContent) {

        console.error(
            "chat-content not found."
        );

        return null;
    }

    // ---------------------------------------------------------
    // CREATE HISTORY CONTAINER
    // ---------------------------------------------------------

    history =
        document.createElement("div");

    history.id =
        "chatHistory";

    history.className =
        "chat-history";

    // ---------------------------------------------------------
    // INSERT BEFORE INPUT
    // ---------------------------------------------------------

    if (questionInput) {

        const inputWrapper =
            questionInput.closest(".chat-input") ||
            questionInput.parentElement;

        if (
            inputWrapper &&
            inputWrapper.parentNode === chatContent
        ) {

            chatContent.insertBefore(
                history,
                inputWrapper
            );

        } else {

            chatContent.appendChild(
                history
            );
        }

    } else {

        chatContent.appendChild(
            history
        );
    }

    return history;
}
// =========================================================
// AI ASSISTANT PAGE
// =========================================================

function openAssistantPage() {

    if (!requireAuthentication()) {
        return;
    }

    // ---------------------------------------------------------
    // DOCUMENT CHECK
    // ---------------------------------------------------------

    if (!currentDocumentId) {

        showError(
            "Please select a document first."
        );

        return;
    }

    // ---------------------------------------------------------
    // NAVIGATION
    // ---------------------------------------------------------

    setActiveNav("assistant");

    // ---------------------------------------------------------
    // HIDE DASHBOARD
    // ---------------------------------------------------------

    hideDashboardSections();

    // ---------------------------------------------------------
    // SHOW MAIN CHAT CARD
    // ---------------------------------------------------------

    if (chatCard) {
        chatCard.hidden = false;
    }

    // ---------------------------------------------------------
    // HIDE DYNAMIC PAGE
    // ---------------------------------------------------------

    if (dynamicPage) {
        dynamicPage.hidden = true;
    }

    // ---------------------------------------------------------
    // UPDATE SELECTED DOCUMENT INFO
    // ---------------------------------------------------------

    updateChatDocumentInfo();

    // ---------------------------------------------------------
    // RESTORE CHAT HISTORY FOR THE SELECTED DOCUMENT
    // ---------------------------------------------------------

    const mainHistory = document.getElementById("chatHistory");

    if (mainHistory) {
        loadChatHistory();
}
}
// =========================================================
// UPDATE CHAT INFO
// =========================================================

function updateChatDocumentInfo() {

    const chatDocumentName =
        document.getElementById(
            "chatDocumentName"
        );

    if (!chatDocumentName) {
        return;
    }

    if (!currentDocument) {

        chatDocumentName.textContent =
            "Select a document to begin.";

        return;
    }

    chatDocumentName.textContent =
        `${currentDocument.filename} • ` +
        `${currentDocument.pages || 0} pages • ` +
        `${currentDocument.chunks || 0} chunks`;

}
// =========================================================
// ASK QUESTION
// =========================================================

async function askQuestion() {

    if (!requireAuthentication()) {
        return;
    }

    // ---------------------------------------------------------
    // DOCUMENT CHECK
    // ---------------------------------------------------------

    if (!currentDocumentId) {

        showError(
            "Please select a document first."
        );

        return;
    }

    // ---------------------------------------------------------
    // INPUT CHECK
    // ---------------------------------------------------------

    if (!questionInput) {
        return;
    }

    const question =
        questionInput.value.trim();

    if (!question) {

        showError(
            "Please enter a question."
        );

        questionInput.focus();

        return;
    }

    try {

        // -----------------------------------------------------
        // DISABLE BUTTON
        // -----------------------------------------------------

        if (askButton) {
            askButton.disabled = true;
        }

        setLoading(
            true,
            "DocuMind AI is thinking..."
        );

        hideError();

        // -----------------------------------------------------
        // SEND QUESTION TO BACKEND
        // -----------------------------------------------------

        const response =
            await fetch(
                `/api/chat/${currentDocumentId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        ...authHeaders()
                    },

                    body: JSON.stringify({
                        question: question
                    })
                }
            );

        // -----------------------------------------------------
        // AUTH ERROR
        // -----------------------------------------------------

        if (response.status === 401) {

            handleUnauthorized();

            return;
        }

        // -----------------------------------------------------
        // READ RESPONSE
        // -----------------------------------------------------

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "AI request failed."
            );
        }

        // -----------------------------------------------------
        // GET CHAT HISTORY
        // -----------------------------------------------------

        let history =
            document.getElementById(
                "chatHistory"
            );

        if (!history) {

            history =
                createChatHistoryContainer();
        }

        if (!history) {
            return;
        }

        // -----------------------------------------------------
        // REMOVE ONLY WELCOME / EMPTY STATE
        //
        // NEVER clear history.innerHTML here.
        // This is what preserves Question 1 when
        // Question 2 is asked.
        // -----------------------------------------------------

        history
            .querySelectorAll(
                ".chat-welcome, .empty-state"
            )
            .forEach(element => {

                element.remove();
            });

        // -----------------------------------------------------
        // APPEND NEW QUESTION + ANSWER
        // -----------------------------------------------------

        history.insertAdjacentHTML(
            "beforeend",
            createChatMessage(
                question,
                data
            )
        );

        // =====================================================
        // NOTIFICATION - AI RESPONSE
        // =====================================================
        addNotification({
            type: "ai",
            title: "AI response ready",
            message:
                "DocuMind AI has answered your question.",
            icon: "fa-robot"
        });
        // -----------------------------------------------------
        // CLEAR INPUT
        // -----------------------------------------------------

        questionInput.value = "";

        // -----------------------------------------------------
        // RENDER MATH
        // -----------------------------------------------------
        if (
            typeof renderMath === "function"
        ) {

            renderMath(history);
        }

        // -----------------------------------------------------
        // UPDATE USAGE
        // -----------------------------------------------------

        if (
            typeof updateStatistics === "function"
        ) {

            updateStatistics();
        }

        // -----------------------------------------------------
        // SCROLL TO LATEST MESSAGE
        // -----------------------------------------------------

        history.scrollTop =
            history.scrollHeight;

    }
    catch (error) {

        console.error(
            "Chat error:",
            error
        );

        showError(
            error.message ||
            "Unable to get AI response."
        );

    }
    finally {

        if (askButton) {
            askButton.disabled = false;
        }

        setLoading(false);
    }
}
// =========================================================
// DYNAMIC CHAT
// =========================================================

async function askDynamicQuestion() {

    const input =
        document.getElementById(
            "dynamicQuestionInput"
        );

    const button =
        document.getElementById(
            "dynamicAskButton"
        );

    if (!input) {
        return;
    }

    const question =
        input.value.trim();

    if (!question) {
        return;
    }

    if (!currentDocumentId) {

        showError(
            "Please select a document first."
        );

        return;
    }

    try {

        button.disabled = true;

        setLoading(
            true,
            "DocuMind AI is thinking..."
        );

        const response =
            await fetch(
                `/api/chat/${currentDocumentId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        ...authHeaders()
                    },

                    body: JSON.stringify({
                        question:
                            question
                    })
                }
            );

        if (response.status === 401) {

            handleUnauthorized();

            return;
        }

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "AI request failed."
            );

        }

        const history =
            document.getElementById(
                "dynamicHistory"
            );

        if (history) {

            history.insertAdjacentHTML(
                "beforeend",

                createChatMessage(
                    question,
                    data
                )
            );
            // Render equations in the newly added message
            renderMath(history);
        }

        input.value = "";
        updateStatistics();

    }
    catch (error) {

        console.error(
            "Dynamic chat error:",
            error
        );

        showError(
            error.message ||
            "Unable to get AI response."
        );

    }
    finally {

        button.disabled = false;

        setLoading(false);

    }
}


// =========================================================
// CHAT MESSAGE UI
// =========================================================
function createChatMessage(
    question,
    data
) {
    let answer =
        data.answer || "";

    if (typeof answer !== "string") {
        answer =
            JSON.stringify(answer);
    }

    // =========================================================
    // AI PREFERENCES - SHOW SOURCES
    // =========================================================

    let sourcesHTML = "";

    const chatSettings =
        getDocuMindSettings();

    const shouldShowSources =
        chatSettings.ai.showSources !== false;

    if (
        shouldShowSources &&
        Array.isArray(data.sources) &&
        data.sources.length
    ) {

        sourcesHTML = `
        <div class="sources-area">

            <span class="sources-title">
                Sources
            </span>

            <div class="sources-list">

                ${data.sources.map(
            source => {

                const filename =
                    source.filename ||
                    "Uploaded document";

                const page =
                    source.page ??
                    "Unknown";

                return `
                            <span class="source-badge">
                                ${escapeHtml(filename)}
                                • Page
                                ${escapeHtml(
                    String(page)
                )}
                            </span>
                        `;

            }
        ).join("")}

            </div>

        </div>
    `;
    }
    return `
        <div class="chat-message user-message">

            <div class="message-label">
                You
            </div>

            <div class="message-bubble">
                ${escapeHtml(question)}
            </div>

        </div>

        <div class="chat-message ai-message">

            <div class="message-label">
                <span class="ai-mark">D</span>
                DocuMind AI
            </div>

            <div class="answer-area">
                ${formatAnswer(answer)}
            </div>

            ${sourcesHTML}

        </div>
    `;
}

// =========================================================
// DISPLAY CHAT MESSAGE
// =========================================================

function displayAnswer(data, question) {

    const chatHistory =
        document.getElementById("chatHistory");

    if (!chatHistory) {
        console.error(
            "chatHistory container not found."
        );
        return;
    }

    // -----------------------------------------------------
    // GET ANSWER
    // -----------------------------------------------------

    let answer = data.answer || "";

    if (Array.isArray(answer)) {

        answer = answer
            .map(item => item.text || "")
            .join("\n");

    }

    if (
        typeof answer === "object" &&
        answer !== null
    ) {

        answer =
            answer.text ||
            JSON.stringify(answer);

    }

    // -----------------------------------------------------
    // CREATE USER MESSAGE
    // -----------------------------------------------------

    const userMessage =
        document.createElement("div");

    userMessage.className =
        "chat-message user-message";

    userMessage.innerHTML = `
        <div class="message-label">
            You
        </div>

        <div class="message-bubble">
            ${escapeHtml(question)}
        </div>
    `;

    // -----------------------------------------------------
    // CREATE AI MESSAGE
    // -----------------------------------------------------

    const aiMessage =
        document.createElement("div");

    aiMessage.className =
        "chat-message ai-message";

    // -----------------------------------------------------
    // ANSWER
    // -----------------------------------------------------

    const answerContainer =
        document.createElement("div");

    answerContainer.className =
        "answer-area";

    answerContainer.innerHTML =
        formatAnswer(answer);

    // -----------------------------------------------------
    // AI LABEL
    // -----------------------------------------------------

    const aiLabel =
        document.createElement("div");

    aiLabel.className =
        "message-label";

    aiLabel.innerHTML = `
        <span class="ai-mark">
            D
        </span>

        DocuMind AI
    `;

    aiMessage.appendChild(
        aiLabel
    );

    aiMessage.appendChild(
        answerContainer
    );

    // -----------------------------------------------------
    // SOURCES
    // AI PREFERENCES: SHOW SOURCES
    // -----------------------------------------------------

    const displaySettings =
        getDocuMindSettings();

    const shouldShowSources =
        displaySettings.ai.showSources !== false;

    if (
        shouldShowSources &&
        Array.isArray(data.sources) &&
        data.sources.length > 0
    ) {

        const sourcesArea =
            document.createElement("div");

        sourcesArea.className =
            "sources-area";

        sourcesArea.innerHTML = `
            <span class="sources-title">
                Sources
            </span>

            <div class="sources-list"></div>
        `;

        const sourcesList =
            sourcesArea.querySelector(
                ".sources-list"
            );

        data.sources.forEach(
            source => {

                const badge =
                    document.createElement(
                        "span"
                    );

                badge.className =
                    "source-badge";

                const filename =
                    source.filename ||
                    "Uploaded document";

                const page =
                    source.page ??
                    "Unknown";

                badge.textContent =
                    `${filename} • Page ${page}`;

                sourcesList.appendChild(
                    badge
                );

            }
        );

        aiMessage.appendChild(
            sourcesArea
        );
    }

    // -----------------------------------------------------
    // APPEND BOTH MESSAGES
    // -----------------------------------------------------

    chatHistory.appendChild(
        userMessage
    );

    chatHistory.appendChild(
        aiMessage
    );

    // -----------------------------------------------------
    // RENDER MATH
    // -----------------------------------------------------

    renderMath(
        answerContainer
    );

    // -----------------------------------------------------
    // SCROLL TO LATEST MESSAGE
    // -----------------------------------------------------

    aiMessage.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });
}
// =========================================================
// LOAD CHAT HISTORY FOR CURRENT DOCUMENT
// =========================================================

async function loadChatHistory() {

    if (!currentDocumentId) {
        return;
    }

    try {

        // -----------------------------------------------------
        // GET CHAT HISTORY CONTAINER
        // -----------------------------------------------------

        let history =
            document.getElementById("chatHistory");

        if (!history) {

            history =
                createChatHistoryContainer();
        }

        if (!history) {
            return;
        }

        // -----------------------------------------------------
        // SHOW LOADING
        // -----------------------------------------------------

        history.innerHTML = `
            <div class="chat-history-loading">
                Loading your conversation...
            </div>
        `;

        // -----------------------------------------------------
        // REQUEST HISTORY
        // -----------------------------------------------------

        const response =
            await fetch(
                `/api/chat/${currentDocumentId}/history`,
                {
                    method: "GET",

                    headers: {
                        ...authHeaders()
                    }
                }
            );

        // -----------------------------------------------------
        // AUTH ERROR
        // -----------------------------------------------------

        if (response.status === 401) {

            handleUnauthorized();

            return;
        }

        // -----------------------------------------------------
        // REQUEST ERROR
        // -----------------------------------------------------

        if (!response.ok) {

            console.error(
                "Unable to load chat history:",
                response.status
            );

            history.innerHTML = `
                <div class="chat-history-error">
                    Unable to load conversation.
                </div>
            `;

            return;
        }

        // -----------------------------------------------------
        // READ RESPONSE
        // -----------------------------------------------------

        const data =
            await response.json();

        // -----------------------------------------------------
        // NORMALIZE BACKEND RESPONSE
        // -----------------------------------------------------

        let messages = [];

        if (Array.isArray(data)) {

            messages = data;

        }
        else if (
            data &&
            Array.isArray(data.history)
        ) {

            messages =
                data.history;

        }
        else if (
            data &&
            Array.isArray(data.messages)
        ) {

            messages =
                data.messages;

        }
        else if (
            data &&
            Array.isArray(data.data)
        ) {

            messages =
                data.data;
        }

        console.log(
            "Loaded chat history:",
            currentDocumentId,
            messages
        );

        // -----------------------------------------------------
        // CLEAR CURRENT DISPLAY
        // -----------------------------------------------------

        history.innerHTML = "";

        // -----------------------------------------------------
        // NO PREVIOUS QUESTIONS
        // -----------------------------------------------------

        if (!messages.length) {

            history.innerHTML = `
                <div class="chat-welcome">

                    <div class="chat-welcome-icon">
                        ✦
                    </div>

                    <h3>
                        Ready to explore your document
                    </h3>

                    <p>
                        Ask questions, summarize sections,
                        extract key information, or clarify concepts.
                    </p>

                    <span>
                        DocuMind AI will answer using the content
                        of your uploaded document.
                    </span>

                </div>
            `;

            return;
        }

        // -----------------------------------------------------
        // RENDER ALL PREVIOUS MESSAGES
        // -----------------------------------------------------

        messages.forEach(message => {

            const question =
                message.question || "";

            const answer =
                message.answer || "";

            const sources =
                message.sources || [];

            history.insertAdjacentHTML(
                "beforeend",

                createChatMessage(
                    question,
                    {
                        answer: answer,
                        sources: sources
                    }
                )
            );
        });

        // -----------------------------------------------------
        // RENDER MATH
        // -----------------------------------------------------

        if (
            typeof renderMath === "function"
        ) {

            renderMath(history);
        }

        // -----------------------------------------------------
        // SCROLL TO LATEST
        // -----------------------------------------------------

        history.scrollTop =
            history.scrollHeight;

    }
    catch (error) {

        console.error(
            "History error:",
            error
        );

        const history =
            document.getElementById(
                "chatHistory"
            );

        if (history) {

            history.innerHTML = `
                <div class="chat-history-error">
                    Unable to load conversation.
                </div>
            `;
        }
    }
}
// =========================================================
// HISTORY PAGE
// =========================================================
async function showHistoryPage() {
    if (!requireAuthentication()) {
        return;
    }

    setActiveNav("history");
    hideDashboardSections();

    showDynamicPage(`
        <div class="section-title">
            <span class="section-label">
                ACTIVITY
            </span>

            <h2>
                Chat History
            </h2>

            <p>
                Review your previous questions and AI answers.
            </p>
        </div>

        <div id="historyDocuments" class="history-list">
            Loading history...
        </div>
    `);

    const container =
        document.getElementById("historyDocuments");

    if (!container) {
        return;
    }

    // ---------------------------------------------------------
    // LOAD DOCUMENTS
    // ---------------------------------------------------------

    if (!documents.length) {
        await loadDocuments();
    }

    if (!documents.length) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    ◷
                </div>

                <h3>
                    No history yet
                </h3>

                <p>
                    Ask questions about your documents
                    and your activity will appear here.
                </p>
            </div>
        `;

        return;
    }

    container.innerHTML = "";

    let totalHistoryMessages = 0;

    // ---------------------------------------------------------
    // LOAD HISTORY FOR EVERY DOCUMENT
    // ---------------------------------------------------------

    for (const doc of documents) {

        try {

            console.log(
                "Loading history for:",
                doc.filename,
                doc.document_id
            );

            const response =
                await fetch(
                    `/api/chat/${doc.document_id}/history`,
                    {
                        method: "GET",

                        headers: {
                            ...authHeaders()
                        }
                    }
                );

            console.log(
                "History response:",
                doc.filename,
                response.status
            );

            if (response.status === 401) {

                handleUnauthorized();

                return;
            }

            if (!response.ok) {

                console.error(
                    "History request failed:",
                    doc.filename,
                    response.status
                );

                continue;
            }

            const rawData =
                await response.json();

            console.log(
                "History raw data:",
                doc.filename,
                rawData
            );

            // -------------------------------------------------
            // SUPPORT MULTIPLE BACKEND RESPONSE FORMATS
            // -------------------------------------------------

            let history = [];

            if (Array.isArray(rawData)) {

                history = rawData;

            }
            else if (
                rawData &&
                Array.isArray(rawData.history)
            ) {

                history = rawData.history;

            }
            else if (
                rawData &&
                Array.isArray(rawData.messages)
            ) {

                history = rawData.messages;

            }
            else if (
                rawData &&
                Array.isArray(rawData.data)
            ) {

                history = rawData.data;

            }

            console.log(
                "Normalized history:",
                doc.filename,
                history
            );

            // -------------------------------------------------
            // NO HISTORY FOR THIS DOCUMENT
            // -------------------------------------------------

            if (!history.length) {
                continue;
            }

            totalHistoryMessages +=
                history.length;

            // -------------------------------------------------
            // DOCUMENT HISTORY BLOCK
            // -------------------------------------------------

            const block =
                document.createElement("div");

            block.className =
                "history-document";

            block.innerHTML = `
                <div class="history-document-header">
                    <div class="history-document-title">
                        ${escapeHtml(
                doc.filename ||
                "Uploaded document"
            )}
                    </div>

                    <div class="history-document-count">
                        ${history.length}
                        ${history.length === 1
                    ? "question"
                    : "questions"}
                    </div>
                </div>
            `;

            // -------------------------------------------------
            // RENDER QUESTIONS
            // -------------------------------------------------

            history.forEach(
                message => {

                    const question =
                        message.question ||
                        "";

                    const answer =
                        message.answer ||
                        "";

                    block.insertAdjacentHTML(
                        "beforeend",
                        `
                        <div class="history-message">

                            <div class="history-question">
                                You
                            </div>

                            <div class="history-answer">
                                ${escapeHtml(
                            question
                        )}
                            </div>

                            <div
                                class="history-question"
                                style="margin-top: 14px;"
                            >
                                DocuMind AI
                            </div>

                            <div class="history-answer">
                                ${formatAnswer(
                            answer
                        )}
                            </div>

                        </div>
                        `
                    );
                }
            );

            container.appendChild(block);

        }
        catch (error) {

            console.error(
                "History document error:",
                doc.filename,
                error
            );
        }
    }

    // ---------------------------------------------------------
    // FINAL EMPTY STATE
    // ---------------------------------------------------------

    if (totalHistoryMessages === 0) {

        container.innerHTML = `
            <div class="empty-state">

                <div class="empty-icon">
                    ◷
                </div>

                <h3>
                    No questions asked yet
                </h3>

                
                <p>
                    Your document conversations
                    will appear here.
                </p>

            </div>
        `;

    }

    // ---------------------------------------------------------
    // RENDER MATH
    // ---------------------------------------------------------

    if (
        typeof renderMath === "function"
    ) {
        renderMath(container);
    }
}
// =========================================================
// DOCUMIND AI - BILLING HELPERS
// FINAL DEMO PAYMENT UI
// =========================================================

function removeDemoPaymentModal() {
    const modal = document.getElementById(
        "demoPaymentModal"
    );

    if (modal) {
        modal.remove();
    }
}


function closeDemoPaymentModal() {
    removeDemoPaymentModal();
}


function createDemoPaymentModal(amount) {

    removeDemoPaymentModal();

    const modal =
        document.createElement("div");

    modal.id =
        "demoPaymentModal";

    modal.className =
        "billing-modal-overlay";

    modal.innerHTML = `
        <div
            class="billing-payment-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="demoPaymentTitle"
        >

            <button
                type="button"
                class="billing-modal-close"
                id="billingModalClose"
                aria-label="Close"
            >
                ×
            </button>

            <div class="billing-modal-icon">
                ✦
            </div>

            <div class="billing-modal-header">

                <span class="billing-modal-label">
                    DOCUMIND PREMIUM
                </span>

                <h2 id="demoPaymentTitle">
                    Upgrade to Premium
                </h2>

                <p>
                    Unlock higher limits and more powerful
                    document intelligence.
                </p>

            </div>


            <div class="billing-payment-summary">

                <div class="billing-payment-summary-row">

                    <span>
                        Premium plan
                    </span>

                    <strong>
                        ₹${amount} / month
                    </strong>

                </div>

                <div class="billing-payment-summary-divider"></div>

                <div class="billing-payment-feature">
                    <span>✓</span>
                    <span>50 documents</span>
                </div>

                <div class="billing-payment-feature">
                    <span>✓</span>
                    <span>500 AI questions</span>
                </div>

                <div class="billing-payment-feature">
                    <span>✓</span>
                    <span>25 MB PDF uploads</span>
                </div>

                <div class="billing-payment-feature">
                    <span>✓</span>
                    <span>Advanced AI workspace</span>
                </div>

            </div>


            <div class="billing-demo-notice">

                <div class="billing-demo-notice-icon">
                    ✓
                </div>

                <div>
                    <strong>
                        Demo payment mode
                    </strong>

                    <p>
                        No real money will be charged.
                        This payment only simulates a successful
                        subscription.
                    </p>
                </div>

            </div>


            <div
                id="billingPaymentStatus"
                class="billing-payment-status"
                hidden
            ></div>


            <div class="billing-modal-actions">

                <button
                    type="button"
                    class="billing-cancel-button"
                    id="billingCancelPayment"
                >
                    Cancel
                </button>

                <button
                    type="button"
                    class="billing-pay-button"
                    id="billingPayButton"
                >
                    Pay ₹${amount}
                </button>

            </div>

            <p class="billing-secure-note">
                Demo checkout · Secure application flow
            </p>

        </div>
    `;

    document.body.appendChild(modal);


    // ---------------------------------------------------------
    // CLOSE
    // ---------------------------------------------------------

    const closeButton =
        document.getElementById(
            "billingModalClose"
        );

    const cancelButton =
        document.getElementById(
            "billingCancelPayment"
        );

    if (closeButton) {
        closeButton.addEventListener(
            "click",
            closeDemoPaymentModal
        );
    }

    if (cancelButton) {
        cancelButton.addEventListener(
            "click",
            closeDemoPaymentModal
        );
    }


    // ---------------------------------------------------------
    // BACKDROP CLICK
    // ---------------------------------------------------------

    modal.addEventListener(
        "click",
        event => {

            if (
                event.target === modal
            ) {
                closeDemoPaymentModal();
            }

        }
    );


    // ---------------------------------------------------------
    // ESC KEY
    // ---------------------------------------------------------

    document.addEventListener(
        "keydown",
        function billingEscapeHandler(event) {

            if (
                event.key === "Escape" &&
                document.getElementById(
                    "demoPaymentModal"
                )
            ) {

                closeDemoPaymentModal();

                document.removeEventListener(
                    "keydown",
                    billingEscapeHandler
                );

            }

        }
    );


    // ---------------------------------------------------------
    // PAY
    // ---------------------------------------------------------

    const payButton =
        document.getElementById(
            "billingPayButton"
        );

    if (payButton) {

        payButton.addEventListener(
            "click",
            completeDemoPayment
        );

    }
}


async function startDemoPayment() {

    try {

        const response =
            await fetch(
                "/api/payment/create",
                {
                    method: "POST",

                    headers: {
                        ...authHeaders()
                    }
                }
            );


        if (
            response.status === 401
        ) {

            handleUnauthorized();

            return;

        }


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to create payment."
            );

        }


        console.log(
            "Demo payment created:",
            data
        );


        createDemoPaymentModal(
            data.amount || 499
        );


        // Store payment information
        window.docuMindPendingPayment = {
            order_id:
                data.order_id,

            payment_id:
                data.payment_id,

            amount:
                data.amount || 499
        };

    }
    catch (error) {

        console.error(
            "Demo payment creation error:",
            error
        );


        showError(
            error.message ||
            "Unable to start payment."
        );

    }

}


async function completeDemoPayment() {

    const payment =
        window.docuMindPendingPayment;


    if (!payment) {

        showError(
            "Payment session expired. Please try again."
        );

        closeDemoPaymentModal();

        return;

    }


    const payButton =
        document.getElementById(
            "billingPayButton"
        );

    const cancelButton =
        document.getElementById(
            "billingCancelPayment"
        );

    const statusBox =
        document.getElementById(
            "billingPaymentStatus"
        );


    if (payButton) {

        payButton.disabled = true;

        payButton.innerHTML =
            `
            <span class="billing-button-spinner"></span>
            Processing...
            `;

    }


    if (cancelButton) {
        cancelButton.disabled = true;
    }


    if (statusBox) {

        statusBox.hidden = false;

        statusBox.className =
            "billing-payment-status processing";

        statusBox.innerHTML =
            `
            <span class="billing-status-spinner"></span>
            Processing your demo payment...
            `;

    }


    try {

        // -----------------------------------------------------
        // VERIFY PAYMENT
        // -----------------------------------------------------

        const response =
            await fetch(
                "/api/payment/verify",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        ...authHeaders()
                    },

                    body: JSON.stringify({

                        order_id:
                            payment.order_id,

                        payment_id:
                            payment.payment_id

                    })
                }
            );


        if (
            response.status === 401
        ) {

            handleUnauthorized();

            return;

        }


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Payment verification failed."
            );

        }


        console.log(
            "Demo payment verified:",
            data
        );


        // -----------------------------------------------------
        // SUCCESS STATE
        // -----------------------------------------------------

        if (statusBox) {

            statusBox.className =
                "billing-payment-status success";

            statusBox.innerHTML =
                `
                <span class="billing-success-icon">
                    ✓
                </span>

                <div>
                    <strong>
                        Payment successful
                    </strong>

                    <span>
                        Premium has been activated.
                    </span>
                </div>
                `;

        }


        if (payButton) {

            payButton.innerHTML =
                `
                ✓ Premium activated
                `;

        }


        // -----------------------------------------------------
        // RELOAD USER
        // -----------------------------------------------------

        await loadCurrentUser();


        // -----------------------------------------------------
        // WAIT A MOMENT SO USER SEES SUCCESS
        // -----------------------------------------------------

        await new Promise(
            resolve =>
                setTimeout(
                    resolve,
                    900
                )
        );


        removeDemoPaymentModal();


        delete window.docuMindPendingPayment;


        showSuccess(
            "Premium activated successfully."
        );


        // -----------------------------------------------------
        // RE-RENDER BILLING
        // -----------------------------------------------------

        await showSettingsPage();

    }
    catch (error) {

        console.error(
            "Demo payment verification error:",
            error
        );


        if (statusBox) {

            statusBox.hidden = false;

            statusBox.className =
                "billing-payment-status error";

            statusBox.innerHTML =
                `
                <strong>
                    Payment could not be completed
                </strong>

                <span>
                    ${escapeHtml(
                    error.message ||
                    "Please try again."
                )}
                </span>
                `;

        }


        if (payButton) {

            payButton.disabled =
                false;

            payButton.innerHTML =
                `
                Try Again
                `;

        }


        if (cancelButton) {
            cancelButton.disabled =
                false;
        }

    }

}

// =========================================================
// PAYMENT HISTORY
// =========================================================

async function loadPaymentHistory() {

    const container =
        document.getElementById(
            "paymentHistoryContainer"
        );

    // ---------------------------------------------------------
    // CONTAINER CHECK
    // ---------------------------------------------------------

    if (!container) {

        console.warn(
            "paymentHistoryContainer not found."
        );

        return;
    }

    // ---------------------------------------------------------
    // SHOW LOADING STATE
    // ---------------------------------------------------------

    container.innerHTML = `
        <div class="payment-history-loading">

            <div class="payment-loading-icon">
                ◷
            </div>

            <div>
                <strong>
                    Loading payment history
                </strong>

                <p>
                    Retrieving your recent transactions...
                </p>
            </div>

        </div>
    `;

    try {

        console.log(
            "Loading payment history..."
        );

        // -----------------------------------------------------
        // API REQUEST
        // -----------------------------------------------------

        const response =
            await fetch(
                `/api/payment/history?_=${Date.now()}`,
                {
                    method: "GET",

                    cache: "no-store",

                    headers: {
                        ...authHeaders()
                    }
                }
            );

        console.log(
            "Payment history response:",
            response.status
        );

        // -----------------------------------------------------
        // AUTH ERROR
        // -----------------------------------------------------

        if (response.status === 401) {

            handleUnauthorized();

            return;
        }

        // -----------------------------------------------------
        // READ RESPONSE SAFELY
        // -----------------------------------------------------

        const rawText =
            await response.text();

        console.log(
            "Payment history raw response:",
            rawText
        );

        let data = {};

        try {

            data =
                rawText
                    ? JSON.parse(rawText)
                    : {};

        }
        catch (jsonError) {

            console.error(
                "Payment history JSON error:",
                jsonError
            );

            throw new Error(
                "Invalid payment history response."
            );
        }

        // -----------------------------------------------------
        // API ERROR
        // -----------------------------------------------------

        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.message ||
                `Unable to load payment history (${response.status}).`
            );
        }

        // -----------------------------------------------------
        // NORMALIZE RESPONSE
        //
        // Supports:
        //
        // []
        //
        // {
        //   payments: []
        // }
        //
        // {
        //   history: []
        // }
        //
        // {
        //   data: []
        // }
        // -----------------------------------------------------

        let payments = [];

        if (Array.isArray(data)) {

            payments = data;

        }
        else if (
            data &&
            Array.isArray(data.payments)
        ) {

            payments =
                data.payments;

        }
        else if (
            data &&
            Array.isArray(data.history)
        ) {

            payments =
                data.history;

        }
        else if (
            data &&
            Array.isArray(data.data)
        ) {

            payments =
                data.data;
        }

        console.log(
            "Normalized payment history:",
            payments
        );

        // -----------------------------------------------------
        // NO PAYMENTS
        // -----------------------------------------------------

        if (!payments.length) {

            container.innerHTML = `
                <div class="payment-history-empty">

                    <div class="payment-empty-icon">
                        ✓
                    </div>

                    <h3>
                        No payments yet
                    </h3>

                    <p>
                        Your completed DocuMind AI
                        subscription payments will appear here.
                    </p>

                </div>
            `;

            return;
        }

        // -----------------------------------------------------
        // RENDER PAYMENT HISTORY
        // -----------------------------------------------------

        container.innerHTML = `
            <div class="payment-history-list">

                ${payments.map(payment => {

            const amount =
                payment.amount_in_rupees ??
                payment.amount ??
                0;

            const currency =
                payment.currency ||
                "INR";

            const plan =
                payment.plan ||
                "Premium";

            const status =
                payment.status ||
                "paid";

            const paymentId =
                payment.payment_id ||
                payment.order_id ||
                "—";

            const createdAt =
                payment.paid_at ||
                payment.created_at;

            let dateText =
                "—";

            if (createdAt) {

                const date =
                    new Date(
                        createdAt
                    );

                if (
                    !Number.isNaN(
                        date.getTime()
                    )
                ) {

                    dateText =
                        date.toLocaleDateString(
                            "en-IN",
                            {
                                day: "2-digit",
                                month: "short",
                                year: "numeric"
                            }
                        );
                }
            }

            const normalizedStatus =
                String(status)
                    .toLowerCase();

            const statusClass =
                normalizedStatus === "paid" ||
                    normalizedStatus === "success" ||
                    normalizedStatus === "completed"
                    ? "payment-status-success"
                    : normalizedStatus === "pending"
                        ? "payment-status-pending"
                        : "payment-status-failed";

            const statusLabel =
                normalizedStatus === "paid" ||
                    normalizedStatus === "success" ||
                    normalizedStatus === "completed"
                    ? "Paid"
                    : normalizedStatus === "pending"
                        ? "Pending"
                        : "Failed";

            return `
                        <div class="payment-history-row">

                            <div class="payment-history-main">

                                <div class="payment-history-icon">
                                    ✓
                                </div>

                                <div class="payment-history-info">

                                    <strong>
                                        ${escapeHtml(
                plan
            )}
                                        Subscription
                                    </strong>

                                    <span>
                                        ${escapeHtml(
                dateText
            )}
                                    </span>

                                </div>

                            </div>


                            <div class="payment-history-reference">

                                <span>
                                    Transaction
                                </span>

                                <strong>
                                    ${escapeHtml(
                String(
                    paymentId
                )
            )}
                                </strong>

                            </div>


                            <div class="payment-history-amount">

                                <strong>
                                    ₹${Number(
                amount
            ).toLocaleString(
                "en-IN"
            )}
                                </strong>

                                <span>
                                    ${escapeHtml(
                currency
            )}
                                </span>

                            </div>


                            <div class="
                                payment-history-status
                                ${statusClass}
                            ">

                                ${statusLabel}

                            </div>

                        </div>
                    `;

        }).join("")}

            </div>
        `;

        console.log(
            `Rendered ${payments.length} payment(s).`
        );

    }
    catch (error) {

        console.error(
            "Payment history error:",
            error
        );

        // -----------------------------------------------------
        // IMPORTANT:
        // NEVER leave "Loading payment history..."
        // -----------------------------------------------------

        container.innerHTML = `
            <div class="payment-history-error">

                <div class="payment-error-icon">
                    !
                </div>

                <div>

                    <strong>
                        Unable to load payment history
                    </strong>

                    <p>
                        ${escapeHtml(
            error.message ||
            "Please try again."
        )}
                    </p>

                    <button
                        type="button"
                        class="payment-retry-button"
                        onclick="loadPaymentHistory()"
                    >
                        Try Again
                    </button>

                </div>

            </div>
        `;
    }
}
// =========================================================
// PAYMENT HISTORY ITEM
// =========================================================

function createPaymentHistoryItem(
    payment
) {

    const amount =
        payment.amount_in_rupees ??
        payment.amount ??
        499;

    const currency =
        payment.currency ||
        "INR";

    const plan =
        payment.plan ||
        "Premium";

    const status =
        String(
            payment.status ||
            "success"
        ).toLowerCase();

    const paymentId =
        payment.payment_id ||
        payment.id ||
        "—";

    const orderId =
        payment.order_id ||
        "—";

    const rawDate =
        payment.paid_at ||
        payment.created_at;

    let formattedDate =
        "Date unavailable";

    if (rawDate) {

        const date =
            new Date(rawDate);

        if (!isNaN(date.getTime())) {

            formattedDate =
                date.toLocaleString(
                    "en-IN",
                    {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit"
                    }
                );
        }
    }

    const isSuccessful =
        status === "success" ||
        status === "successful" ||
        status === "paid" ||
        status === "completed";

    const statusText =
        isSuccessful
            ? "Paid"
            : (
                status.charAt(0).toUpperCase() +
                status.slice(1)
            );

    return `
        <div class="payment-history-item">

            <div class="payment-history-icon ${isSuccessful
            ? "payment-success"
            : "payment-other"
        }">
                ${isSuccessful
            ? "✓"
            : "•"
        }
            </div>

            <div class="payment-history-main">

                <div class="payment-history-title-row">

                    <div>

                        <strong>
                            ${escapeHtml(plan)}
                            subscription
                        </strong>

                        <span>
                            ${escapeHtml(
            formattedDate
        )}
                        </span>

                    </div>

                    <div class="payment-history-amount">

                        ₹${Number(
            amount
        ).toLocaleString(
            "en-IN"
        )}

                    </div>

                </div>

                <div class="payment-history-meta">

                    <span>
                        ${escapeHtml(
            statusText
        )}
                    </span>

                    <span>
                        Order:
                        ${escapeHtml(
            orderId
        )}
                    </span>

                    <span>
                        Payment:
                        ${escapeHtml(
            paymentId
        )}
                    </span>

                </div>

            </div>

        </div>
    `;
}
// =========================================================
// SUBSCRIPTION REMINDER NOTIFICATIONS
// =========================================================

function checkSubscriptionReminderNotifications({
    subscriptionExpiresAt,
    daysRemaining,
    userKey = "anonymous"
}) {

    if (
        !subscriptionExpiresAt ||
        daysRemaining === null
    ) {
        return;
    }
    const expiryKey =
        String(
            subscriptionExpiresAt
        );
    const notificationPrefix =
        `documind_subscription_${userKey}_${expiryKey}`;
    // -----------------------------------------------------
    // 7 DAYS BEFORE EXPIRY
    // -----------------------------------------------------

    if (
        daysRemaining <= 7 &&
        daysRemaining > 1
    ) {

        const storageKey =
            `${notificationPrefix}_reminder7`;

        if (
            localStorage.getItem(
                storageKey
            ) !== "sent"
        ) {

            if (
                addNotification({

                    type:
                        "reminder7",

                    title:
                        "Premium subscription reminder",

                    message:
                        `Your Premium subscription expires in ${daysRemaining} days.`,

                    icon:
                        "fa-calendar-days"

                })
            ) {

                localStorage.setItem(
                    storageKey,
                    "sent"
                );

            }

        }

    }


    // -----------------------------------------------------
    // 1 DAY BEFORE EXPIRY
    // -----------------------------------------------------

    if (
        daysRemaining <= 1 &&
        daysRemaining > 0
    ) {

        const storageKey =
            `${notificationPrefix}_reminder1`;

        if (
            localStorage.getItem(
                storageKey
            ) !== "sent"
        ) {

            if (
                addNotification({

                    type:
                        "reminder1",

                    title:
                        "Premium subscription expires tomorrow",

                    message:
                        "Your Premium subscription expires tomorrow.",

                    icon:
                        "fa-clock"

                })
            ) {

                localStorage.setItem(
                    storageKey,
                    "sent"
                );

            }

        }

    }


    // -----------------------------------------------------
    // EXPIRATION
    // -----------------------------------------------------

    if (
        daysRemaining <= 0
    ) {

        const storageKey =
            `${notificationPrefix}_expiry`;

        if (
            localStorage.getItem(
                storageKey
            ) !== "sent"
        ) {

            if (
                addNotification({

                    type:
                        "expiry",

                    title:
                        "Premium subscription expired",

                    message:
                        "Your Premium subscription has reached its expiration date.",

                    icon:
                        "fa-circle-exclamation"

                })
            ) {

                localStorage.setItem(
                    storageKey,
                    "sent"
                );

            }

        }

    }

}
            // =========================================================
            // SETTINGS PAGE
            // =========================================================

            async function showSettingsPage() {

                if (!requireAuthentication()) {
                    return;
                }

                setActiveNav("settings");
                hideDashboardSections();

                // -----------------------------------------------------
                // LOAD CURRENT USER DATA
                // -----------------------------------------------------

                try {
                    await loadCurrentUser();
                }
                catch (error) {
                    console.error(
                        "Unable to load user for settings:",
                        error
                    );
                }

                const user = currentUser || {};

                const plan =
                    String(
                        user.plan || "free"
                    ).toLowerCase();

                const isPremium =
                    plan === "premium";

                const subscriptionStatus =
                    user.subscription_status ||
                    "active";
                // =========================================================
                // PREMIUM SUBSCRIPTION EXPIRY
                // =========================================================

                const subscriptionExpiresAt =
                    user.subscription_expires_at || null;
                console.log("Subscription started:", user.subscription_started_at);
                console.log("Subscription expires:", user.subscription_expires_at);
                console.log("Current date:", new Date().toISOString());

                const subscriptionStartedAt =
                    user.subscription_started_at || null;


                let daysRemaining = null;
                let subscriptionExpiryText = "Not applicable";
                let subscriptionStartText = "Not applicable";
                let subscriptionExpiryState = "none";

                if (subscriptionStartedAt) {
                    const startDate =
                        new Date(subscriptionStartedAt);

                    if (!Number.isNaN(startDate.getTime())) {
                        subscriptionStartText =
                            startDate.toLocaleDateString(
                                "en-IN",
                                {
                                    day: "2-digit",
                                    month: "short",
                                    year: "numeric"
                                }
                            );
                    }
                }

                if (subscriptionExpiresAt) {

                    const expiryDate =
                        new Date(subscriptionExpiresAt);

                    if (!Number.isNaN(expiryDate.getTime())) {

                        subscriptionExpiryText =
                            expiryDate.toLocaleDateString(
                                "en-IN",
                                {
                                    day: "2-digit",
                                    month: "short",
                                    year: "numeric"
                                }
                            );

                        const now =
                            new Date();

                        daysRemaining =
                            Math.ceil(
                                (
                                    expiryDate.getTime() -
                                    now.getTime()
                                ) /
                                (1000 * 60 * 60 * 24)
                            );

                        if (daysRemaining <= 0) {
                            subscriptionExpiryState =
                                "expired";
                        }
                        else if (daysRemaining <= 3) {
                            subscriptionExpiryState =
                                "critical";
                        }
                        else if (daysRemaining <= 7) {
                            subscriptionExpiryState =
                                "warning";
                        }
                        else {
                            subscriptionExpiryState =
                                "active";
                        }


                         // =========================================================
                        // SUBSCRIPTION EXPIRY NOTIFICATIONS
                        // =========================================================

                        if (
                            subscriptionExpiresAt &&
                            daysRemaining !== null
                        ) {

                           checkSubscriptionReminderNotifications({

                                subscriptionExpiresAt,

                                daysRemaining,

                                userKey:
                                    user.email ||
                                    "anonymous"

                            });

                        }
                    }
                } 

                    const questionsUsed =
                        Number(
                            user.questions_used || 0
                        );

                        const questionLimit =
                            Number(
                                user.question_limit ||
                                (isPremium ? 500 : 20)
                            );

                        const documentsUsed =
                            Number(
                                user.documents_used ??
                                documents.length ??
                                0
                            );

                        const documentLimit =
                            Number(
                                user.document_limit ||
                                (isPremium ? 50 : 3)
                            );

                        const maxFileSize =
                            Number(
                                user.max_file_size_mb ||
                                (isPremium ? 25 : 5)
                            );
                        // -----------------------------------------------------
                        // CALCULATE USAGE
                        // -----------------------------------------------------

                        const questionPercentage =
                            questionLimit > 0
                                ? Math.min(
                                    100,
                                    Math.round(
                                        (questionsUsed / questionLimit) * 100
                                    )
                                )
                                : 0;

                        const documentPercentage =
                            documentLimit > 0
                                ? Math.min(
                                    100,
                                    Math.round(
                                        (documentsUsed / documentLimit) * 100
                                    )
                                )
                                : 0;


                        // -----------------------------------------------------
                        // BILLING TEXT
                        // -----------------------------------------------------

                        const planName =
                            isPremium
                                ? "Premium"
                                : "Free";

                        const planPrice =
                            isPremium
                                ? "₹499"
                                : "₹0";

                        const planDescription =
                            isPremium
                                ? "Everything you need for advanced document intelligence."
                                : "Essential document intelligence for getting started.";


                        // -----------------------------------------------------
                        // SETTINGS PAGE
                        // -----------------------------------------------------

                        showDynamicPage(`

        <div class="settings-page">

            <!-- =================================================
                 SETTINGS SIDEBAR
            ================================================== -->

            <aside class="settings-sidebar">

                <div class="settings-sidebar-header">

                    <h2>
                        Settings
                    </h2>

                    <button
                        type="button"
                        class="settings-close-button"
                        id="settingsCloseButton"
                        aria-label="Close settings"
                    >
                        ×
                    </button>

                </div>


                <!-- SEARCH -->

                <div class="settings-search">

                    <span class="settings-search-icon">
                        ⌕
                    </span>

                    <input
                        type="text"
                        id="settingsSearch"
                        placeholder="Search settings..."
                        autocomplete="off"
                    >

                </div>


                <!-- SETTINGS NAVIGATION -->

                <nav
                    class="settings-nav"
                    id="settingsNav"
                >

                    <button
                        type="button"
                        class="settings-nav-item active"
                        data-settings-section="general"
                    >

                        <span class="settings-nav-icon">
                        <i class="fa-regular fa-user"></i>
                    </span>
                        <span>
                            General
                        </span>

                    </button>


                    <button
                        type="button"
                        class="settings-nav-item"
                        data-settings-section="billing"
                    >

                        <span class="settings-nav-icon">
                        <i class="fa-regular fa-credit-card"></i>
                        </span>

                        <span>
                            Billing
                        </span>

                    </button>


                    <button
                        type="button"
                        class="settings-nav-item"
                        data-settings-section="usage"
                    >

                        <span class="settings-nav-icon">
                        <i class="fa-solid fa-chart-column"></i>
                    </span>

                        <span>
                            Usage
                        </span>

                    </button>


                    <button
                        type="button"
                        class="settings-nav-item"
                        data-settings-section="notifications"
                    >

                        <span class="settings-nav-icon">
                        <i class="fa-regular fa-bell"></i>
                    </span>

                        <span>
                            Notifications
                        </span>

                    </button>


                    <button
                        type="button"
                        class="settings-nav-item"
                        data-settings-section="personalization"
                    >

                       <span class="settings-nav-icon">
                        <i class="fa-solid fa-palette"></i>
                    </span>

                        <span>
                            Personalization
                        </span>

                    </button>


                    <button
                        type="button"
                        class="settings-nav-item"
                        data-settings-section="ai"
                    >

                        <span class="settings-nav-icon">
                        <i class="fa-solid fa-wand-magic-sparkles"></i>
                    </span>
                        <span>
                            AI Preferences
                        </span>

                    </button>


                    <button
                        type="button"
                        class="settings-nav-item"
                        data-settings-section="security"
                    >

                       <span class="settings-nav-icon">
                      <i class="fa-solid fa-shield-halved"></i>
                    </span>

                        <span>
                            Security
                        </span>
                    </button>
                </nav>
            </aside>
            <!-- =================================================
                 SETTINGS CONTENT
            ================================================== -->

            <div class="settings-content">
                <!-- =================================================
                     GENERAL
                ================================================== -->
                <section
                    class="settings-section"
                    data-settings-content="general"
                >
                    <div class="settings-page-header">

                        <span class="section-label">
                            ACCOUNT
                        </span>

                        <h1>
                            General
                        </h1>

                        <p>
                            Manage your DocuMind AI account information
                            and workspace preferences.
                        </p>

                    </div>


                    <!-- PROFILE -->

                    <div class="settings-card">

                        <div class="settings-card-header">

                            <div>

                                <h2>
                                    Profile
                                </h2>

                                <p>
                                    Your account information
                                </p>

                            </div>

                            <span class="settings-badge">
                                ${isPremium ? "Premium" : "Free"}
                            </span>

                        </div>


                        <div class="settings-details">


                            <div class="settings-detail-row">

                                <div>

                                    <strong>
                                        Email
                                    </strong>

                                    <p>
                                        Your registered account email
                                    </p>

                                </div>

                                <strong id="settingsEmail">
                                    ${escapeHtml(
                            user.email ||
                            "Loading..."
                        )}
                                </strong>

                            </div>


                            <div class="settings-detail-row">

                                <div>

                                    <strong>
                                        Plan
                                    </strong>

                                    <p>
                                        Current DocuMind AI subscription
                                    </p>

                                </div>

                                <strong>
                                    ${planName}
                                </strong>

                            </div>


                            <div class="settings-detail-row">

                                <div>

                                    <strong>
                                        Account Status
                                    </strong>

                                    <p>
                                        Your account is currently active
                                    </p>

                                </div>

                                <span class="settings-status">

                                    <span class="settings-status-dot"></span>

                                    ${escapeHtml(
                            subscriptionStatus
                        )}

                                </span>

                            </div>


                        </div>

                    </div>


                    <!-- ACCOUNT ACTION -->

                    <div class="settings-card">

                        <div class="settings-card-header">

                            <div>

                                <h2>
                                    Account Actions
                                </h2>

                                <p>
                                    Manage your DocuMind AI session.
                                </p>

                            </div>

                        </div>


                        <div class="settings-actions">

                            <button
                                type="button"
                                id="settingsLogout"
                                class="settings-danger-button"
                            >
                                Logout
                            </button>

                        </div>

                    </div>

                </section>


                <!-- =================================================
                    BILLING
                ================================================== -->

                <section
                    class="settings-section"
                    data-settings-content="billing"
                    hidden
                >

                    <div class="settings-page-header">

                        <span class="section-label">
                            SUBSCRIPTION
                        </span>

                        <h1>
                            Billing
                        </h1>

                        <p>
                            Manage your DocuMind AI plan,
                            subscription, and payment history.
                        </p>

                    </div>


                    <!-- =================================================
                        CURRENT PLAN
                    ================================================== -->

                    <div
                        class="
                            settings-card
                            billing-plan-card
                            ${isPremium ? "premium-billing-card" : ""}
                        "
                    >

                        <div class="billing-plan-header">

                            <div>

                                <div class="billing-current-plan-line">

                                    <span class="billing-plan-label">
                                        CURRENT PLAN
                                    </span>

                                    <span
                                        class="
                                            billing-active-badge
                                            ${isPremium ? "premium" : "free"}
                                        "
                                    >
                                        <span></span>

                                        ${isPremium
                                ? "Premium Active"
                                : "Free Plan"
                            }

                                    </span>

                                </div>


                                <h2>
                                    ${planName}
                                </h2>

                                <p>
                                    ${isPremium
                                ? "Advanced document intelligence for larger workloads."
                                : "Essential document intelligence for getting started."
                            }
                                </p>

                            </div>


                            <div class="billing-plan-price">

                                <strong>
                                    ${planPrice}
                                </strong>

                                <span>
                                    / month
                                </span>

                            </div>

                        </div>


                        <div class="billing-plan-divider"></div>


                        <!-- USAGE SUMMARY -->

                        <div class="billing-usage-grid">

                            <div class="billing-usage-item">

                                <span>
                                    Documents
                                </span>

                                <strong>
                                    ${documentsUsed} / ${documentLimit}
                                </strong>

                            </div>


                            <div class="billing-usage-item">

                                <span>
                                    Questions
                                </span>

                                <strong>
                                    ${questionsUsed} / ${questionLimit}
                                </strong>

                            </div>


                            <div class="billing-usage-item">

                                <span>
                                    PDF size
                                </span>

                                <strong>
                                    ${maxFileSize} MB
                                </strong>

                            </div>

                        </div>


                        ${isPremium

                                ?

                                `
                            <div class="billing-premium-active">

                                <div class="billing-premium-active-icon">
                                    ✓
                                </div>

                                <div>

                                    <strong>
                                        Premium subscription active
                                    </strong>

                                    <span>
                                        Your account has access to all Premium limits.
                                    </span>

                                </div>

                            </div>
                            `

                                :

                                ""
                            }

                    </div>


                    <!-- =================================================
                        PREMIUM PLAN
                    ================================================== -->

                    ${!isPremium

                                ?

                                `
                        <div class="settings-card premium-billing-card billing-upgrade-card">

                            <div class="billing-upgrade-top">

                                <div>

                                    <span class="billing-plan-label">
                                        DOCUMIND PREMIUM
                                    </span>

                                    <h2>
                                        Unlock more from your documents
                                    </h2>

                                    <p>
                                        Get more capacity and a more powerful
                                        AI document workspace.
                                    </p>

                                </div>


                                <div class="billing-upgrade-price">

                                    <strong>
                                        ₹499
                                    </strong>

                                    <span>
                                        / month
                                    </span>

                                </div>

                            </div>


                            <div class="premium-feature-list">

                                <div class="premium-feature">
                                    <span>✓</span>
                                    <strong>
                                        50 documents
                                    </strong>
                                </div>

                                <div class="premium-feature">
                                    <span>✓</span>
                                    <strong>
                                        500 AI questions
                                    </strong>
                                </div>

                                <div class="premium-feature">
                                    <span>✓</span>
                                    <strong>
                                        25 MB PDF uploads
                                    </strong>
                                </div>

                                <div class="premium-feature">
                                    <span>✓</span>
                                    <strong>
                                        Advanced document intelligence
                                    </strong>
                                </div>

                            </div>


                            <div class="billing-upgrade-footer">

                                <div class="billing-demo-caption">

                                    <span>
                                        ✦
                                    </span>

                                    <div>

                                        <strong>
                                            Demo payment
                                        </strong>

                                        <p>
                                            No real money will be charged.
                                        </p>

                                    </div>

                                </div>


                                <div class="settings-actions">

                                    <button
                                        type="button"
                                        id="upgradePremiumButton"
                                        class="primary-button billing-upgrade-button"
                                    >
                                        Upgrade to Premium
                                    </button>

                                </div>

                            </div>

                        </div>
                        `

                                :

                                ""
                            }


                    <!-- =================================================
                        PAYMENT HISTORY
                    ================================================== -->

                    <div class="settings-card billing-history-card">

                        <div class="settings-card-header">

                            <div>

                                <span class="billing-plan-label">
                                    TRANSACTIONS
                                </span>

                                <h2>
                                    Payment History
                                </h2>

                                <p>
                                    View your completed DocuMind AI subscription payments.
                                </p>

                            </div>

                        </div>


                        <div
                            id="paymentHistoryContainer"
                            class="billing-history-container"
                        >
                            Loading payment history...
                        </div>

                    </div>


                    <!-- =================================================
                        BILLING NOTE
                    ================================================== -->

                    <div class="billing-security-note">

                        <div class="billing-security-icon">
                            ✓
                        </div>

                        <div>

                            <strong>
                                Demo billing environment
                            </strong>

                            <p>
                                Payments shown here are simulated for
                                demonstration purposes. No real payment
                                method or financial information is collected.
                            </p>

                        </div>

                    </div>

                </section>

                <!-- =================================================
                     USAGE
                ================================================== -->

                <section
                    class="settings-section"
                    data-settings-content="usage"
                    hidden
                >

                    <div class="settings-page-header">

                        <span class="section-label">
                            USAGE
                        </span>

                        <h1>
                            Usage
                        </h1>

                        <p>
                            Monitor your current DocuMind AI resource usage.
                        </p>

                    </div>


                    <!-- QUESTIONS -->

                    <div class="settings-card">

                        <div class="usage-card-header">

                            <div>

                                <h2>
                                    Questions
                                </h2>

                                <p>
                                    Questions used on your current plan.
                                </p>

                            </div>

                            <strong>
                                ${questionsUsed} / ${questionLimit}
                            </strong>

                        </div>


                        <div class="usage-progress">

                            <div
                                class="usage-progress-bar"
                                style="width: ${questionPercentage}%"
                            ></div>

                        </div>

                    </div>


                    <!-- DOCUMENTS -->

                    <div class="settings-card">

                        <div class="usage-card-header">

                            <div>

                                <h2>
                                    Documents
                                </h2>

                                <p>
                                    Documents currently stored in your workspace.
                                </p>

                            </div>

                            <strong>
                                ${documentsUsed} / ${documentLimit}
                            </strong>

                        </div>


                        <div class="usage-progress">

                            <div
                                class="usage-progress-bar"
                                style="width: ${documentPercentage}%"
                            ></div>

                        </div>

                    </div>


                    <!-- FILE SIZE -->

                    <div class="settings-card">

                        <div class="settings-card-header">

                            <div>

                                <h2>
                                    Maximum PDF Size
                                </h2>

                                <p>
                                    Maximum size allowed for a single PDF.
                                </p>

                            </div>

                            <span class="settings-badge">
                                ${maxFileSize} MB
                            </span>

                        </div>

                    </div>

                </section>


                <!-- =================================================
                        NOTIFICATIONS
                    ================================================== -->

                    <section
                        class="settings-section"
                        data-settings-content="notifications"
                        hidden
                    >

                        <div class="settings-page-header">

                            <span class="section-label">
                                PREFERENCES
                            </span>

                            <h1>
                                Notifications
                            </h1>

                            <p>
                                Control how DocuMind AI keeps you informed.
                            </p>

                        </div>


                        <!-- NOTIFICATION PREFERENCES -->

                        <div class="settings-card">

                            <div class="settings-card-header">

                                <div>

                                    <h2>
                                        Notification preferences
                                    </h2>

                                    <p>
                                        Choose which DocuMind AI activities
                                        should notify you.
                                    </p>

                                </div>

                                <span class="settings-badge">
                                    Preferences
                                </span>

                            </div>


                            <div class="settings-option-list">


                                <!-- DOCUMENT PROCESSING -->

                                <div class="settings-option">

                                    <div>

                                        <strong>
                                            Document processing
                                        </strong>

                                        <p>
                                            Notify me when a PDF finishes
                                            processing and becomes ready.
                                        </p>

                                    </div>

                                    <label
                                        class="settings-toggle"
                                        title="Document processing notifications"
                                    >

                                        <input
                                            type="checkbox"
                                            id="notificationDocumentProcessing"
                                        >

                                        <span></span>

                                    </label>

                                </div>


                                <!-- AI RESPONSES -->

                                <div class="settings-option">

                                    <div>

                                        <strong>
                                            AI responses
                                        </strong>

                                        <p>
                                            Show notifications when an AI
                                            response has completed.
                                        </p>

                                    </div>

                                    <label
                                        class="settings-toggle"
                                        title="AI response notifications"
                                    >

                                        <input
                                            type="checkbox"
                                            id="notificationAIResponses"
                                        >

                                        <span></span>

                                    </label>

                                </div>


                                <!-- USAGE ALERTS -->

                                <div class="settings-option">

                                    <div>

                                        <strong>
                                            Usage alerts
                                        </strong>

                                        <p>
                                            Warn me when I am approaching
                                            my plan limits.
                                        </p>

                                    </div>

                                    <label
                                        class="settings-toggle"
                                        title="Usage alerts"
                                    >

                                        <input
                                            type="checkbox"
                                            id="notificationUsageAlerts"
                                        >

                                        <span></span>

                                    </label>

                                </div>


                                <!-- SUBSCRIPTION -->

                                <div class="settings-option">

                                    <div>

                                        <strong>
                                            Subscription reminders
                                        </strong>

                                        <p>
                                            Receive reminders about Premium
                                            subscription status and expiry.
                                        </p>

                                    </div>

                                    <label
                                        class="settings-toggle"
                                        title="Subscription reminders"
                                    >

                                        <input
                                            type="checkbox"
                                            id="notificationSubscription"
                                        >

                                        <span></span>

                                    </label>

                                </div>


                                <!-- PRODUCT UPDATES -->

                                <div class="settings-option">

                                    <div>

                                        <strong>
                                            Product updates
                                        </strong>

                                        <p>
                                            Receive important DocuMind AI
                                            feature and product updates.
                                        </p>

                                    </div>

                                    <label
                                        class="settings-toggle"
                                        title="Product updates"
                                    >

                                        <input
                                            type="checkbox"
                                            id="notificationProductUpdates"
                                        >

                                        <span></span>

                                    </label>

                                </div>


                            </div>

                        </div>


                        <!-- SUBSCRIPTION REMINDERS -->

                        <div class="settings-card">

                            <div class="settings-card-header">

                                <div>

                                    <h2>
                                        Subscription reminders
                                    </h2>

                                    <p>
                                        Choose when DocuMind AI should remind
                                        you about your Premium subscription.
                                    </p>

                                </div>

                            </div>


                            <div class="settings-option-list">


                                <div class="settings-option">

                                    <div>

                                        <strong>
                                            7 days before expiry
                                        </strong>

                                        <p>
                                            Receive an early reminder before
                                            Premium access expires.
                                        </p>

                                    </div>

                                    <label
                                        class="settings-toggle"
                                    >

                                        <input
                                            type="checkbox"
                                            id="notificationExpiry7Days"
                                        >

                                        <span></span>

                                    </label>

                                </div>


                                <div class="settings-option">

                                    <div>

                                        <strong>
                                            1 day before expiry
                                        </strong>

                                        <p>
                                            Receive a reminder one day before
                                            your Premium access ends.
                                        </p>

                                    </div>

                                    <label
                                        class="settings-toggle"
                                    >

                                        <input
                                            type="checkbox"
                                            id="notificationExpiry1Day"
                                        >

                                        <span></span>

                                    </label>

                                </div>


                                <div class="settings-option">

                                    <div>

                                        <strong>
                                            On expiration
                                        </strong>

                                        <p>
                                            Notify me when Premium access
                                            reaches its expiration date.
                                        </p>

                                    </div>

                                    <label
                                        class="settings-toggle"
                                    >

                                        <input
                                            type="checkbox"
                                            id="notificationExpiry"
                                        >

                                        <span></span>

                                    </label>

                                </div>


                            </div>

                        </div>

                    <!-- PHASE 8 - NOTIFICATION SAVE STATUS -->
                    <div class="settings-save-status-card">
                        <span
                            class="settings-save-status-dot"
                            aria-hidden="true"
                        ></span>

                        <div>
                            <strong>Preference status</strong>

                            <p id="notificationSaveStatus">
                                Your notification preferences are saved automatically on this device.
                            </p>
                        </div>

                        <span
                            id="notificationSaveStatusText"
                            class="settings-save-status-text"
                        >
                            Saved automatically
                        </span>
                    </div>

                </section>
                <!-- =================================================
                     PERSONALIZATION
                ================================================== -->

                <section
                    class="settings-section"
                    data-settings-content="personalization"
                    hidden
                >

                    <div class="settings-page-header">

                        <span class="section-label">
                            WORKSPACE
                        </span>

                        <h1>
                            Personalization
                        </h1>

                        <p>
                            Customize how your DocuMind AI workspace
                            looks and behaves.
                        </p>

                    </div>


                    <!-- INTERFACE -->

                    <div class="settings-card">

                        <div class="settings-card-header">

                            <div>

                                <h2>
                                    Interface
                                </h2>

                                <p>
                                    Adjust the workspace experience
                                    to match your workflow.
                                </p>

                            </div>

                            <span class="settings-badge">
                                Workspace
                            </span>

                        </div>


                        <div class="settings-option-list">


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Compact interface
                                    </strong>

                                    <p>
                                        Use a denser layout for documents,
                                        conversations and workspace content.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="personalizationCompact"
                                    >

                                    <span></span>

                                </label>

                            </div>


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Show document details
                                    </strong>

                                    <p>
                                        Display pages and chunks in
                                        document cards.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="personalizationDocumentDetails"
                                    >

                                    <span></span>

                                </label>

                            </div>


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Remember last document
                                    </strong>

                                    <p>
                                        Automatically reopen the last
                                        document used in your workspace.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="personalizationRememberDocument"
                                    >

                                    <span></span>

                                </label>

                            </div>


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Show workspace information
                                    </strong>

                                    <p>
                                        Display helpful document and
                                        processing information.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="personalizationWorkspaceInfo"
                                    >

                                    <span></span>

                                </label>

                            </div>


                        </div>

                    </div>


                    <!-- DOCUMENT WORKSPACE -->

                    <div class="settings-card">

                        <div class="settings-card-header">

                            <div>

                                <h2>
                                    Document workspace
                                </h2>

                                <p>
                                    Control how document information
                                    is presented.
                                </p>

                            </div>

                        </div>


                        <div class="settings-option-list">


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Remember current document
                                    </strong>

                                    <p>
                                        Keep the current document selected
                                        between sessions.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="personalizationRememberCurrent"
                                    >

                                    <span></span>

                                </label>

                            </div>


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Smooth navigation
                                    </strong>

                                    <p>
                                        Use smooth scrolling when moving
                                        between workspace sections.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="personalizationSmoothNavigation"
                                    >

                                    <span></span>

                                </label>

                            </div>


                        </div>

                    </div>

                    <!-- PHASE 8 - PERSONALIZATION SAVE STATUS -->
                    <div class="settings-save-status-card">
                        <span
                            class="settings-save-status-dot"
                            aria-hidden="true"
                        ></span>

                        <div>
                            <strong>Preference status</strong>

                            <p id="personalizationSaveStatus">
                                Your personalization preferences are saved automatically on this device.
                            </p>
                        </div>

                        <span
                            id="personalizationSaveStatusText"
                            class="settings-save-status-text"
                        >
                            Saved automatically
                        </span>
                    </div>

                </section>


                <!-- =================================================
                     AI PREFERENCES
                ================================================== -->

                <section
                    class="settings-section"
                    data-settings-content="ai"
                    hidden
                >

                    <div class="settings-page-header">

                        <span class="section-label">
                            AI
                        </span>

                        <h1>
                            AI Preferences
                        </h1>

                        <p>
                            Configure how DocuMind AI responds to
                            questions about your documents.
                        </p>

                    </div>


                    <!-- RESPONSE STYLE -->

                    <div class="settings-card">

                        <div class="settings-card-header">

                            <div>

                                <h2>
                                    Response style
                                </h2>

                                <p>
                                    Choose how answers should be presented.
                                </p>

                            </div>

                            <span class="settings-badge">
                                AI behavior
                            </span>

                        </div>


                        <div class="settings-option-list">


                            <!-- CONCISE -->

                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Concise responses
                                    </strong>

                                    <p>
                                        Prefer shorter answers focused on
                                        the most important information.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="radio"
                                        name="aiResponseStyle"
                                        id="aiResponseConcise"
                                        value="concise"
                                    >

                                    <span></span>

                                </label>

                            </div>


                            <!-- BALANCED -->

                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Balanced responses
                                    </strong>

                                    <p>
                                        Provide useful explanations while
                                        keeping answers reasonably concise.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="radio"
                                        name="aiResponseStyle"
                                        id="aiResponseBalanced"
                                        value="balanced"
                                    >

                                    <span></span>

                                </label>

                            </div>


                            <!-- DETAILED -->

                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Detailed responses
                                    </strong>

                                    <p>
                                        Provide more explanation, calculations
                                        and supporting document context.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="radio"
                                        name="aiResponseStyle"
                                        id="aiResponseDetailed"
                                        value="detailed"
                                    >

                                    <span></span>

                                </label>

                            </div>


                        </div>

                    </div>


                    <!-- DOCUMENT INTELLIGENCE -->

                    <div class="settings-card">

                        <div class="settings-card-header">

                            <div>

                                <h2>
                                    Document intelligence
                                </h2>

                                <p>
                                    Control how DocuMind AI uses your
                                    uploaded documents.
                                </p>

                            </div>

                        </div>


                        <div class="settings-option-list">


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Prioritize document context
                                    </strong>

                                    <p>
                                        Always prioritize information
                                        retrieved from your uploaded documents.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="aiPrioritizeContext"
                                    >

                                    <span></span>

                                </label>

                            </div>


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Show sources
                                    </strong>

                                    <p>
                                        Display relevant document pages
                                        with AI answers.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="aiShowSources"
                                    >

                                    <span></span>

                                </label>

                            </div>


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Save chat history
                                    </strong>

                                    <p>
                                        Keep document conversations available
                                        in Chat History.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="aiSaveHistory"
                                    >

                                    <span></span>

                                </label>

                            </div>


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Explain calculations
                                    </strong>

                                    <p>
                                        Provide step-by-step explanations
                                        when answering mathematical questions.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="aiExplainCalculations"
                                    >

                                    <span></span>

                                </label>

                            </div>


                        </div>

                    </div>


                    <!-- MATHEMATICAL CONTENT -->

                    <div class="settings-card">

                        <div class="settings-card-header">

                            <div>

                                <h2>
                                    Mathematical content
                                </h2>

                                <p>
                                    Improve readability when working with
                                    formulas and calculations.
                                </p>

                            </div>

                        </div>


                        <div class="settings-option-list">


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Preserve mathematical notation
                                    </strong>

                                    <p>
                                        Keep formulas, equations and symbols
                                        formatted accurately.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="aiMathNotation"
                                    >

                                    <span></span>

                                </label>

                            </div>


                            <div class="settings-option">

                                <div>

                                    <strong>
                                        Step-by-step calculations
                                    </strong>

                                    <p>
                                        Show intermediate calculation steps
                                        when useful.
                                    </p>

                                </div>

                                <label class="settings-toggle">

                                    <input
                                        type="checkbox"
                                        id="aiStepCalculations"
                                    >

                                    <span></span>

                                </label>

                            </div>


                        </div>

                    </div>
                    <!-- PHASE 8 - AI PREFERENCES SAVE STATUS -->
                    <div class="settings-save-status-card">
                        <span
                            class="settings-save-status-dot"
                            aria-hidden="true"
                        ></span>

                        <div>
                            <strong>Preference status</strong>

                            <p id="aiSaveStatus">
                                Your AI preferences are saved automatically on this device.
                            </p>
                        </div>

                        <span
                            id="aiSaveStatusText"
                            class="settings-save-status-text"
                        >
                            Saved automatically
                        </span>
                    </div>

                </section>


                <!-- =================================================
                    SECURITY
                ================================================= -->

                <section
                    class="settings-section"
                    data-settings-content="security"
                    hidden
                >

                    <div class="settings-page-header">

                        <span class="section-label">
                            ACCOUNT
                        </span>

                        <h1>
                            Security
                        </h1>

                        <p>
                            Review your account security information.
                        </p>

                    </div>


                    <div class="settings-card">

                        <div class="settings-detail-row">

                            <div>

                                <strong>
                                    Authentication
                                </strong>

                                <p>
                                    Your account uses secure JWT authentication.
                                </p>

                            </div>

                            <span class="settings-status">

                                <span class="settings-status-dot"></span>

                                Protected

                            </span>

                        </div>


                        <div class="settings-detail-row">

                            <div>

                                <strong>
                                    Session
                                </strong>

                                <p>
                                    Your current session is authenticated.
                                </p>

                            </div>

                            <span class="settings-badge">
                                Active
                            </span>

                        </div>

                    </div>
                        </div>

                    </div>

                </section>

            </div>

        </div>

    `);
                        
                        // =========================================================
                        // PHASE 8 - RENDER PROFESSIONAL SETTINGS
                        // =========================================================

                        renderPhase8SettingsSections();
                        initializePhase8SettingsControls();

                        // =========================================================
                        // SETTINGS PAGE
                        // =========================================================

                        const settingsPage =
                            document.querySelector(".settings-page");

                        // =========================================================
                        // SHOW DEFAULT SETTINGS SECTION
                        // =========================================================

                        if (settingsPage) {
                            const defaultSection = "general";

                            const settingsSections =
                                settingsPage.querySelectorAll(
                                    "[data-settings-content]"
                                );

                            settingsSections.forEach(section => {
                                section.hidden =
                                    section.dataset.settingsContent !==
                                    defaultSection;
                            });

                            const settingsNavItems =
                                settingsPage.querySelectorAll(
                                    ".settings-nav-item"
                                );

                            settingsNavItems.forEach(item => {
                                item.classList.toggle(
                                    "active",
                                    item.dataset.settingsSection ===
                                    defaultSection
                                );
                            });

                            // =====================================================
                            // SETTINGS NAVIGATION
                            // =====================================================

                            settingsNavItems.forEach(item => {
                                item.addEventListener("click", () => {
                                    const section =
                                        item.dataset.settingsSection;

                                    settingsNavItems.forEach(navItem => {
                                        navItem.classList.toggle(
                                            "active",
                                            navItem === item
                                        );
                                    });

                                    settingsSections.forEach(content => {
                                        content.hidden =
                                            content.dataset.settingsContent !==
                                            section;
                                    });

                                    // BILLING
                                    if (section === "billing") {
                                        setTimeout(() => {
                                            loadPaymentHistory();
                                        }, 0);
                                    }
                                });
                            });
                        }

                        // =========================================================
                        // SETTINGS SEARCH
                        // =========================================================

                        const settingsSearch =
                            document.getElementById("settingsSearch");

                        if (settingsSearch && settingsPage) {
                            const searchNavItems =
                                settingsPage.querySelectorAll(
                                    ".settings-nav-item"
                                );

                            settingsSearch.addEventListener("input", () => {
                                const search =
                                    settingsSearch.value
                                        .trim()
                                        .toLowerCase();

                                searchNavItems.forEach(item => {
                                    const text =
                                        item.textContent
                                            .trim()
                                            .toLowerCase();

                                    item.hidden =
                                        search.length > 0 &&
                                        !text.includes(search);
                                });
                            });
                        }

                        // =========================================================
                        // LOGOUT BUTTON
                        // =========================================================

                        const settingsLogout =
                            document.getElementById("settingsLogout");

                        if (settingsLogout) {
                            settingsLogout.addEventListener("click", logout);
                        }
                        // =========================================================
                        // PROFESSIONAL DEMO PAYMENT MODAL
                        // =========================================================

                        function showDemoPaymentModal(amount) {

                            return new Promise(resolve => {

                                // -----------------------------------------------------
                                // REMOVE OLD MODAL IF ANY
                                // -----------------------------------------------------

                                const existingModal =
                                    document.getElementById(
                                        "demoPaymentModal"
                                    );

                                if (existingModal) {
                                    existingModal.remove();
                                }


                                // -----------------------------------------------------
                                // CREATE MODAL
                                // -----------------------------------------------------

                                const modal =
                                    document.createElement("div");

                                modal.id =
                                    "demoPaymentModal";

                                modal.className =
                                    "demo-payment-overlay";


                                // -----------------------------------------------------
                                // MODAL CONTENT
                                // -----------------------------------------------------

                                modal.innerHTML = `

            <div class="demo-payment-modal">

                <!-- HEADER -->

                <div class="demo-payment-header">

                    <div class="demo-payment-brand">

                        <div class="demo-payment-logo">
                            D
                        </div>

                        <div>

                            <div class="demo-payment-title">
                                DocuMind AI
                            </div>

                            <div class="demo-payment-subtitle">
                                Secure Demo Checkout
                            </div>

                        </div>

                    </div>


                    <button
                        type="button"
                        class="demo-payment-close"
                        id="demoPaymentClose"
                        aria-label="Close"
                    >
                        ×
                    </button>

                </div>


                <!-- BODY -->

                <div class="demo-payment-body">

                    <div class="demo-payment-icon">
                        ✓
                    </div>


                    <h2>
                        Upgrade to Premium
                    </h2>


                    <p class="demo-payment-description">
                        Unlock higher limits and enhanced
                        document intelligence with DocuMind AI Premium.
                    </p>


                    <!-- PLAN -->

                    <div class="demo-plan-card">

                        <div>

                            <div class="demo-plan-name">
                                Premium Plan
                            </div>

                            <div class="demo-plan-period">
                                Monthly subscription
                            </div>

                        </div>


                        <div class="demo-plan-price">

                            <span class="demo-price-symbol">
                                ₹
                            </span>

                            <span>
                                ${amount}
                            </span>

                            <small>
                                /month
                            </small>

                        </div>

                    </div>


                    <!-- FEATURES -->

                    <div class="demo-payment-features">

                        <div class="demo-feature">
                            <span>✓</span>
                            <span>
                                Up to 50 documents
                            </span>
                        </div>

                        <div class="demo-feature">
                            <span>✓</span>
                            <span>
                                Up to 500 AI questions
                            </span>
                        </div>

                        <div class="demo-feature">
                            <span>✓</span>
                            <span>
                                25 MB document uploads
                            </span>
                        </div>

                        <div class="demo-feature">
                            <span>✓</span>
                            <span>
                                Premium AI document assistance
                            </span>
                        </div>

                    </div>


                    <!-- DEMO NOTICE -->

                    <div class="demo-payment-notice">

                        <div class="demo-notice-icon">
                            ⓘ
                        </div>

                        <div>

                            <strong>
                                Demo Payment Mode
                            </strong>

                            <p>
                                This is a simulated payment for
                                demonstration purposes.
                                No real money will be charged.
                            </p>

                        </div>

                    </div>

                </div>


                <!-- FOOTER -->

                <div class="demo-payment-footer">

                    <button
                        type="button"
                        id="demoPaymentCancel"
                        class="demo-payment-cancel"
                    >
                        Cancel
                    </button>


                    <button
                        type="button"
                        id="demoPaymentPay"
                        class="demo-payment-pay"
                    >

                        <span>
                            Pay ₹${amount}
                        </span>

                        <span class="demo-payment-arrow">
                            →
                        </span>

                    </button>

                </div>

            </div>

        `;


                                // -----------------------------------------------------
                                // ADD TO PAGE
                                // -----------------------------------------------------

                                document.body.appendChild(modal);


                                // -----------------------------------------------------
                                // ELEMENTS
                                // -----------------------------------------------------

                                const closeButton =
                                    document.getElementById(
                                        "demoPaymentClose"
                                    );

                                const cancelButton =
                                    document.getElementById(
                                        "demoPaymentCancel"
                                    );

                                const payButton =
                                    document.getElementById(
                                        "demoPaymentPay"
                                    );


                                // -----------------------------------------------------
                                // CLOSE MODAL
                                // -----------------------------------------------------

                                function closeModal(result) {

                                    modal.classList.add(
                                        "closing"
                                    );

                                    setTimeout(() => {

                                        modal.remove();

                                        resolve(result);

                                    }, 180);
                                }


                                // -----------------------------------------------------
                                // CANCEL
                                // -----------------------------------------------------

                                closeButton.addEventListener(
                                    "click",
                                    () => {
                                        closeModal(false);
                                    }
                                );


                                cancelButton.addEventListener(
                                    "click",
                                    () => {
                                        closeModal(false);
                                    }
                                );


                                // -----------------------------------------------------
                                // PAY
                                // -----------------------------------------------------

                                payButton.addEventListener(
                                    "click",
                                    () => {

                                        payButton.disabled = true;

                                        payButton.innerHTML = `
                    <span>
                        Processing payment...
                    </span>

                    <span class="demo-payment-spinner">
                        ◌
                    </span>
                `;


                                        setTimeout(() => {

                                            closeModal(true);

                                        }, 650);

                                    }
                                );


                                // -----------------------------------------------------
                                // CLICK OUTSIDE MODAL
                                // -----------------------------------------------------

                                modal.addEventListener(
                                    "click",
                                    event => {

                                        if (
                                            event.target === modal
                                        ) {

                                            closeModal(false);

                                        }

                                    }
                                );


                                // -----------------------------------------------------
                                // ESC KEY
                                // -----------------------------------------------------

                                function escapeHandler(event) {

                                    if (
                                        event.key === "Escape"
                                    ) {

                                        document.removeEventListener(
                                            "keydown",
                                            escapeHandler
                                        );

                                        closeModal(false);

                                    }

                                }


                                document.addEventListener(
                                    "keydown",
                                    escapeHandler
                                );


                                // -----------------------------------------------------
                                // SHOW MODAL
                                // -----------------------------------------------------

                                requestAnimationFrame(() => {

                                    modal.classList.add(
                                        "visible"
                                    );

                                });

                            });

                        }

                        // =========================================================
                        // UPGRADE TO PREMIUM - DEMO PAYMENT
                        // =========================================================

                        const upgradePremiumButton =
                            document.getElementById(
                                "upgradePremiumButton"
                            );


                        if (upgradePremiumButton) {

                            upgradePremiumButton.addEventListener(
                                "click",
                                async () => {

                                    upgradePremiumButton.disabled = true;

                                    upgradePremiumButton.textContent =
                                        "Creating payment...";


                                    try {

                                        // =========================================
                                        // STEP 1: CREATE DEMO PAYMENT
                                        // =========================================

                                        const createResponse =
                                            await fetch(
                                                "/api/payment/create",
                                                {
                                                    method: "POST",

                                                    headers: {
                                                        ...authHeaders()
                                                    }
                                                }
                                            );


                                        const createData =
                                            await createResponse.json();


                                        // =========================================
                                        // AUTHENTICATION ERROR
                                        // =========================================

                                        if (createResponse.status === 401) {

                                            handleUnauthorized();

                                            return;

                                        }


                                        // =========================================
                                        // PAYMENT CREATION ERROR
                                        // =========================================

                                        if (!createResponse.ok) {

                                            throw new Error(
                                                createData.detail ||
                                                "Unable to create payment."
                                            );

                                        }


                                        console.log(
                                            "Demo payment created:",
                                            createData
                                        );


                                        // =========================================
                                        // STEP 2: SHOW PROFESSIONAL DEMO PAYMENT MODAL
                                        // =========================================

                                        const confirmPayment =
                                            await showDemoPaymentModal(
                                                createData.amount
                                            );


                                        // =========================================
                                        // PAYMENT CANCELLED
                                        // =========================================

                                        if (!confirmPayment) {

                                            upgradePremiumButton.disabled = false;

                                            upgradePremiumButton.textContent =
                                                "Upgrade to Premium";

                                            return;
                                        }


                                        // =========================================
                                        // PAYMENT CANCELLED
                                        // =========================================

                                        if (!confirmPayment) {

                                            upgradePremiumButton.disabled =
                                                false;

                                            upgradePremiumButton.textContent =
                                                "Upgrade to Premium";

                                            return;

                                        }


                                        // =========================================
                                        // STEP 3: VERIFY DEMO PAYMENT
                                        // =========================================

                                        upgradePremiumButton.textContent =
                                            "Verifying payment...";


                                        const verifyResponse =
                                            await fetch(
                                                "/api/payment/verify",
                                                {
                                                    method: "POST",

                                                    headers: {
                                                        "Content-Type":
                                                            "application/json",

                                                        ...authHeaders()
                                                    },

                                                    body: JSON.stringify({

                                                        order_id:
                                                            createData.order_id,

                                                        payment_id:
                                                            createData.payment_id

                                                    })
                                                }
                                            );


                                        const verifyData =
                                            await verifyResponse.json();


                                        // =========================================
                                        // AUTHENTICATION ERROR
                                        // =========================================

                                        if (verifyResponse.status === 401) {

                                            handleUnauthorized();

                                            return;

                                        }


                                        // =========================================
                                        // VERIFICATION ERROR
                                        // =========================================

                                        if (!verifyResponse.ok) {

                                            throw new Error(
                                                verifyData.detail ||
                                                "Payment verification failed."
                                            );

                                        }


                                        console.log(
                                            "Demo payment verified:",
                                            verifyData
                                        );


                                        // =========================================
                                        // STEP 4: RELOAD USER
                                        // =========================================

                                        await loadCurrentUser();


                                        // =========================================
                                        // STEP 5: SHOW SUCCESS
                                        // =========================================

                                        showSuccess(
                                            "🎉 Premium activated successfully!"
                                        );
                                        // =========================================
                                        // STEP 6: RE-RENDER SETTINGS
                                        // =========================================

                                        await showSettingsPage();


                                    }
                                    catch (error) {

                                        console.error(
                                            "Premium payment error:",
                                            error
                                        );


                                        showError(
                                            error.message ||
                                            "Unable to complete payment."
                                        );


                                        upgradePremiumButton.disabled =
                                            false;

                                        upgradePremiumButton.textContent =
                                            "Upgrade to Premium";

                                    }

                                }
                            );

                        }

                        // =========================================================
                        // CLOSE SETTINGS
                        // =========================================================

                        const settingsCloseButton =
                            document.getElementById(
                                "settingsCloseButton"
                            );


                        if (settingsCloseButton) {

                            settingsCloseButton.addEventListener(
                                "click",
                                showDashboardPage
                            );

                        }
                    }
                    // =========================================================
                    // CURRENT USER
                    // =========================================================
                    async function loadCurrentUser() {
                        try {
                            const response =
                                await fetch(
                                    "/api/auth/me",
                                    {
                                        method: "GET",

                                        headers: {
                                            ...authHeaders()
                                        }
                                    }
                                );

                            if (response.status === 401) {

                                handleUnauthorized();

                                return;
                            }

                            if (!response.ok) {
                                return;
                            }

                            currentUser =
                                await response.json();

                            updateUserInterface();

                        }
                        catch (error) {

                            console.error(
                                "User profile error:",
                                error
                            );

                        }
                    }
                    // =========================================================
                    // Greeting Function
                    // =========================================================
                    function updateDashboardGreeting() {

                        const greeting =
                            document.getElementById("dashboardGreeting");

                        if (!greeting || !currentUser) {
                            return;
                        }

                        const email =
                            currentUser.email || "";

                        const name =
                            email.includes("@")
                                ? email.split("@")[0]
                                : email;

                        greeting.innerHTML = `
        Welcome back, ${escapeHtml(capitalize(name))}
        <span class="wave">👋</span>
    `;
                    }


                    // =========================================================
                    // USER UI
                    // =========================================================
                    function updateUserInterface() {

                        if (!currentUser) {
                            return;
                        }

                        const email = currentUser.email || "";

                        const name = email.includes("@")
                            ? email.split("@")[0]
                            : email;

                        const displayName = capitalize(name);

                        // Topbar name
                        const userStrong =
                            document.querySelector(".user-info strong");

                        if (userStrong) {
                            userStrong.textContent = displayName;
                        }

                        // Topbar avatar
                        const userAvatar =
                            document.getElementById("userAvatar");

                        if (userAvatar) {
                            userAvatar.textContent =
                                displayName.charAt(0).toUpperCase();
                        }

                        // Settings email
                        const settingsEmail =
                            document.getElementById("settingsEmail");

                        if (settingsEmail) {
                            settingsEmail.textContent = email;
                        }
                        if (userAvatar) {
                            userAvatar.textContent =
                                displayName.charAt(0).toUpperCase();
                        }
                        // Profile dropdown
                        updateProfileMenu();
                        updateDashboardGreeting();
                    }
                    // =========================================================
                    // FILE SELECTION
                    // =========================================================
                    if (chooseFileButton && fileInput) {
                        chooseFileButton.onclick = function () {
                            if (!requireAuthentication()) return;
                            fileInput.click();
                        };
                    }
                    if (fileInput) {

                        fileInput.addEventListener(
                            "change",
                            handleFileSelection
                        );

                    }


                    function handleFileSelection(event) {

                        const file =
                            event.target.files[0];

                        if (!file) {
                            return;
                        }

                        if (
                            file.type !== "application/pdf" &&
                            !file.name.toLowerCase().endsWith(".pdf")
                        ) {

                            showError(
                                "Only PDF files are supported."
                            );

                            fileInput.value = "";

                            return;
                        }

                        selectedFile =
                            file;

                        if (fileName) {

                            fileName.textContent =
                                file.name;

                        }

                        if (fileStatus) {

                            fileStatus.textContent =
                                formatFileSize(
                                    file.size
                                );

                        }

                        if (fileInfo) {
                            fileInfo.hidden = false;
                        }

                        if (uploadButton) {
                            uploadButton.disabled = false;
                        }

                        hideError();
                    }


                    // =========================================================
                    // DRAG & DROP
                    // =========================================================

                    if (uploadArea) {

                        uploadArea.addEventListener(
                            "dragover",
                            event => {

                                event.preventDefault();

                                uploadArea.classList.add(
                                    "drag-over"
                                );

                            }
                        );

                        uploadArea.addEventListener(
                            "dragleave",
                            () => {

                                uploadArea.classList.remove(
                                    "drag-over"
                                );

                            }
                        );

                        uploadArea.addEventListener(
                            "drop",
                            event => {

                                event.preventDefault();

                                uploadArea.classList.remove(
                                    "drag-over"
                                );

                                const file =
                                    event.dataTransfer.files[0];

                                if (!file) {
                                    return;
                                }

                                if (
                                    !file.name
                                        .toLowerCase()
                                        .endsWith(".pdf")
                                ) {

                                    showError(
                                        "Only PDF files are supported."
                                    );

                                    return;
                                }

                                selectedFile =
                                    file;

                                if (fileName) {
                                    fileName.textContent =
                                        file.name;
                                }

                                if (fileStatus) {
                                    fileStatus.textContent =
                                        formatFileSize(file.size);
                                }

                                if (fileInfo) {
                                    fileInfo.hidden = false;
                                }

                                if (uploadButton) {
                                    uploadButton.disabled = false;
                                }

                                hideError();

                            }
                        );
                    }


                    // =========================================================
                    // UPLOAD DOCUMENT
                    // =========================================================

                    if (uploadButton) {

                        uploadButton.addEventListener(
                            "click",
                            uploadDocument
                        );

                    }


                    async function uploadDocument() {

                        if (!requireAuthentication()) {
                            return;
                        }

                        if (!selectedFile) {

                            showError(
                                "Please select a PDF first."
                            );

                            return;
                        }

                        const formData =
                            new FormData();

                        formData.append(
                            "file",
                            selectedFile
                        );

                        try {

                            setLoading(
                                true,
                                "Processing your document..."
                            );

                            hideError();

                            uploadButton.disabled =
                                true;

                            if (fileStatus) {
                                fileStatus.textContent =
                                    "Processing...";
                            }

                            const response =
                                await fetch(
                                    "/api/documents/upload",
                                    {
                                        method: "POST",

                                        headers: {
                                            ...authHeaders()
                                        },

                                        body: formData
                                    }
                                );

                            if (response.status === 401) {

                                handleUnauthorized();

                                return;
                            }

                            const data =
                                await response.json();

                            if (!response.ok) {

                                throw new Error(
                                    data.detail ||
                                    "Document upload failed."
                                );

                            }

                            currentDocumentId =
                                data.document_id;

                            currentDocument = {
                                document_id:
                                    data.document_id,

                                filename:
                                    data.filename,

                                pages:
                                    data.pages,

                                chunks:
                                    data.chunks,

                                status:
                                    data.status
                            };

                            localStorage.setItem(
                                "currentDocumentId",
                                currentDocumentId
                            );

                            if (fileStatus) {
                                fileStatus.textContent =
                                    "Ready";
                            }

                            selectedFile = null;

                            if (fileInput) {
                                fileInput.value = "";
                            }

                            if (fileInfo) {
                                fileInfo.hidden = true;
                            }

                            await loadDocuments();

                            // =====================================================
                            // NOTIFICATION - DOCUMENT PROCESSED
                            // =====================================================

                            addNotification({
                                type: "document",
                                title: "Document processed",
                                message:
                                    `${data.filename || "Your document"} is ready to use with DocuMind AI.`,
                                icon: "fa-file-circle-check"
                            });

                            setLoading(false);

                            openAssistantPage();

                        }
                        catch (error) {

                            console.error(
                                "Upload error:",
                                error
                            );

                            showError(
                                error.message ||
                                "Unable to process document."
                            );

                            if (fileStatus) {
                                fileStatus.textContent =
                                    "Failed";
                            }

                        }
                        finally {

                            uploadButton.disabled =
                                false;

                            setLoading(false);

                        }
                    }


                    // =========================================================
                    // DASHBOARD UPLOAD BUTTONS
                    // =========================================================

                    function openUploadSection() {

                        showDashboardPage();

                        setTimeout(() => {

                            if (uploadArea) {

                                uploadArea.scrollIntoView({
                                    behavior: "smooth",
                                    block: "center"
                                });

                            }

                        }, 100);

                    }


                    if (dashboardUploadButton) {

                        dashboardUploadButton.addEventListener(
                            "click",
                            openUploadSection
                        );

                    }


                    if (documentsUploadButton) {

                        documentsUploadButton.addEventListener(
                            "click",
                            openUploadSection
                        );

                    }


                    if (viewAllDocuments) {

                        viewAllDocuments.addEventListener(
                            "click",
                            showDocumentsPage
                        );

                    }


                    // =========================================================
                    // ASK BUTTON
                    // =========================================================

                    if (askButton) {

                        askButton.addEventListener(
                            "click",
                            askQuestion
                        );

                    }


                    if (questionInput) {

                        questionInput.addEventListener(
                            "keydown",
                            event => {

                                if (
                                    event.key === "Enter" &&
                                    !event.shiftKey
                                ) {

                                    event.preventDefault();

                                    askQuestion();

                                }

                            }
                        );

                    }


                    // =========================================================
                    // NAVIGATION CLICK HANDLERS
                    // =========================================================

                    navItems.forEach(item => {

                        item.addEventListener(
                            "click",
                            () => {

                                const page =
                                    item.dataset.page;

                                if (page === "dashboard") {

                                    showDashboardPage();

                                }

                                else if (page === "documents") {

                                    showDocumentsPage();

                                }

                                else if (page === "assistant") {

                                    // ---------------------------------------------------------
                                    // DO NOT AUTOMATICALLY OPEN THE FIRST DOCUMENT
                                    //
                                    // AI Assistant should start empty after login.
                                    // A document must be intentionally selected.
                                    // ---------------------------------------------------------

                                    if (!currentDocumentId) {

                                        setActiveNav("assistant");

                                        hideDashboardSections();

                                        if (chatCard) {
                                            chatCard.hidden = false;
                                        }

                                        if (dynamicPage) {
                                            dynamicPage.hidden = true;
                                        }

                                        // Update header to neutral state
                                        const chatDocumentName =
                                            document.getElementById(
                                                "chatDocumentName"
                                            );

                                        if (chatDocumentName) {

                                            chatDocumentName.textContent =
                                                "Select a document to begin.";
                                        }

                                        // Create / get chat history
                                        const history =
                                            createChatHistoryContainer();

                                        if (history) {

                                            history.innerHTML = `
                        <div class="chat-welcome">

                            <div class="chat-welcome-icon">
                                ✦
                            </div>

                            <h3>
                                Ready to explore your documents
                            </h3>

                            <p>
                                Select a document to start a conversation
                                with DocuMind AI.
                            </p>

                            <span>
                                Ask questions, summarize content,
                                extract key information, or clarify concepts.
                            </span>

                        </div>
                    `;
                                        }

                                        return;
                                    }

                                    // ---------------------------------------------------------
                                    // A DOCUMENT WAS INTENTIONALLY SELECTED
                                    // ---------------------------------------------------------

                                    openAssistantPage();
                                }

                                else if (page === "history") {

                                    showHistoryPage();

                                }

                                else if (page === "settings") {

                                    showSettingsPage();

                                }

                            }
                        );

                    });


                    // =========================================================
                    // LOGOUT
                    // =========================================================

                    const logoutButton =
                        document.getElementById(
                            "logoutButton"
                        );


                    if (logoutButton) {

                        logoutButton.addEventListener(
                            "click",
                            logout
                        );

                    }                    
                function logout() {
                    localStorage.removeItem("access_token");
                    localStorage.removeItem("currentDocumentId");
                    currentDocumentId = null;
                    currentDocument = null;
                    documents = [];
                    window.location.reload();
                }
                function bindLogoutButton(id) {
                    const button = document.getElementById(id);

                    if (!button || button.dataset.logoutBound === "true") {
                        return;
                    }

                    button.dataset.logoutBound = "true";
                    button.addEventListener("click", logout);
                }

                function initializeLogoutButtons() {
                    bindLogoutButton("profileLogoutButton");
                    bindLogoutButton("settingsLogoutButton");
                    bindLogoutButton("securityLogout");
                }

                if (document.readyState === "loading") {
                    document.addEventListener("DOMContentLoaded", initializeLogoutButtons);
                } else {
                    initializeLogoutButtons();
                }
                    // =========================================================
                    // USAGE NOTIFICATION CHECK
                    // =========================================================
                    function checkUsageNotifications({
                        documentsUsed = 0,
                        documentLimit = 0,
                        questionsUsed = 0,
                        questionLimit = 0
                    }) {

                        const userKey =
                            currentUser?.email ||
                            "anonymous";

                        const notificationPrefix =
                            `documind_usage_notification_${userKey}`;


                        // -----------------------------------------------------
                        // DOCUMENT USAGE
                        // -----------------------------------------------------

                        if (
                            documentLimit > 0
                        ) {

                            const documentPercentage =
                                Math.round(
                                    (
                                        documentsUsed /
                                        documentLimit
                                    ) * 100
                                );

                            if (
                                documentPercentage >= 100
                            ) {
                                const storageKey =
                                    `${notificationPrefix}_documents_100`;
                                if (
                                    localStorage.getItem(
                                        storageKey
                                    ) !== "sent"
                                ) {
                                    if (
                                        addNotification({
                                            type: "usage",
                                            title:"Document limit reached",
                                                message:
                                                    `You have reached your document limit of ${documentLimit}.`,
                                                icon:
                                                    "fa-file-circle-exclamation"
                                        })
                                    ) {
                                        localStorage.setItem(
                                            storageKey,
                                            "sent"
                                        );
                                    }
                                }
                            }
                            else if (
                                documentPercentage >= 80
                            ) {
                                const storageKey =
                                    `${notificationPrefix}_documents_80`;
                                if (
                                    localStorage.getItem(
                                        storageKey
                                    ) !== "sent"
                                ) {

                                    if (
                                        addNotification({

                                            type: "usage",

                                            title:
                                                "Document usage is high",

                                            message:
                                                `You are using ${documentsUsed} of ${documentLimit} available documents.`,
                                            icon:
                                                "fa-chart-line"

                                        })
                                    ) {

                                        localStorage.setItem(
                                            storageKey,
                                            "sent"
                                        );
                                    }
                                }
                            }
                        }
                        // -----------------------------------------------------
                        // QUESTION USAGE
                        // -----------------------------------------------------

                        if (
                            questionLimit > 0
                        ) {

                            const questionPercentage =
                                Math.round(
                                    (
                                        questionsUsed /
                                        questionLimit
                                    ) * 100
                                );


                            if (
                                questionPercentage >= 100
                            ) {

                                const storageKey =
                                    `${notificationPrefix}_questions_100`;

                                if (
                                    localStorage.getItem(
                                        storageKey
                                    ) !== "sent"
                                ) {
                               if (
                                    addNotification({

                                        type: "usage",
                                        title:
                                            "Question limit reached",
                                        message:
                                            `You have reached your question limit of ${questionLimit}.`,
                                        icon:
                                            "fa-circle-exclamation"
                                        })
                                    ) {

                                    localStorage.setItem(
                                            storageKey,
                                            "sent"
                                        );
                                    }
                                }
                            }
                            else if (
                                questionPercentage >= 80
                            ) {

                                const storageKey =
                                    `${notificationPrefix}_questions_80`;

                                if (
                                    localStorage.getItem(
                                        storageKey
                                    ) !== "sent"
                                ) {

                                    if (
                                        addNotification({

                                            type: "usage",

                                            title:
                                                "Question  usage is high",

                                            message:
                                               `You are using ${questionsUsed} of ${questionLimit} available questions.`,
                                            icon:
                                                "fa-chart-line"
                                        })
                                    ) {
                                        localStorage.setItem(
                                            storageKey,
                                            "sent"
                                        );
                                    }

                                }

                            }

                        }

                    }
                    // =========================================================
                    // STATISTICS
                    // =========================================================
                    async function updateStatistics() {

                        try {

                            // =====================================================
                            // GET SUBSCRIPTION / USAGE DATA
                            // =====================================================

                            const response =
                                await fetch(
                                    "/api/subscription",
                                    {
                                        method: "GET",
                                        headers: {
                                            ...authHeaders()
                                        }
                                    }
                                );


                            if (!response.ok) {

                                console.error(
                                    "Failed to load subscription data."
                                );

                                return;
                            }


                            const subscription =
                                await response.json();
                            // =====================================================
                            // USAGE VALUES
                            // =====================================================

                            const documentsUsed =
                                Number(
                                    subscription.documents_used || 0
                                );

                            const questionsUsed =
                                Number(
                                    subscription.questions_used || 0
                                );

                            const documentLimit =
                                Number(
                                    subscription.document_limit ||
                                    (subscription.plan === "premium"
                                        ? 50
                                        : 3)
                                );

                            const questionLimit =
                                Number(
                                    subscription.question_limit ||
                                    (subscription.plan === "premium"
                                        ? 500
                                        : 20)
                                );


                            // =====================================================
                            // DOCUMENT COUNT
                            // =====================================================

                            const documentCount =
                                document.getElementById(
                                    "documentCount"
                                );

                            if (documentCount) {

                                documentCount.textContent =
                                    documentsUsed;
                            }
                            // =====================================================
                            // QUESTIONS COUNT
                            // =====================================================

                            const questionCount =
                                document.getElementById(
                                    "questionCount"
                                );

                            if (questionCount) {

                                questionCount.textContent =
                                    questionsUsed;
                            }
                            // =====================================================
                            // USAGE NOTIFICATIONS
                            // =====================================================

                            if (
                                typeof checkUsageNotifications ===
                                "function"
                            ) {

                                checkUsageNotifications({
                                    documentsUsed,
                                    documentLimit,
                                    questionsUsed,
                                    questionLimit
                                });

                            }
                            // =====================================================
                            // AI USAGE
                            // =====================================================

                            const usage =
                                document.getElementById(
                                    "storageUsed"
                                );

                            if (usage) {

                                let totalChunks = 0;


                                documents.forEach(doc => {

                                    totalChunks +=
                                        Number(
                                            doc.chunks || 0
                                        );

                                });


                                const percentage =
                                    Math.min(
                                        100,
                                        totalChunks * 2
                                    );


                                usage.textContent =
                                    `${percentage}%`;
                            }


                        }
                        catch (error) {

                            console.error(
                                "Statistics error:",
                                error
                            );

                        }
                    }

                    // =========================================================
                    // LOADING
                    // =========================================================

                    function setLoading(
                        visible,
                        message = "Processing..."
                    ) {

                        if (!loading) {
                            return;
                        }

                        loading.hidden =
                            !visible;

                        if (loadingText) {

                            loadingText.textContent =
                                message;

                        }
                    }


                    // =========================================================
                    // ERROR
                    // =========================================================

                    function showError(message) {

                        if (!errorMessage) {
                            return;
                        }

                        errorMessage.textContent =
                            message;

                        errorMessage.hidden =
                            false;

                    }
                    // =========================================================
                    // SUCCESS MESSAGE
                    // =========================================================

                    function showSuccess(message) {

                        // Remove existing success message
                        const existing =
                            document.getElementById("documindSuccessMessage");

                        if (existing) {
                            existing.remove();
                        }

                        // Create success message
                        const success =
                            document.createElement("div");

                        success.id =
                            "documindSuccessMessage";

                        success.className =
                            "documind-success-message";

                        success.textContent =
                            message;

                        // Add to page
                        document.body.appendChild(success);

                        // Auto remove
                        setTimeout(() => {

                            if (success && success.parentNode) {
                                success.remove();
                            }

                        }, 4000);
                    }

                    function hideError() {

                        if (!errorMessage) {
                            return;
                        }

                        errorMessage.hidden =
                            true;

                        errorMessage.textContent =
                            "";

                    }


                    // =========================================================
                    // UTILITIES
                    // =========================================================

                    function formatFileSize(bytes) {

                        if (bytes < 1024) {

                            return `${bytes} B`;

                        }

                        if (bytes < 1024 * 1024) {

                            return `${(
                                bytes / 1024
                            ).toFixed(1)} KB`;

                        }

                        return `${(
                            bytes /
                            (1024 * 1024)
                        ).toFixed(1)} MB`;

                    }


                    function escapeHtml(text) {

                        const div =
                            document.createElement(
                                "div"
                            );

                        div.textContent =
                            text ?? "";

                        return div.innerHTML;

                    }

                    // =========================================================
                    // RENDER MATHEMATICS IN AI ANSWERS
                    // =========================================================

                    function renderMath(element) {

                        if (!element) {
                            return;
                        }

                        const render =
                            () => {

                                if (
                                    window.MathJax &&
                                    typeof window.MathJax.typesetPromise ===
                                    "function"
                                ) {

                                    window.MathJax.typesetClear?.(
                                        [element]
                                    );

                                    window.MathJax.typesetPromise(
                                        [element]
                                    ).catch(
                                        error => {
                                            console.warn(
                                                "MathJax rendering error:",
                                                error
                                            );
                                        }
                                    );
                                }
                            };

                        if (
                            window.MathJax &&
                            typeof window.MathJax.typesetPromise ===
                            "function"
                        ) {

                            render();

                        } else {

                            setTimeout(
                                render,
                                500
                            );
                        }
                    }
                    function formatAnswer(text) {
                        let formatted = escapeHtml(String(text));

                        // Markdown headings: ### Heading
                        formatted = formatted.replace(
                            /^###\s+(.*)$/gm,
                            "<h3>$1</h3>"
                        );

                        // Bold: **text**
                        formatted = formatted.replace(
                            /\*\*(.*?)\*\*/g,
                            "<strong>$1</strong>"
                        );

                        // Preserve line breaks
                        formatted = formatted.replace(/\n/g, "<br>");

                        return formatted;
                    }

                    function capitalize(text) {

                        if (!text) {
                            return "User";
                        }

                        return text.charAt(0).toUpperCase()
                            + text.slice(1);

                    }
                    // =========================================================
                    // DOCUMIND SETTINGS STORAGE
                    // =========================================================

                    const DOCUMIND_SETTINGS_KEY =
                        "documind_settings";

                    const defaultDocuMindSettings = {

                        notifications: {
                            documentProcessing: true,
                            aiResponses: true,
                            usageAlerts: true,
                            paymentUpdates: true,
                            subscriptionAlerts: true,
                            productUpdates: false,
                            reminder7Days: true,
                            reminder1Day: true,
                            reminderOnExpiry: true
                        },
                        personalization: {
                                theme: "light",
                                compactInterface: false,
                                documentDetails: true,
                                rememberLastDocument: true,
                                showSources: true,
                                density: "standard"
                        },
                        ai: {
                            showSources: true,
                            saveHistory: true,
                            explainAnswers: true,
                            renderMath: true,
                            preserveNotation: true,
                            responseLength: "balanced",
                            answerFormat: "structured",
                            notFoundBehavior: "document-only"
                        },
                    };

                    function getDocuMindSettings() {
                        try {
                            const saved =
                                localStorage.getItem(
                                    DOCUMIND_SETTINGS_KEY
                                );
                            if (!saved) {
                                return JSON.parse(
                                    JSON.stringify(
                                        defaultDocuMindSettings
                                    )
                                );
                            }
                            const parsed =
                                JSON.parse(saved);
                            return {
                                notifications: {
                                    ...defaultDocuMindSettings.notifications,
                                    ...(parsed.notifications || {})
                                },                               
                                personalization: {
                                    ...defaultDocuMindSettings.personalization,
                                    ...(parsed.personalization || {})
                                },
                                ai: {
                                    ...defaultDocuMindSettings.ai,
                                    ...(parsed.ai || {})
                                }

                            };

                        }
                        catch (error) {

                            console.error(
                                "Unable to load DocuMind settings:",
                                error
                            );

                            return JSON.parse(
                                JSON.stringify(
                                    defaultDocuMindSettings
                                )
                            );

                        }

                    }
                    function saveDocuMindSettings(settings) {

                        try {

                            // ---------------------------------------------------------
                            // SAVE SETTINGS
                            // ---------------------------------------------------------

                            localStorage.setItem(
                                DOCUMIND_SETTINGS_KEY,
                                JSON.stringify(settings)
                            );


                            // ---------------------------------------------------------
                            // SHOW "SAVED JUST NOW"
                            // ---------------------------------------------------------

                            showSettingsSavedState();


                            // ---------------------------------------------------------
                            // NOTIFY OTHER DOCUMIND COMPONENTS
                            // ---------------------------------------------------------

                            document.dispatchEvent(
                                new CustomEvent(
                                    "documind:settingsChanged"
                                )
                            );

                        }

                        catch (error) {

                            console.error(
                                "Unable to save DocuMind settings:",
                                error
                            );

                        }
                    }
                    
                    function applyPersonalizationSettings() {
                        const settings = getDocuMindSettings();
                        const personalization = settings.personalization || {};
                       const selectedTheme =
                            personalization.theme === "dark" ? "dark" : "light";

                        document.documentElement.dataset.theme = selectedTheme;
                        document.documentElement.style.colorScheme = selectedTheme;

                         // =====================================================
                        // SYNC PROFILE DROPDOWN APPEARANCE LABEL
                        // =====================================================

                        const dropdownAppearanceLabel =
                            document.getElementById(
                                "dropdownAppearanceLabel"
                            );

                        if (dropdownAppearanceLabel) {

                            dropdownAppearanceLabel.textContent =
                                selectedTheme === "dark"
                                    ? "Dark mode"
                                    : "Light mode";
                        }
                        
                        // =====================================================
                        // EXISTING PERSONALIZATION CODE
                        // =====================================================

                        // Apply interface density without replacing the page UI.
                        document.documentElement.dataset.interfaceDensity =
                            personalization.density || "standard";

                        // Apply compact layout as a class so existing CSS can control it.
                        document.body.classList.toggle(
                            "documind-compact-interface",
                            Boolean(personalization.compactInterface)
                        );
                        // Update document detail visibility only if the app has
                        // an existing element specifically marked for document details.
                        document.querySelectorAll("[data-document-details]").forEach(element => {
                            element.hidden = !Boolean(personalization.documentDetails);
                        });
                    }
                    // =====================================================
                    // INITIALIZE APPEARANCE ON APP STARTUP
                    // =====================================================

                    (function initializeDocuMindAppearance() {
                        if (document.readyState === "loading") {
                            document.addEventListener(
                                "DOMContentLoaded",
                                applyPersonalizationSettings,
                                { once: true }
                            );
                        } else {
                            applyPersonalizationSettings();
                        }
                    })();
                    /* =========================================================
                       SETTINGS SAVE STATUS
                       ========================================================= */

                    let settingsSaveStatusTimer = null;


                    function findSettingsSaveStatusElement(
                        section
                    ) {

                        if (!section) {
                            return null;
                        }


                        // ---------------------------------------------------------
                        // If we already created/found the status element
                        // ---------------------------------------------------------

                        const existing =
                            section.querySelector(
                                "[data-documind-save-status]"
                            );

                        if (existing) {
                            return existing;
                        }


                        // ---------------------------------------------------------
                        // Find existing "Saved automatically" text
                        // WITHOUT creating another element.
                        //
                        // This prevents duplicate IDs/elements.
                        // ---------------------------------------------------------

                        const candidates =
                            section.querySelectorAll(
                                "span, strong, small, div, p"
                            );


                        for (
                            const element of candidates
                        ) {

                            const text =
                                element.textContent
                                    ?.trim();


                            if (
                                text ===
                                "Saved automatically"
                            ) {

                                element.setAttribute(
                                    "data-documind-save-status",
                                    "true"
                                );

                                return element;
                            }

                        }


                        // ---------------------------------------------------------
                        // If the existing HTML does not contain the status,
                        // create ONE status element.
                        // ---------------------------------------------------------

                        const cards =
                            section.querySelectorAll(
                                ".settings-card"
                            );


                        if (!cards.length) {
                            return null;
                        }


                        const lastCard =
                            cards[cards.length - 1];


                        const status =
                            document.createElement(
                                "span"
                            );


                        status.setAttribute(
                            "data-documind-save-status",
                            "true"
                        );


                        status.textContent =
                            "Saved automatically";


                        status.style.fontSize =
                            "12px";


                        status.style.fontWeight =
                            "600";


                        status.style.color =
                            "#16a34a";


                        lastCard.appendChild(
                            status
                        );


                        return status;
                    }


                    function showSettingsSavedState() {

                        // ---------------------------------------------------------
                        // Find currently visible settings section
                        // ---------------------------------------------------------

                        const sections =
                            document.querySelectorAll(
                                "[data-settings-content]"
                            );


                        let activeSection = null;


                        sections.forEach(
                            function (section) {

                                if (
                                    !section.hidden &&
                                    getComputedStyle(
                                        section
                                    ).display !== "none"
                                ) {

                                    activeSection =
                                        section;

                                }

                            }
                        );


                        // ---------------------------------------------------------
                        // Fallback: notifications
                        // ---------------------------------------------------------

                        if (!activeSection) {

                            activeSection =
                                document.querySelector(
                                    '[data-settings-content="notifications"]'
                                );

                        }


                        if (!activeSection) {
                            return;
                        }


                        const status =
                            findSettingsSaveStatusElement(
                                activeSection
                            );


                        if (!status) {
                            return;
                        }


                        // ---------------------------------------------------------
                        // CLEAR OLD TIMER
                        // ---------------------------------------------------------

                        if (
                            settingsSaveStatusTimer
                        ) {

                            clearTimeout(
                                settingsSaveStatusTimer
                            );

                        }


                        // ---------------------------------------------------------
                        // SAVED JUST NOW
                        // ---------------------------------------------------------

                        status.textContent =
                            "Saved just now";


                        status.style.color =
                            "#16a34a";


                        status.style.fontWeight =
                            "600";


                        // ---------------------------------------------------------
                        // RETURN TO NORMAL STATE
                        // ---------------------------------------------------------

                        settingsSaveStatusTimer =
                            setTimeout(
                                function () {

                                    status.textContent =
                                        "Saved automatically";

                                    status.style.color =
                                        "#16a34a";

                                },
                                2500
                            );

                    }

                    // =========================================================
                    //  PROFESSIONAL SETTINGS UI
                    // =========================================================

                    function ensurePhase8SettingsStyles() {

                        if (
                            document.getElementById(
                                "phase8SettingsStyles"
                            )
                        ) {
                            return;
                        }


                        const style =
                            document.createElement("style");

                        style.id =
                            "phase8SettingsStyles";


                        style.textContent = `

                        .phase8-settings-group {
                            margin-top: 24px;
                        }


                        .phase8-settings-group-title {
                            font-size: 13px;
                            font-weight: 700;
                            letter-spacing: 0.04em;
                            text-transform: uppercase;
                            color: #667085;
                            margin-bottom: 10px;
                        }


                        .phase8-settings-card {
                            border: 1px solid #e4e7ec;
                            border-radius: 14px;
                            background: #ffffff;
                            overflow: hidden;
                        }


                        .phase8-option {
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                            gap: 24px;
                            padding: 18px 20px;
                            border-bottom: 1px solid #eef0f3;
                        }


                        .phase8-option:last-child {
                            border-bottom: none;
                        }


                        .phase8-option-content {
                            min-width: 0;
                        }


                        .phase8-option-title {
                            display: block;
                            font-size: 14px;
                            font-weight: 650;
                            color: #101828;
                            margin-bottom: 4px;
                        }


                        .phase8-option-description {
                            display: block;
                            font-size: 12px;
                            line-height: 1.55;
                            color: #667085;
                            max-width: 620px;
                        }


                        .phase8-section-intro {
                            margin-bottom: 20px;
                        }


                        .phase8-section-intro p {
                            margin-top: 6px;
                            color: #667085;
                            font-size: 13px;
                            line-height: 1.6;
                        }


                        .phase8-subscription-box {
                            margin-top: 18px;
                            padding: 16px 18px;
                            border: 1px solid #e4e7ec;
                            border-radius: 12px;
                            background: #f8f9fc;
                        }


                        .phase8-subscription-title {
                            font-size: 13px;
                            font-weight: 700;
                            color: #101828;
                            margin-bottom: 12px;
                        }


                        .phase8-save-row {
                            display: flex;
                            align-items: center;
                            justify-content: flex-end;
                            gap: 12px;
                            margin-top: 18px;
                        }


                        .phase8-save-status {
                            font-size: 12px;
                            color: #667085;
                            opacity: 0;
                            transition: opacity 0.2s ease;
                        }


                        .phase8-save-status.visible {
                            opacity: 1;
                        }


                        .phase8-select {
                            min-width: 180px;
                            border: 1px solid #d0d5dd;
                            border-radius: 9px;
                            background: #ffffff;
                            color: #101828;
                            padding: 9px 34px 9px 11px;
                            font-size: 13px;
                            outline: none;
                            cursor: pointer;
                        }


                        .phase8-select:focus {
                            border-color: #635bff;
                            box-shadow: 0 0 0 3px rgba(
                                99,
                                91,
                                255,
                                0.12
                            );
                        }


                        .phase8-choice-grid {
                            display: grid;
                            grid-template-columns:
                                repeat(
                                    3,
                                    minmax(0, 1fr)
                                );
                            gap: 10px;
                            margin-top: 10px;
                        }


                        .phase8-choice {
                            position: relative;
                        }


                        .phase8-choice input {
                            position: absolute;
                            opacity: 0;
                            pointer-events: none;
                        }


                        .phase8-choice label {
                            display: block;
                            padding: 12px;
                            border: 1px solid #d0d5dd;
                            border-radius: 10px;
                            cursor: pointer;
                            background: #ffffff;
                            transition:
                                border-color 0.15s ease,
                                background 0.15s ease;
                        }


                        .phase8-choice label strong {
                            display: block;
                            font-size: 13px;
                            color: #101828;
                            margin-bottom: 3px;
                        }


                        .phase8-choice label span {
                            display: block;
                            font-size: 11px;
                            color: #667085;
                            line-height: 1.4;
                        }


                        .phase8-choice input:checked + label {
                            border-color: #635bff;
                            background: #f5f3ff;
                        }


                        .phase8-info-banner {
                            display: flex;
                            gap: 10px;
                            align-items: flex-start;
                            margin-bottom: 18px;
                            padding: 13px 15px;
                            border: 1px solid #e4e7ec;
                            border-radius: 10px;
                            background: #f8f9fc;
                        }


                        .phase8-info-icon {
                            font-size: 16px;
                        }


                        .phase8-info-text {
                            font-size: 12px;
                            color: #667085;
                            line-height: 1.55;
                        }


                        @media (max-width: 760px) {

                            .phase8-option {
                                align-items: flex-start;
                                flex-direction: column;
                                gap: 12px;
                            }


                            .phase8-choice-grid {
                                grid-template-columns: 1fr;
                            }


                            .phase8-select {
                                width: 100%;
                            }

                        }

                    `;
                        document.head.appendChild(
                            style
                        );
                    }


                    // =========================================================
                    // PHASE 8 - RENDER PROFESSIONAL SETTINGS
                    // =========================================================

                    function renderPhase8SettingsSections() {

                        ensurePhase8SettingsStyles();


                        const settingsPage =
                            document.querySelector(".settings-page");

                        if (!settingsPage) {
                            console.warn(
                                "Dynamic Settings page not found."
                            );

                            return;
                        }
                        const notificationsSection =
                            settingsPage.querySelector(
                                '[data-settings-content="notifications"]'
                            );

                        const personalizationSection =
                            settingsPage.querySelector(
                                '[data-settings-content="personalization"]'
                            );

                        const aiSection =
                            settingsPage.querySelector(
                                '[data-settings-content="ai"]'
                            );


                        if (
                            !notificationsSection ||
                            !personalizationSection ||
                            !aiSection
                        ) {
                            console.warn(
                                "Phase 8 settings sections not found."
                            );

                            return;
                        }


                        // =====================================================
                        // NOTIFICATIONS
                        // =====================================================

                        notificationsSection.innerHTML = `

                        <div class="settings-page-header">

                            <span class="section-label">
                                PREFERENCES
                            </span>

                            <h1>
                                Notifications
                            </h1>

                            <p>
                                Control which DocuMind AI events
                                you want to be notified about.
                            </p>

                        </div>


                        <div class="phase8-settings-group">

                        <div class="phase8-settings-group-title">
                                Workspace notifications
                            </div>

                            <div class="phase8-settings-card">

                                ${phase8NotificationRow(
                                            "notifDocumentProcessing",
                                            "Document processing",
                                            "Notify me when a PDF finishes processing.",
                                            "notifications",
                                            "documentProcessing"
                                        )}

                                ${phase8NotificationRow(
                                            "notifAIResponses",
                                            "AI responses",
                                            "Notify me when an AI response is ready.",
                                            "notifications",
                                            "aiResponses"
                                        )}

                                ${phase8NotificationRow(
                                            "notifUsageAlerts",
                                            "Usage alerts",
                                            "Warn me when I am approaching document or question limits.",
                                            "notifications",
                                            "usageAlerts"
                                        )}

                                ${phase8NotificationRow(
                                            "notifPaymentUpdates",
                                            "Payment updates",
                                            "Notify me about successful payments and billing activity.",
                                            "notifications",
                                            "paymentUpdates"
                                        )}

                                ${phase8NotificationRow(
                                            "notifSubscriptionAlerts",
                                            "Subscription reminders",
                                            "Notify me about Premium activation and subscription status.",
                                            "notifications",
                                            "subscriptionAlerts"
                                        )}

                                ${phase8NotificationRow(
                                            "notifProductUpdates",
                                            "Product updates",
                                            "Receive important DocuMind AI feature and product updates.",
                                            "notifications",
                                            "productUpdates"
                                        )}

                                ${phase8NotificationRow(
                                            "notifReminder7",
                                            "7-day reminders",
                                            "Notify me about important reminders seven days before they are due.",
                                            "notifications",
                                            "reminder7Days"
                                        )}

                                ${phase8NotificationRow(
                                            "notifReminder1",
                                            "1-day reminders",
                                            "Notify me about important reminders one day before they are due.",
                                            "notifications",
                                            "reminder1Day"
                                        )}

                                ${phase8NotificationRow(
                                            "notifReminderExpiry",
                                            "Expiry reminders",
                                            "Notify me when an important subscription or service expiry is approaching.",
                                            "notifications",
                                            "reminderOnExpiry"
                                        )}

                            </div>

                        </div>       
                        <div class="phase8-save-row">

                            <span
                                id="phase8NotificationsStatus"
                                class="phase8-save-status"
                            >
                                Saved
                            </span>
                        </div>
                    `;
                        // =====================================================
                        // PERSONALIZATION
                        // =====================================================

                        personalizationSection.innerHTML = `

                    <div class="settings-page-header">

                        <span class="section-label">
                            WORKSPACE
                        </span>

                        <h1>
                            Personalization
                        </h1>

                        <p>
                            Customize how DocuMind AI looks
                            and behaves while you work.
                        </p>

                    </div>


                    <div class="phase8-info-banner">

                        <span class="phase8-info-icon">
                            ✦
                        </span>

                        <span class="phase8-info-text">
                            These preferences are saved locally
                            to your DocuMind AI workspace and
                            remain available when you return.
                        </span>

                    </div>


                    <div class="phase8-settings-group">

                        <div class="phase8-settings-group-title">
                            Interface
                        </div>


                        <div class="phase8-settings-card">

                            ${phase8PersonalizationRow(
                                        "personalCompact",
                                        "Compact interface",
                                        "Use a denser workspace layout when working with documents.",
                                        "personalization",
                                        "compactInterface"
                                    )}


                            ${phase8PersonalizationRow(
                                        "personalDocumentDetails",
                                        "Show document details",
                                        "Display pages, chunks and processing information in document cards.",
                                        "personalization",
                                        "documentDetails"
                                    )}


                            ${phase8PersonalizationRow(
                                        "personalRememberDocument",
                                        "Remember last document",
                                        "Open the most recently used document when your workspace is restored.",
                                        "personalization",
                                        "rememberLastDocument"
                                    )}


                            ${phase8PersonalizationRow(
                                        "personalShowSources",
                                        "Show source references",
                                        "Keep source references visible when they are available.",
                                        "personalization",
                                        "showSources"
                                    )}

                        </div>

                    </div>


                    <div class="phase8-settings-group">

                        <div class="phase8-settings-group-title">
                            Interface density
                        </div>

                            <div class="phase8-settings-group">

                        <div class="phase8-settings-group-title">
                            Appearance
                        </div>

                        <div class="phase8-settings-card">
                            <div class="phase8-option">

                                <div class="phase8-option-content">
                                    <span class="phase8-option-title">
                                        Workspace theme
                                    </span>

                                    <span class="phase8-option-description">
                                        Choose light or dark mode.
                                    </span>
                                </div>

                                <select id="personalTheme" class="phase8-select">
                                    <option value="light">Light mode</option>
                                    <option value="dark">Dark mode</option>
                                </select>
                            </div>
                        </div>

                    </div>
                        <div class="phase8-settings-card">

                            <div class="phase8-option">

                                <div class="phase8-option-content">

                                    <span class="phase8-option-title">
                                        Workspace density
                                    </span>

                                    <span class="phase8-option-description">
                                        Choose how much information is displayed
                                        in the workspace at once.
                                    </span>

                                </div>


                                <select
                                    id="personalDensity"
                                    class="phase8-select"
                                >

                                    <option value="comfortable">
                                        Comfortable
                                    </option>

                                    <option value="standard">
                                        Standard
                                    </option>

                                    <option value="compact">
                                        Compact
                                    </option>

                                </select>

                            </div>

                        </div>

                    </div>


                    <div class="phase8-save-row">

                        <span
                            id="phase8PersonalizationStatus"
                            class="phase8-save-status"
                        >
                            Saved
                        </span>

                    </div>

                `;


                        // =====================================================
                        // AI PREFERENCES
                        // =====================================================

                        aiSection.innerHTML = `

                <div class="settings-page-header">

                    <span class="section-label">
                        AI SETTINGS
                    </span>

                    <h1>
                        AI Preferences
                    </h1>

                    <p>
                        Configure how DocuMind AI answers
                        questions about your documents.
                    </p>

                </div>


                <div class="phase8-info-banner">

                    <span class="phase8-info-icon">
                        ✦
                    </span>

                    <span class="phase8-info-text">
                        These settings control the preferred
                        presentation and behavior of the
                        document assistant.
                    </span>

                </div>


                <div class="phase8-settings-group">

                    <div class="phase8-settings-group-title">
                        Response style
                    </div>


                    <div class="phase8-settings-card">

                        <div class="phase8-option">

                            <div class="phase8-option-content">

                                <span class="phase8-option-title">
                                    Response length
                                </span>

                                <span class="phase8-option-description">
                                    Choose how detailed AI responses
                                    should normally be.
                                </span>

                            </div>


                            <select
                                id="aiResponseLength"
                                class="phase8-select"
                            >

                                <option value="concise">
                                    Concise
                                </option>

                                <option value="balanced">
                                    Balanced
                                </option>

                                <option value="detailed">
                                    Detailed
                                </option>

                            </select>

                        </div>


                        <div class="phase8-option">

                            <div class="phase8-option-content">

                                <span class="phase8-option-title">
                                    Answer format
                                </span>

                                <span class="phase8-option-description">
                                    Select the preferred structure
                                    for document answers.
                                </span>

                            </div>


                            <select
                                id="aiAnswerFormat"
                                class="phase8-select"
                            >

                                <option value="structured">
                                    Structured
                                </option>

                                <option value="natural">
                                    Natural
                                </option>

                                <option value="technical">
                                    Technical
                                </option>

                            </select>

                        </div>

                    </div>

                </div>


                <div class="phase8-settings-group">

                    <div class="phase8-settings-group-title">
                        Document intelligence
                    </div>


                    <div class="phase8-settings-card">

                        ${phase8AIRow(
                                    "aiSaveHistory",
                                    "Save chat history",
                                    "Keep document conversations available in Chat History.",
                                    "saveHistory"
                                )}


                        ${phase8AIRow(
                                    "aiExplainAnswers",
                                    "Explain answers",
                                    "Provide additional explanation when it helps clarify the answer.",
                                    "explainAnswers"
                                )}

                    </div>

                </div>


                <div class="phase8-settings-group">

                    <div class="phase8-settings-group-title">
                        Mathematical content
                    </div>


                    <div class="phase8-settings-card">

                        ${phase8AIRow(
                                    "aiRenderMath",
                                    "Render formulas clearly",
                                    "Preserve readable mathematical formatting in document answers.",
                                    "renderMath"
                                )}


                        ${phase8AIRow(
                                    "aiPreserveNotation",
                                    "Preserve mathematical notation",
                                    "Keep symbols, equations and mathematical notation intact where possible.",
                                    "preserveNotation"
                                )}

                    </div>

                </div>


                <div class="phase8-settings-group">

                    <div class="phase8-settings-group-title">
                        When information is not found
                    </div>


                    <div class="phase8-settings-card">

                        <div class="phase8-option">

                            <div class="phase8-option-content">

                                <span class="phase8-option-title">
                                    Fallback behavior
                                </span>

                                <span class="phase8-option-description">
                                    Choose how the assistant should
                                    respond when the document does
                                    not contain the requested information.
                                </span>

                            </div>


                            <select
                                id="aiNotFoundBehavior"
                                class="phase8-select"
                            >

                                <option value="document-only">
                                    Clearly say it was not found
                                </option>

                                <option value="general">
                                    Allow a general answer
                                </option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="phase8-save-row">

                    <span
                        id="phase8AIStatus"
                        class="phase8-save-status"
                    >
                        Saved
                    </span>
                </div>
            `;
                                console.log(
                                    "Phase 8 professional Settings UI rendered."
                                );
                            }
                    // =========================================================
                    // PHASE 8 - SETTINGS ROW HELPERS
                    // =========================================================

                    function phase8NotificationRow(
                        id,
                        title,
                        description,
                        group,
                        key
                    ) {

                        return `

        <div class="phase8-option">

            <div class="phase8-option-content">

                <span class="phase8-option-title">
                    ${title}
                </span>

                <span class="phase8-option-description">
                    ${description}
                </span>

            </div>


            <label class="settings-toggle">

                <input
                    type="checkbox"
                    id="${id}"
                    data-phase8-group="${group}"
                    data-phase8-key="${key}"
                >

                <span></span>

            </label>

        </div>

    `;
                    }


                    function phase8PersonalizationRow(
                        id,
                        title,
                        description,
                        group,
                        key
                    ) {

                        return `

        <div class="phase8-option">

            <div class="phase8-option-content">

                <span class="phase8-option-title">
                    ${title}
                </span>

                <span class="phase8-option-description">
                    ${description}
                </span>

            </div>


            <label class="settings-toggle">

                <input
                    type="checkbox"
                    id="${id}"
                    data-phase8-group="${group}"
                    data-phase8-key="${key}"
                >

                <span></span>

            </label>

        </div>

    `;
                    }


                    function phase8AIRow(
                        id,
                        title,
                        description,
                        key
                    ) {

                        return `

        <div class="phase8-option">

            <div class="phase8-option-content">

                <span class="phase8-option-title">
                    ${title}
                </span>

                <span class="phase8-option-description">
                    ${description}
                </span>

            </div>


            <label class="settings-toggle">

                <input
                    type="checkbox"
                    id="${id}"
                    data-phase8-group="ai"
                    data-phase8-key="${key}"
                >

                <span></span>

            </label>

        </div>

    `;
                    }


                    // =========================================================
                    // PHASE 8 - BIND SETTINGS CONTROLS
                    // =========================================================

                    function initializePhase8SettingsControls() {

                        const settings =
                            getDocuMindSettings();


                        // =====================================================
                        // HELPER
                        // =====================================================
                        function saveAndShowStatus(statusId) {
                            const status = document.getElementById(statusId);

                            // Show pending state immediately.
                            if (status) {
                                status.textContent = "Unsaved changes...";
                                status.classList.add("visible");
                            }

                            // Restart the 2.5-second auto-save timer for this status.
                            clearTimeout(saveAndShowStatus._timers?.[statusId]);

                            if (!saveAndShowStatus._timers) {
                                saveAndShowStatus._timers = {};
                            }

                            saveAndShowStatus._timers[statusId] = setTimeout(() => {
                                try {
                                    saveDocuMindSettings(settings);

                                    if (status) {
                                        status.textContent = "Saved automatically";
                                        status.classList.add("visible");
                                    }
                                } catch (error) {
                                    console.error("Settings auto-save failed:", error);

                                    if (status) {
                                        status.textContent = "Save failed. Please try again.";
                                        status.classList.add("visible");
                                    }
                                }
                            }, 2500);
                        }
                        // =====================================================
                        // NOTIFICATIONS
                        // =====================================================
                       const notificationMap = [
                        [
                            "notificationDocumentProcessing",
                            "documentProcessing"
                        ],

                        [
                            "notificationAIResponses",
                            "aiResponses"
                        ],

                        [
                            "notificationUsageAlerts",
                            "usageAlerts"
                        ],
                         [
                            "notifPaymentUpdates",
                            "paymentUpdates"
                        ],
                        [
                            "notificationSubscription",
                            "subscriptionAlerts"
                        ],

                        [
                            "notificationProductUpdates",
                            "productUpdates"
                        ],

                        [
                            "notificationExpiry7Days",
                            "reminder7Days"
                        ],

                        [
                            "notificationExpiry1Day",
                            "reminder1Day"
                        ],

                        [
                            "notificationExpiry",
                            "reminderOnExpiry"
                        ]

                    ];

                        notificationMap.forEach(
                            ([id, key]) => {

                                const element =
                                    document.getElementById(
                                        id
                                    );


                                if (!element) {
                                    return;
                                }


                                element.checked =
                                    Boolean(
                                        settings.notifications[key]
                                    );


                                element.addEventListener(
                                    "change",
                                    () => {

                                        settings.notifications[key] =
                                            element.checked;


                                        saveAndShowStatus(
                                            "phase8NotificationsStatus"
                                        );

                                    }
                                );

                            }
                        );


                        // =====================================================
                        // PERSONALIZATION
                        // =====================================================

                        const personalizationMap = [

                            [
                                "personalCompact",
                                "compactInterface"
                            ],

                            [
                                "personalDocumentDetails",
                                "documentDetails"
                            ],

                            [
                                "personalRememberDocument",
                                "rememberLastDocument"
                            ],

                            [
                                "personalShowSources",
                                "showSources"
                            ]

                        ];


                        personalizationMap.forEach(
                            ([id, key]) => {

                                const element =
                                    document.getElementById(
                                        id
                                    );


                                if (!element) {
                                    return;
                                }


                                element.checked =
                                    Boolean(
                                        settings.personalization[key]
                                    );


                                element.addEventListener(
                                    "change",
                                    () => {

                                        settings.personalization[key] =
                                            element.checked;


                                        // Save settings
                                        localStorage.setItem(
                                            "documind_settings",
                                            JSON.stringify(settings)
                                        );


                                        // Apply immediately
                                        applyPersonalizationSettings();


                                        // Update save status
                                        saveAndShowStatus(
                                            "phase8PersonalizationStatus"
                                        );

                                    }
                                );

                            }
                        );


                        // =====================================================
                        // DENSITY
                        // =====================================================

                        const density =
                            document.getElementById(
                                "personalDensity"
                            );


                        if (density) {

                            density.value =
                                settings.personalization.density ||
                                "standard";


                            density.addEventListener(
                                "change",
                                () => {

                                    settings.personalization.density =
                                        density.value;


                                    settings.personalization.density =
                                        density.value;


                                    localStorage.setItem(
                                        "documind_settings",
                                        JSON.stringify(settings)
                                    );


                                    applyPersonalizationSettings();


                                    saveAndShowStatus(
                                        "phase8PersonalizationStatus"
                                    );

                                }
                            );
                        }
                        // =====================================================
                        // THEME
                        // =====================================================

                        const themeSelect = document.getElementById("personalTheme");

                        if (themeSelect) {
                            // Load the current saved theme into the dropdown.
                            themeSelect.value =
                                settings.personalization.theme === "dark" ? "dark" : "light";

                            // Register exactly one change handler.
                            themeSelect.addEventListener("change", () => {
                                // Update the current settings object.
                                settings.personalization.theme = themeSelect.value;

                                // Save the updated settings before applying the theme.
                                saveDocuMindSettings(settings);

                                // Apply the newly saved preference immediately.
                                applyPersonalizationSettings();

                                // Update the existing status message.
                                saveAndShowStatus("phase8PersonalizationStatus");
                            });
                        }

                        // =====================================================
                        // AI TOGGLES
                        // =====================================================

                        const aiMap = [

                            [
                                "aiShowSources",
                                "showSources"
                            ],

                            [
                                "aiSaveHistory",
                                "saveHistory"
                            ],

                            [
                                "aiExplainAnswers",
                                "explainAnswers"
                            ],

                            [
                                "aiRenderMath",
                                "renderMath"
                            ],

                            [
                                "aiPreserveNotation",
                                "preserveNotation"
                            ]

                        ];


                        aiMap.forEach(
                            ([id, key]) => {

                                const element =
                                    document.getElementById(
                                        id
                                    );


                                if (!element) {
                                    return;
                                }


                                element.checked =
                                    Boolean(
                                        settings.ai[key]
                                    );


                                element.addEventListener(
                                    "change",
                                    () => {

                                        settings.ai[key] =
                                            element.checked;


                                        saveAndShowStatus(
                                            "phase8AIStatus"
                                        );

                                    }
                                );

                            }
                        );


                        // =====================================================
                        // AI SELECTS
                        // =====================================================

                        const responseLength =
                            document.getElementById(
                                "aiResponseLength"
                            );


                        if (responseLength) {

                            responseLength.value =
                                settings.ai.responseLength ||
                                "balanced";


                            responseLength.addEventListener(
                                "change",
                                () => {

                                    settings.ai.responseLength =
                                        responseLength.value;


                                    saveAndShowStatus(
                                        "phase8AIStatus"
                                    );

                                }
                            );

                        }


                        const answerFormat =
                            document.getElementById(
                                "aiAnswerFormat"
                            );


                        if (answerFormat) {

                            answerFormat.value =
                                settings.ai.answerFormat ||
                                "structured";


                            answerFormat.addEventListener(
                                "change",
                                () => {

                                    settings.ai.answerFormat =
                                        answerFormat.value;


                                    saveAndShowStatus(
                                        "phase8AIStatus"
                                    );

                                }
                            );

                        }


                        const notFoundBehavior =
                            document.getElementById(
                                "aiNotFoundBehavior"
                            );


                        if (notFoundBehavior) {

                            notFoundBehavior.value =
                                settings.ai.notFoundBehavior ||
                                "document-only";


                            notFoundBehavior.addEventListener(
                                "change",
                                () => {

                                    settings.ai.notFoundBehavior =
                                        notFoundBehavior.value;


                                    saveAndShowStatus(
                                        "phase8AIStatus"
                                    );

                                }
                            );

                        }


                        // =====================================================
                        // APPLY INITIAL STATE
                        // =====================================================

                        document.body.classList.toggle(
                            "compact-interface",
                            settings.personalization.compactInterface ||
                            settings.personalization.density === "compact"
                        );


                        document.body.dataset.phase8Density =
                            settings.personalization.density ||
                            "standard";


                        console.log(
                            "Phase 8 Settings initialized successfully."
                        );

                    }

                    function formatNotificationTime(
                        timestamp
                    ) {

                        const date =
                            new Date(timestamp);

                        if (
                            Number.isNaN(
                                date.getTime()
                            )
                        ) {
                            return "";
                        }

                        return date.toLocaleString(
                            "en-IN",
                            {
                                day: "2-digit",
                                month: "short",
                                hour: "2-digit",
                                minute: "2-digit"
                            }
                        );
                    }
                    // =========================================================
                    // DOCUMIND NOTIFICATION CENTER
                    // =========================================================
                    let docuMindNotifications = [];
                    docuMindNotifications = getNotifications();

                    renderNotificationCenter();

                    updateNotificationBadge();

                    function getNotifications() {

                        try {

                            const saved =
                                localStorage.getItem(
                                    "documind_notifications"
                                );

                            return saved
                                ? JSON.parse(saved)
                                : [];

                        }
                        catch (error) {

                            console.error(
                                "Notification loading error:",
                                error
                            );

                            return [];

                        }

                    }


                    function saveNotifications() {

                        localStorage.setItem(
                            "documind_notifications",
                            JSON.stringify(
                                docuMindNotifications
                            )
                        );

                    }


                    function addNotification({

                        type = "info",

                        title,

                        message,

                        icon = "fa-bell"

                    }) {

                        const settings =
                            getDocuMindSettings();


                        if (
                            type === "document" &&
                            !settings.notifications.documentProcessing
                        ) {
                            return false;
                        }


                        if (
                            type === "ai" &&
                            !settings.notifications.aiResponses
                        ) {
                            return false;
                        }
                        if (
                            type === "payment" &&
                            !settings.notifications.paymentUpdates
                        ) {
                            return false;
                        }
                        if (
                            type === "subscription" &&
                            !settings.notifications.subscriptionAlerts
                        ) {
                            return false;
                        }
                        // =====================================================
                        // USAGE ALERTS
                        // =====================================================

                        if (
                            type === "usage" &&
                            !settings.notifications.usageAlerts
                        ) {
                            return false;
                        }

                        // =====================================================
                        // PRODUCT UPDATES
                        // =====================================================

                        if (
                            type === "product" &&
                            !settings.notifications.productUpdates
                        ) {
                            return false;
                        }

                        // =====================================================
                        // SUBSCRIPTION REMINDERS
                        // =====================================================

                        if (
                            type === "reminder7" &&
                            !settings.notifications.reminder7Days
                        ) {
                             return false;
                        }


                        if (
                            type === "reminder1" &&
                            !settings.notifications.reminder1Day
                        ) {
                             return false;
                        }

                        if (
                            type === "expiry" &&
                            !settings.notifications.reminderOnExpiry
                        ) {
                             return false;
                        }

                        const notification = {

                            id:
                                crypto.randomUUID(),

                            type,

                            title,

                            message,

                            icon,

                            createdAt:
                                new Date().toISOString(),

                            read: false

                        };


                        docuMindNotifications.unshift(
                            notification
                        );


                        docuMindNotifications =
                            docuMindNotifications.slice(
                                0,
                                30
                            );
                        saveNotifications();
                        renderNotificationCenter();
                        updateNotificationBadge();
                        return true;
                    }

                    function updateNotificationBadge() {
                        const button =
                            document.getElementById(
                                "notificationButton"
                            );

                        if (!button) {
                            return;
                        }


                        const unreadCount =
                            docuMindNotifications.filter(
                                item => !item.read
                            ).length;


                        let badge =
                            button.querySelector(
                                ".notification-count"
                            );


                        if (!unreadCount) {

                            if (badge) {
                                badge.remove();
                            }

                            return;

                        }


                        if (!badge) {

                            badge =
                                document.createElement(
                                    "span"
                                );

                            badge.className =
                                "notification-count";

                            button.appendChild(
                                badge
                            );

                        }


                        badge.textContent =
                            unreadCount > 9
                                ? "9+"
                                : String(unreadCount);

                    }


                    function markAllNotificationsRead() {

                        docuMindNotifications =
                            docuMindNotifications.map(
                                notification => ({
                                    ...notification,
                                    read: true
                                })
                            );


                        saveNotifications();

                        renderNotificationCenter();

                        updateNotificationBadge();

                    }


                    function clearAllNotifications() {

                        docuMindNotifications = [];

                        saveNotifications();

                        renderNotificationCenter();

                        updateNotificationBadge();

                    }


                    function formatNotificationTime(
                        timestamp
                    ) {

                        const date =
                            new Date(timestamp);

                        if (
                            Number.isNaN(
                                date.getTime()
                            )
                        ) {
                            return "";
                        }


                        return date.toLocaleString(
                            "en-IN",
                            {
                                day: "2-digit",
                                month: "short",
                                hour: "2-digit",
                                minute: "2-digit"
                            }
                        );

                    }


                    function renderNotificationCenter() {

                        const panel =
                            document.getElementById(
                                "notificationPanel"
                            );

                        if (!panel) {
                            return;
                        }


                        if (!docuMindNotifications.length) {

                            panel.innerHTML = `

            <div class="notification-panel-header">

                <div>

                    <strong>function updateProfileMenu()
                        Notifications
                    </strong>

                </div>

            </div>


            <div class="notification-empty">

                <div class="notification-empty-icon">

                    <i class="fa-regular fa-bell-slash"></i>

                </div>


                <strong>
                    You're all caught up
                </strong>


                <p>
                    New activity and important account
                    updates will appear here.
                </p>

            </div>

        `;

                            return;

                        }


                        panel.innerHTML = `

        <div class="notification-panel-header">

            <div>

                <strong>
                    Notifications
                </strong>

                <span>
                    ${docuMindNotifications.length} recent
                </span>

            </div>


            <button
                type="button"
                class="notification-action-button"
                id="markNotificationsRead"
            >
                Mark all read
            </button>

        </div>


        <div class="notification-list">

            ${docuMindNotifications
                                .map(
                                    notification => `

                        <div
                            class="
                                notification-item
                                ${notification.read ? "read" : "unread"}
                            "
                        >

                            <div
                                class="
                                    notification-item-icon
                                    notification-${escapeHtml(
                                        notification.type
                                    )}
                                "
                            >

                                <i
                                    class="
                                        fa-solid
                                        ${escapeHtml(
                                        notification.icon
                                    )}
                                    "
                                ></i>

                            </div>


                            <div
                                class="notification-item-content"
                            >

                                <strong>
                                    ${escapeHtml(
                                        notification.title
                                    )}
                                </strong>


                                <p>
                                    ${escapeHtml(
                                        notification.message
                                    )}
                                </p>


                                <span>
                                    ${formatNotificationTime(
                                        notification.createdAt
                                    )}
                                </span>

                            </div>

                        </div>

                        `
                                )
                                .join("")
                            }

        </div>


        <div class="notification-panel-footer">

            <button
                type="button"
                id="clearNotifications"
                class="notification-clear-button"
            >
                Clear notifications
            </button>

        </div>

    `;


                        const markReadButton =
                            document.getElementById(
                                "markNotificationsRead"
                            );


                        if (markReadButton) {

                            markReadButton.onclick =
                                markAllNotificationsRead;

                        }


                        const clearButton =
                            document.getElementById(
                                "clearNotifications"
                            );


                        if (clearButton) {

                            clearButton.onclick =
                                clearAllNotifications;

                        }

                    }
                    // =========================================================
                    // TOPBAR - NOTIFICATIONS + USER MENU
                    // =========================================================

                    const notificationButton =
                        document.getElementById("notificationButton");

                    const notificationPanel =
                        document.getElementById("notificationPanel");

                    const userMenu =
                        document.getElementById("userMenu");


                    // ---------------------------------------------------------
                    // NOTIFICATION BUTTON
                    // ---------------------------------------------------------

                    if (notificationButton && notificationPanel) {

                        notificationButton.addEventListener(
                            "click",
                            function (event) {

                                event.stopPropagation();

                                const isHidden =
                                    notificationPanel.hidden;

                                notificationPanel.hidden =
                                    !isHidden;

                                // Close user menu if open
                                if (userProfilePanel) {
                                    userProfilePanel.hidden = true;
                                }
                            }
                        );
                    }                    
                        let userProfilePanel =
                            document.getElementById("userDropdown");

                        if (userMenu && userProfilePanel) {
                            userMenu.style.position = "relative";
                        }


                        // -----------------------------------------------------
                        // USER MENU CLICK
                        // -----------------------------------------------------

                        userMenu.addEventListener("click", function (event) {
                        event.stopPropagation();

                        if (!userProfilePanel) return;

                        userProfilePanel.hidden = !userProfilePanel.hidden;

                        if (notificationPanel) {
                            notificationPanel.hidden = true;
                        }

                        updateProfileMenu();
                    });

                        // -----------------------------------------------------
                        // SETTINGS FROM USER MENU
                        // -----------------------------------------------------

                        document.addEventListener(
                            "click",
                            function (event) {

                                if (
                                    event.target.closest(
                                        "#profileSettingsButton"
                                    )
                                ) {

                                    userProfilePanel.hidden =
                                        true;

                                    showSettingsPage();
                                }


                                if (
                                    event.target.closest(
                                        "#profileLogoutButton"
                                    )
                                ) {

                                    logout();
                                }

                            }
                        );
                    // ---------------------------------------------------------
                    // UPDATE PROFILE MENU
                    // ---------------------------------------------------------                   
                        function updateProfileMenu() {
                            if (!currentUser) return;

                            const email = currentUser.email || "";
                            const name = email.includes("@")
                                ? email.split("@")[0]
                                : email;

                            const displayName = capitalize(name);
                            const initial = displayName
                                ? displayName.charAt(0).toUpperCase()
                                : "U";

                            const headerName = document.getElementById("userName");
                            const headerAvatar = document.getElementById("userAvatar");
                            const dropdownName = document.getElementById("dropdownUserName");
                            const dropdownEmail = document.getElementById("dropdownUserEmail");
                            const dropdownAvatar = document.getElementById("dropdownAvatar");

                            if (headerName) headerName.textContent = displayName;
                            if (headerAvatar) headerAvatar.textContent = initial;
                            if (dropdownName) dropdownName.textContent = displayName;
                            if (dropdownEmail) dropdownEmail.textContent = email;
                            if (dropdownAvatar) dropdownAvatar.textContent = initial;
                        }                
                    
                        // ---------------------------------------------------------
                        // MY ACCOUNT BUTTON
                        // Reuse the existing dynamic-page architecture.
                        // ---------------------------------------------------------
                        const myAccountButton = document.getElementById("myAccountButton");

                        if (myAccountButton) {
                            myAccountButton.addEventListener("click", async function (event) {
                                event.preventDefault();
                                event.stopPropagation();

                                if (userProfilePanel) {
                                    userProfilePanel.hidden = true;
                                }

                                if (!requireAuthentication()) {
                                    return;
                                }

                                try {
                                    await loadCurrentUser();
                                } catch (error) {
                                    console.error("Unable to load account information:", error);
                                }

                                const user = currentUser || {};
                                const email = user.email || "";
                                const name = email.includes("@")
                                    ? email.split("@")[0]
                                    : email || "User";
                                const displayName = capitalize(name);
                                const plan = String(user.plan || "free").toUpperCase();

                                setActiveNav("");
                                hideDashboardSections();

                                showDynamicPage(`
                                    <div class="section-title">
                                        <span class="section-label">ACCOUNT</span>
                                        <h2>My Account</h2>
                                        <p>View your DocuMind AI profile information.</p>
                                    </div>

                                    <div class="settings-card">
                                        <div class="settings-card-header">
                                            <div>
                                                <h2>Profile information</h2>
                                                <p>Your registered account details</p>
                                            </div>
                                            <span class="settings-badge">${escapeHtml(plan)}</span>
                                        </div>

                                        <div class="settings-details">
                                            <div class="settings-detail-row">
                                                <div>
                                                    <strong>Name</strong>
                                                    <p>Your account display name</p>
                                                </div>
                                                <strong>${escapeHtml(displayName)}</strong>
                                            </div>

                                            <div class="settings-detail-row">
                                                <div>
                                                    <strong>Email</strong>
                                                    <p>Your registered email address</p>
                                                </div>
                                                <strong>${escapeHtml(email || "Not available")}</strong>
                                            </div>

                                            <div class="settings-detail-row">
                                                <div>
                                                    <strong>Plan</strong>
                                                    <p>Your current subscription plan</p>
                                                </div>
                                                <strong>${escapeHtml(plan)}</strong>
                                            </div>
                                        </div>
                                    </div>

                                    <button
                                        type="button"
                                        class="secondary-button"
                                        id="myAccountBackButton"
                                    >
                                        Back to Dashboard
                                    </button>
                                `);

                                document.getElementById("myAccountBackButton")
                                    ?.addEventListener("click", showDashboardPage);

                                window.scrollTo({ top: 0, behavior: "smooth" });
                            });
                        }
                    
                const roleAccessButton =
                    document.getElementById("roleAccessButton");

                if (roleAccessButton) {
                    roleAccessButton.addEventListener("click", async () => {
                        // Close the existing profile dropdown.
                        const dropdown = document.getElementById("userDropdown");
                        if (dropdown) dropdown.hidden = true;

                        // Reuse the existing authentication flow.
                        if (typeof requireAuthentication === "function") {
                            const authenticated = await requireAuthentication();
                            if (authenticated === false) return;
                        }

                        // Refresh the current user's information.
                        await loadCurrentUser();

                        if (!currentUser) {
                            showError("Unable to load your account information.");
                            return;
                        }

                        const plan = currentUser.plan || "free";
                        const status = currentUser.subscription_status || "unknown";

                        const escape = value =>
                            typeof escapeHtml === "function"
                                ? escapeHtml(String(value ?? ""))
                                : String(value ?? "").replace(/[&<>"']/g, char => ({
                                    "&": "&amp;",
                                    "<": "&lt;",
                                    ">": "&gt;",
                                    '"': "&quot;",
                                    "'": "&#39;"
                                })[char]);

                        setActiveNav("");
                        hideDashboardSections();

                        showDynamicPage(`
                            <div class="settings-page-header">
                                <span class="section-label">ACCOUNT ACCESS</span>
                                <h1>Role &amp; Access</h1>
                                <p>View your account plan, usage limits, and subscription status.</p>
                            </div>

                            <div class="settings-card">
                                <div class="settings-card-header">
                                    <div>
                                        <h2>Account overview</h2>
                                        <p>Your current account information.</p>
                                    </div>
                                </div>

                                <div class="settings-option">
                                    <div>
                                        <strong>Account type</strong>
                                        <p>Your current subscription plan.</p>
                                    </div>
                                    <span class="settings-badge">${escape(plan)}</span>
                                </div>

                                <div class="settings-option">
                                    <div>
                                        <strong>Subscription status</strong>
                                        <p>Current status reported by the server.</p>
                                    </div>
                                    <span class="settings-badge">${escape(status)}</span>
                                </div>

                                <div class="settings-option">
                                    <div>
                                        <strong>Questions used</strong>
                                        <p>Questions consumed in your current usage period.</p>
                                    </div>
                                    <span>${escape(currentUser.questions_used ?? 0)}
                                        / ${escape(currentUser.question_limit ?? "—")}</span>
                                </div>

                                <div class="settings-option">
                                    <div>
                                        <strong>Document limit</strong>
                                        <p>Maximum documents allowed by your plan.</p>
                                    </div>
                                    <span>${escape(currentUser.document_limit ?? "—")}</span>
                                </div>

                                <div class="settings-option">
                                    <div>
                                        <strong>Maximum file size</strong>
                                        <p>Upload size limit for your account.</p>
                                    </div>
                                    <span>${escape(currentUser.max_file_size_mb ?? "—")} MB</span>
                                </div>
                            </div>

                            <div class="settings-card">
                                <div class="settings-card-header">
                                    <div>
                                        <h2>Permissions</h2>
                                        <p>
                                            Detailed roles and permissions are not currently
                                            provided by the account API.
                                        </p>
                                    </div>
                                </div>

                                <p>
                                    This page displays account limits only. It does not
                                    grant or change permissions.
                                </p>
                            </div>

                            <div class="settings-actions">
                                <button type="button"
                                    class="settings-secondary-button"
                                    id="roleAccessBackButton">
                                    Back to Dashboard
                                </button>
                            </div>
                        `);

                        document.getElementById("roleAccessBackButton")
                            ?.addEventListener("click", showDashboardPage);

                        window.scrollTo({ top: 0, behavior: "smooth" });
                    });
                    
                const appearanceButton = document.getElementById("appearanceButton");

                if (appearanceButton) {
                    appearanceButton.addEventListener("click", async function (event) {
                        event.preventDefault();
                        event.stopPropagation();

                        if (userProfilePanel) {
                            userProfilePanel.hidden = true;
                        }

                        if (!requireAuthentication()) {
                            return;
                        }

                        await showSettingsPage();

                        const personalizationButton = document.querySelector(
                            '.settings-nav-item[data-settings-section="personalization"]'
                        );

                        if (personalizationButton) {
                            personalizationButton.click();
                        }

                        window.scrollTo({ top: 0, behavior: "smooth" });
                    });
                }
                                }
                    // ---------------------------------------------------------
                    // CLOSE TOPBAR POPUPS WHEN CLICKING OUTSIDE
                    // ---------------------------------------------------------

                    document.addEventListener(
                        "click",
                        function (event) {

                            if (
                                notificationPanel &&
                                !event.target.closest(
                                    ".notification-wrapper"
                                )
                            ) {
                                notificationPanel.hidden =
                                    true;
                            }

                            if (
                                userProfilePanel &&
                                !event.target.closest(
                                    "#userMenu"
                                )
                            ) {
                                userProfilePanel.hidden =
                                    true;
                            }

                        }
                    );

                    // =========================================================
                    // INITIALIZE
                    // =========================================================
                    async function initializeApp() {

                        const token =
                            localStorage.getItem("access_token");


                        // No login → show landing page
                        if (!token) {

                            showLandingPage();

                            return;

                        }

                        // Token exists → try dashboard
                        try {

                            await loadCurrentUser();

                            await loadDocuments();


                            const savedDocumentId =
                                localStorage.getItem(
                                    "currentDocumentId"
                                );


                            if (savedDocumentId) {

                                const found =
                                    documents.find(
                                        doc =>
                                            doc.document_id ===
                                            savedDocumentId
                                    );


                                if (found) {

                                    currentDocument = found;

                                    currentDocumentId =
                                        found.document_id;

                                }

                            }


                            showDashboard();

                            showDashboardPage();


                        } catch (error) {

                            console.error(
                                "Initialization error:",
                                error
                            );


                            localStorage.removeItem(
                                "access_token"
                            );

                            localStorage.removeItem(
                                "currentDocumentId"
                            );


                            showAuthentication();

                        }

                    }

                    document.addEventListener(
                        "DOMContentLoaded",
                        initializeApp
                    );

                    /* =========================================================
                       PHASE 8A
                       RESPONSIVE SIDEBAR
                    ========================================================= */
                    document.addEventListener("DOMContentLoaded", function () {

                        const toggle = document.getElementById("sidebarToggle");
                        const sidebar = document.querySelector(".sidebar");
                        const overlay = document.getElementById("sidebarOverlay");

                        if (!toggle || !sidebar) return;

                        toggle.onclick = function () {

                            const isOpen = sidebar.classList.toggle("mobile-open");

                            if (isOpen) {
                                sidebar.style.setProperty(
                                    "transform",
                                    "translate3d(0,0,0)",
                                    "important"
                                );

                                overlay?.classList.add("active");

                                toggle.setAttribute("aria-expanded", "true");

                            } else {
                                sidebar.style.setProperty(
                                    "transform",
                                    "translate3d(-100%,0,0)",
                                    "important"
                                );

                                overlay?.classList.remove("active");

                                toggle.setAttribute("aria-expanded", "false");
                            }
                        };

                        overlay?.addEventListener("click", function () {

                            sidebar.classList.remove("mobile-open");

                            sidebar.style.setProperty(
                                "transform",
                                "translate3d(-100%,0,0)",
                                "important"
                            );

                            overlay.classList.remove("active");

                            toggle.setAttribute("aria-expanded", "false");
                        });

                    });
