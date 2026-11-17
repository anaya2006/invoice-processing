# ROLE
You are a senior full-stack engineer building "ANA-H1: Finance & Invoice Processing Automation": an internal accounts-payable tool for the BUYER company. An AP operator uploads a supplier invoice; the system reads it with OCR, extracts fields, validates it against stored vendor and purchase-order (PO) data, flags exceptions and duplicates, and routes it to a finance reviewer who approves, rejects, or requests correction. Every action goes into an append-only audit trail. The system must NEVER silently approve or post anything and never connects to a real bank/ERP (demo mode).
Goal today: a complete, locally running app (FastAPI backend + React frontend + SQLite + Tesseract OCR) demonstrating 5 scenarios: (1) clean invoice matches a PO with evidence; (2) quantity/amount mismatch raises exceptions; (3) the same invoice uploaded twice is held as a duplicate; (4) a low-confidence extraction is corrected by a human; (5) approve/reject with a visible audit history. Docker, Alembic and hosting are OUT OF SCOPE. Work in large batches, run tests after each stage, and stop only if something fails.

# EXISTING PROJECT STATE (stage 0: inspect before writing anything)
A partial backend already exists in backend/: .venv, core/, models/, api/, db/, schemas/, main.py. First list the actual tree and read every existing file. ADAPT TO THIS LAYOUT; do not restructure it and do not overwrite existing files without telling me what you are keeping and what you are changing. Target layout (create only what is missing):
backend/
  main.py
  core/      config.py, roles.py, money.py, errors.py
  db/        base.py (DeclarativeBase), session.py (engine, SessionLocal, get_db, PRAGMA foreign_keys=ON), triggers.py (audit triggers)
  models/    one file per aggregate (user, vendor, purchase_order, invoice, extraction, exception, audit_event), all imported in __init__.py
  schemas/   Pydantic request/response models, one file per area
  api/       health, auth, invoices, vendors, purchase_orders, dashboard, admin
  services/  workflow, audit, storage, auth, pipeline, validation, duplicates, anomaly, extraction/{quality,reader,parsing}
  scripts/   check_env, reset_db, seed_demo, make_samples, eval_extraction, eval_anomaly
  tests/, samples/
  requirements.txt, requirements-dev.txt, .env.example, .gitignore
Imports are relative to backend/ (run commands from backend/, e.g. `python -m uvicorn main:app --reload --port 8000`, `python -m pytest`, `python -m scripts.seed_demo`). Every package folder needs an __init__.py. The frontend goes in ../frontend (Vite React TS). Docs go in ../docs.

# TECH STACK (fixed)
- Python 3.11+, FastAPI, SQLAlchemy 2.0 (typed Mapped[...]), Pydantic v2 + pydantic-settings, uvicorn, python-multipart, argon2-cffi, pyjwt
- Database: SQLite (default ./ana.db) through SQLAlchemy using DATABASE_URL; keep constructs portable so PostgreSQL can replace it later. Create tables with Base.metadata.create_all at startup (no Alembic). `python -m scripts.reset_db` deletes and recreates the database.
- OCR/document: pytesseract + the Tesseract binary, opencv-python-headless, numpy, Pillow, PyMuPDF, pdfplumber, rapidfuzz, reportlab
- Frontend: React + Vite + TypeScript, React Router, plain CSS, dev proxy /api -> http://localhost:8000, CORS from config
- Tests: pytest + httpx with a temporary SQLite file per session
- Money: Decimal only, never float. A custom SQLAlchemy TypeDecorator (DecimalString) stores Decimal as exact TEXT with fixed places: money 2, quantity 3, unit price 4. Every amount has an ISO-4217 currency. Pydantic serialises Decimal as strings.

# ENVIRONMENT (do this first)
- All backend work uses the existing backend/.venv. Never install globally, never use --break-system-packages. Call tools through the venv interpreter (python -m pip / python -m pytest / python -m uvicorn).
- requirements.txt (runtime, exactly): fastapi, uvicorn[standard], sqlalchemy, pydantic, pydantic-settings, python-multipart, argon2-cffi, pyjwt, pytesseract, opencv-python-headless, numpy, Pillow, PyMuPDF, pdfplumber, rapidfuzz, reportlab. requirements-dev.txt: `-r requirements.txt`, pytest, httpx. Use opencv-python-headless, NOT opencv-python.
- Do not invent version numbers: install, confirm imports and tests pass, THEN write exact pins from what pip installed. Run `python -m pip check`.
- scripts/check_env.py verifies: Python >= 3.11; a venv is active (sys.prefix != sys.base_prefix); all packages import; the Tesseract binary runs; `eng` AND `osd` language data are present; pytesseract can OCR a generated image and OSD works on a generated rotated image. Print per-OS install instructions on failure (Windows UB-Mannheim installer + TESSERACT_CMD, macOS brew, Ubuntu apt tesseract-ocr tesseract-ocr-eng tesseract-ocr-osd). Exit non-zero on failure.
- config.py settings: DATABASE_URL, UPLOAD_DIR, MAX_UPLOAD_MB=10, ALLOWED_ORIGINS, DEMO_MODE=true, JWT_SECRET (placeholder in .env.example), JWT_EXPIRE_HOURS=8, TESSERACT_CMD, TESSDATA_PREFIX, OCR_MAX_PAGES=5, OCR_DPI=300, OCR_MIN_WORD_CONF=60, BLUR_THRESHOLD, MIN_PAGE_PIXELS, TOTAL_TOLERANCE_PCT=1.0, CONFIDENCE_REVIEW_THRESHOLD=0.80, ALLOWED_TAX_RATES=[0,5,12,18,28].
- .gitignore: .venv/, __pycache__/, .env, ana.db, uploads/, .pytest_cache/, node_modules/, frontend/dist/.
Run check_env.py now and show the real output. If Tesseract, eng or osd is missing, STOP and tell me the install steps for my OS.

# DATA MODEL
- users: id, email UNIQUE, name, password_hash (argon2, NOT NULL), role, is_active, created_at
- vendors: id, name, tax_id UNIQUE, default_currency, status (ACTIVE/INACTIVE), updated_at
- purchase_orders: id, po_number UNIQUE, vendor_id FK, currency, total, status (OPEN/CLOSED), issued_at
- po_lines: id, po_id FK, line_no, description, qty, unit_price, UNIQUE(po_id, line_no)
- invoices: id, vendor_id FK null, po_id FK null, invoice_number, invoice_date, currency, subtotal, tax_total, total, status, source_file_path, original_filename, file_sha256 (INDEXED, NOT UNIQUE), idempotency_key, created_by FK users, created_at, version INT, duplicate_of_invoice_id (self FK null), duplicate_released BOOL default false, anomaly_score null, risk_priority INT, ocr_report JSON, extraction_source (text_layer/ocr/mixed), UNIQUE(created_by, idempotency_key)
- invoice_lines: id, invoice_id FK, line_no, description, qty, unit_price, amount
- extracted_fields: id, invoice_id FK, field_name, extracted_value, confidence 0..1, corrected_value null, corrected_by null, corrected_at null. NEVER overwrite extracted_value.
- exceptions: id, invoice_id FK, rule_code, severity (INFO/WARN/BLOCKING), message, evidence JSON, resolved BOOL, run_id INT (increments per validation run), created_at
- audit_events: id, invoice_id FK, actor_id null (null = SYSTEM), actor_role, action, from_state null, to_state, comment, payload JSON, idempotency_key null, created_at, UNIQUE(invoice_id, idempotency_key)
Indexes: invoices.status, invoices(vendor_id, invoice_number), audit_events(invoice_id, created_at). Status/role/severity are strings with CHECK constraints.
AUDIT IMMUTABILITY: in db/triggers.py create (idempotently, at startup) SQLite triggers BEFORE UPDATE and BEFORE DELETE on audit_events with RAISE(ABORT, 'audit_events is append-only'). No update/delete code path anywhere. NO DELETE routes for invoices or audit events.

# ROLES AND AUTH
Roles: AP_OPERATOR, FINANCE_REVIEWER, ADMIN, AUDITOR (read-only), plus internal SYSTEM (actor_id null, cannot log in).
- AP_OPERATOR: upload, view, correct fields, submit_for_approval, retry, resubmit
- FINANCE_REVIEWER: view, approve, reject, request_correction, release_duplicate, confirm_duplicate
- ADMIN: view, seed demo data, manage users. CANNOT approve/reject.
- AUDITOR: view invoices and audit trail only.
Real JWT auth: POST /auth/login (argon2 verify, inactive users rejected), GET /auth/me. get_current_user is the single identity dependency and reads the role from the database. Routes use Depends(require_permission(...)), never raw role strings. NO signup endpoint. Errors use {"error":{"code","message"}}. 401 = missing/invalid/expired identity; 403 = not permitted; 409 = permitted but wrong state, stale version or business guard failed; 422 = validation.

# STATE MACHINE (services/workflow.py is the ONLY place status changes)
States: UPLOADED, EXTRACTED, NEEDS_REVIEW, PENDING_APPROVAL, APPROVED, REJECTED, CORRECTION_REQUESTED, DUPLICATE_HOLD, FAILED_EXTRACTION.
Initial state: UPLOADED, or DUPLICATE_HOLD when file_sha256 matches an existing non-rejected invoice (duplicate_of_invoice_id set, audit from_state null, BLOCKING exception DUPLICATE_SUSPECT with evidence). Only these transitions exist:
UPLOADED -extraction_succeeded-> EXTRACTED (SYSTEM); UPLOADED -extraction_failed-> FAILED_EXTRACTION (SYSTEM); EXTRACTED -route_to_review-> NEEDS_REVIEW (SYSTEM); EXTRACTED -flag_duplicate-> DUPLICATE_HOLD (SYSTEM); FAILED_EXTRACTION -retry-> UPLOADED (AP_OPERATOR); NEEDS_REVIEW -submit_for_approval-> PENDING_APPROVAL (AP_OPERATOR); PENDING_APPROVAL -approve-> APPROVED, -reject-> REJECTED, -request_correction-> CORRECTION_REQUESTED (FINANCE_REVIEWER); CORRECTION_REQUESTED -resubmit-> NEEDS_REVIEW (AP_OPERATOR); DUPLICATE_HOLD -release_duplicate-> UPLOADED (FINANCE_REVIEWER; sets duplicate_released=true), -confirm_duplicate-> REJECTED (FINANCE_REVIEWER).
transition(session, invoice, action, actor, comment, expected_version, idempotency_key) does everything in ONE transaction: validates the transition, checks permission, applies guards, updates the invoice (version+1, compare-and-swap), writes the audit event. write_audit() takes the caller's session and never commits.
Guards: comment mandatory for reject, request_correction, release_duplicate, confirm_duplicate; segregation of duties (approver may not be invoice.created_by nor anyone who corrected a field) -> 403 SEGREGATION_OF_DUTIES; approve blocked while any unresolved BLOCKING exception exists -> 409 BLOCKING_EXCEPTIONS_OPEN; submit_for_approval blocked while a critical field is below CONFIDENCE_REVIEW_THRESHOLD and unreviewed -> 409 LOW_CONFIDENCE_UNREVIEWED; APPROVED and REJECTED are terminal for everyone including ADMIN; stale expected_version -> 409 VERSION_CONFLICT; illegal transition -> 409 INVALID_TRANSITION; same Idempotency-Key replay returns the earlier result and writes no new audit event. A transition into UPLOADED (retry, release_duplicate) re-schedules the pipeline.

# ENDPOINTS (thin routers; logic in services)
GET /health; POST /auth/login; GET /auth/me
POST /invoices/upload (multipart; Idempotency-Key; replay returns original with 200; type pdf/png/jpg by MAGIC BYTES; MAX_UPLOAD_MB enforced while streaming; uuid server filenames, never paths from client names; SHA-256; audit event; run the pipeline via FastAPI BackgroundTasks with its own DB session)
GET /invoices (limit/offset, status filter, sorted by risk_priority desc then newest); GET /invoices/{id} (fields, lines, exceptions, matched PO with lines, duplicate original summary, audit history, ocr_report)
GET /invoices/{id}/document (streams the file; auth + view permission; never serve UPLOAD_DIR statically)
PATCH /invoices/{id}/fields (AP_OPERATOR; only in NEEDS_REVIEW or CORRECTION_REQUESTED; keeps the original, sets corrected_value/by/at; a value equal to the extracted one counts as confirmation; re-runs validation, NOT OCR; audit event with before/after)
POST /invoices/{id}/transitions {action, comment?, expected_version} + Idempotency-Key header. No separate approve/reject routes.
GET /vendors, GET /purchase-orders (with lines), GET /dashboard/summary (counts by status, exception counts by rule_code, approved/rejected totals, oldest queue items), POST /admin/seed (ADMIN + DEMO_MODE only)

# OCR / EXTRACTION PIPELINE (services/extraction + services/pipeline.py, plain sequential run_pipeline(invoice_id))
1. quality.py per page: is_blank; orientation_degrees + confidence (Tesseract OSD; auto-rotate only above a confidence threshold, else flag ORIENTATION_UNCERTAIN); skew_degrees (OpenCV minAreaRect; deskew only between a small minimum and a plausible maximum); blur_score = variance of Laplacian, flag LOW_SHARPNESS below BLUR_THRESHOLD; low-resolution flag. Store measurements even when nothing fires.
2. reader.py: PDFs with a meaningful embedded text layer use pdfplumber/PyMuPDF words (source="text_layer"). Otherwise rasterize at OCR_DPI with PyMuPDF, run the quality gate, preprocess with OpenCV (grayscale, deskew, denoise; keep the original as fallback), and run pytesseract.image_to_data for words, boxes, per-word confidence (source="ocr"). png/jpg go straight to OCR. At most OCR_MAX_PAGES (flag PAGES_TRUNCATED); page number on every word.
3. Failure (unreadable, all blank, almost no text) -> typed ExtractionError -> extraction_failed via SYSTEM with the reason in the audit payload.
4. parsing.py: regex/layout rules for supplier, supplier tax id, invoice number, date, currency, PO number, subtotal, tax, total, line items. Money via Decimal with explicit thousands/decimal handling. Store everything as UNVERIFIED. Field confidence = mean OCR word confidence of the words forming the field (text-layer baseline 0.98) x a parsing-certainty factor (1.0 unambiguous; reduced for conflicting candidates or weak patterns). Critical fields: supplier, invoice number, date, PO number, total.
5. validation.py (deterministic, Decimal, each exception has evidence JSON with invoice value, PO value, difference, rule): VENDOR_NOT_FOUND (BLOCKING; tax id first, else normalised-name RapidFuzz >= 90; 75-90 gives VENDOR_AMBIGUOUS WARN), VENDOR_INACTIVE, PO_NOT_FOUND, PO_VENDOR_MISMATCH, PO_CLOSED, CURRENCY_MISMATCH, MATH_ERROR (lines vs subtotal; subtotal+tax vs total), LINE_NOT_ON_PO (description RapidFuzz >= 85), QTY_MISMATCH (invoiced qty above REMAINING PO qty = PO qty minus qty on other non-rejected, non-held invoices; zero tolerance), PRICE_MISMATCH, TOTAL_MISMATCH (BLOCKING beyond TOTAL_TOLERANCE_PCT of the PO total; nonzero within tolerance -> INFO) all BLOCKING; TAX_RATE_UNUSUAL (WARN, implied rate not within 0.5 points of ALLOWED_TAX_RATES); LOW_CONFIDENCE_FIELD (WARN, cleared when corrected/confirmed); OCR quality flags as INFO/WARN.
6. duplicates.py: (a) same file hash at upload; (b) same vendor + normalised invoice number (uppercase, strip spaces/punctuation/leading zeros) + currency as another non-rejected invoice -> BLOCKING DUPLICATE_SUSPECT + flag_duplicate unless duplicate_released; (c) soft: same vendor, same total, date within 7 days, different number -> WARN DUPLICATE_POSSIBLE with a similarity breakdown. Never delete or auto-reject.
7. anomaly.py: per-vendor z-score of total vs the vendor's previous invoices (needs >= 5, else null); |z| >= 3 -> WARN ANOMALY_AMOUNT. Sets anomaly_score and risk_priority (from blocking count, anomaly, low-confidence count). It only orders the queue.
8. Order: extract -> extraction_succeeded -> parse/store -> match vendor and PO -> validate -> duplicate checks -> anomaly -> route_to_review (or flag_duplicate / extraction_failed) through workflow.transition as SYSTEM. Each validation run increments run_id; older exceptions are marked resolved/superseded, never deleted. Catch and record every step failure.

# SEED DATA (scripts/seed_demo.py; idempotent via natural keys; only when DEMO_MODE=true)
Users (demo-only passwords documented in README): operator@demo.com, reviewer@demo.com, reviewer2@demo.com, admin@demo.com, auditor@demo.com. 5 vendors including "Company S" (ACTIVE) and one INACTIVE. PO-DEMO-001 for Company S: 10 Laptop @ 5,000 + 5 CPU @ 10,000 = 100,000 INR. ~10 POs total incl. a split-quantity PO, a USD PO and a CLOSED PO. ~20 historical approved invoices for Company S with varied totals for the z-score.

# SAMPLE GENERATOR (scripts/make_samples.py -> samples/ + ground_truth.json; fake data only)
(a) clean text-PDF for PO-DEMO-001; (b) same invoice as an image-only scanned PDF; (c) 90-degree rotated scan; (d) 3-degree skewed scan; (e) blurred, noisy low-quality scan; (f) mismatch invoice (12 laptops, 15 CPUs, total 210,000, same unit prices); (g) byte-identical copy of (a); (h) same vendor and invoice number as (a), re-rendered; (i) blank page file.

# FRONTEND (React + TypeScript, simple and clean)
Pages: Login; Dashboard/Queue (status counts, exception-code counts, invoice table sorted by risk then newest, status filter, auto-refresh while any invoice is UPLOADED); Upload (drag and drop); Invoice Detail: status + version, extracted fields with confidence badges (red below threshold) and inline correct/confirm for AP_OPERATOR, side-by-side invoice vs PO lines with differences highlighted, exception list with severity and evidence, duplicate comparison panel, OCR quality panel (source, blur score, rotation, skew, flags), embedded source document, audit timeline, action buttons by role AND state. Buttons require a comment where mandatory, send expected_version and a fresh Idempotency-Key, and show API error codes readably. UI hides what a role cannot do, but the backend is the real enforcement. JWT in memory + sessionStorage (document the trade-off). VITE_API_URL with the /api proxy default. Visible "DEMO MODE: synthetic data only" banner.

# TESTS (pytest, per stage, real output)
Environment (tesseract available); audit UPDATE/DELETE blocked; auth (401 vs 403 vs 409 distinct, inactive user cannot log in, ADMIN/AUDITOR get 403 on transitions, document download needs auth); workflow (every allowed transition, illegal 409, terminal immutable, stale version, idempotent replay writes exactly one audit row, segregation of duties, approve blocked by BLOCKING exception, submit blocked by unreviewed low confidence, mandatory comments); upload (happy path, bad type, bad magic bytes, oversize, same-hash -> DUPLICATE_HOLD, idempotency replay); extraction on samples (text layer vs OCR chosen correctly, (c) and (d) corrected so parsed total equals ground truth, (e) gives LOW_SHARPNESS and a critical field under 0.80, blank -> FAILED_EXTRACTION, page cap); validation (a test per rule; the 12/15/210,000 case gives QTY_MISMATCH x2 and TOTAL_MISMATCH with correct evidence and NO PRICE_MISMATCH); duplicates (INV-001 vs inv 001, release does not re-hold, recurring different-number invoice not blocked); corrections (original preserved, validation re-run, audit event); money (no float). scripts/eval_extraction.py prints per-field accuracy per sample type (report honestly); scripts/eval_anomaly.py injects known outliers and prints precision and recall with an honest limits note.

# DOCS (generate from the real code at the end, concise)
../README.md (per-OS setup incl. Tesseract, venv activation commands for PowerShell and bash, run commands, demo users, the 5-scenario demo script), ../docs/state-machine.md (Mermaid + role table), data-model.md, rbac.md, matching-rules.md (each rule with a sample case), extraction.md (pipeline, quality gate, confidence vs validation, formula), anomaly-evaluation.md, decisions.md (every decision with a one-line reason, trade-offs, shortcuts, deferred items: hosting, PostgreSQL + migrations, DAG runner, RAG/agent, email intake, fuzzy duplicates beyond the soft check).

# ENGINEERING RULES
No float for money. Business rules are deterministic. OCR/model values are UNVERIFIED until validated or human-confirmed; OCR/ML give signals, rules give decisions, humans approve. Type-hint everything, short WHY docstrings, small readable files. No invented features; pick sensible defaults and record them in docs/decisions.md. Report failures honestly with real command output.

# WORKFLOW
0. Inspect the existing tree and files, summarise what exists and what you will keep/change in at most 15 lines, run check_env, then PROCEED (no approval wait unless Tesseract is missing).
1. Stage 1: config, db, models, triggers, auth/roles, workflow, audit, storage, upload/list/detail/transition endpoints, seed, tests.
2. Stage 2: OCR reading + quality gate + parsing + make_samples + eval_extraction + tests.
3. Stage 3: validation, duplicates, anomaly, pipeline wiring, corrections endpoint, dashboard endpoint, eval_anomaly + tests.
4. Stage 4: frontend; run it against the real backend and walk through the 5 scenarios with the samples.
5. Stage 5: docs, README, final full test run.
After each stage give a short summary with real test output and continue automatically unless something fails. End with how to run everything, the demo script, and anything incomplete or assumed.