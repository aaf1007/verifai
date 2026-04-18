# VerifAI Improvements

VerifAI has a solid prototype shape: a Chrome extension, a FastAPI backend, a live fact-checking pipeline, and the beginning of tests. The path to making this portfolio-impressive is to close the security gaps first, tighten the engineering signals second, and then layer on productized features that make the project feel finished.

---

## URGENT — Security

- **Task:** Rotate both API keys that are committed in `server/.env` (Groq and Gemini), then remove `server/.env` from git history using `git filter-repo`, and add `server/.env` to `.gitignore`.
  **Why it matters:** Committed secrets are a critical security incident regardless of repo visibility. Recruiters who look at git history will notice this immediately, and any key rotation you haven't done is an active exposure. This must be the first commit.

- **Task:** Fix the root `.gitignore` — the `.*` wildcard silently ignores every hidden file (including future `.env` files), and `*.md` ignores all Markdown files including `IMPROVEMENTS.md` itself. Replace both with specific entries: `server/.env`, `.env`, `.DS_Store`, `**/.DS_Store`.
  **Why it matters:** A broken `.gitignore` that accidentally excludes important files is a subtle but credibility-destroying bug visible to anyone who clones the repo.

- **Task:** Remove the three tracked `.DS_Store` files (root, `server/`, `server/app/`) from git with `git rm --cached` and add `**/.DS_Store` to `.gitignore`.
  **Why it matters:** macOS artifact files in a git repo are the fastest signal that basic repo hygiene hasn't been applied.

---

## High Priority

- **Task:** Replace all three hardcoded `http://localhost:8000` calls (in `background.ts` lines ~78 and ~120, and `ChatView.tsx` line ~121) with a single `API_BASE_URL` constant read from a WXT environment variable.
  **Why it matters:** The extension is currently locked to local development, which makes the project feel unfinished. A single config constant makes the localhost-to-production switch a one-line change — the correct architecture for any networked client.

- **Task:** Replace all `print()` calls throughout the backend (`main.py`, `fact_checker.py`, `fact_check.py`) with structured Python `logging` using `logging.getLogger(__name__)` in each module and a root handler configured in `main.py`.
  **Why it matters:** `print()` in a FastAPI service is a beginner signal. Structured logging with module names and log levels is the professional standard and is the first thing a backend reviewer checks.

- **Task:** Extract the shared fact-check pipeline into `services/fact_check_pipeline.py` so that `transcribe.py` does not directly import `fact_check` from the router (current: `transcribe.py` line 85). Both routers should call the shared service function instead.
  **Why it matters:** Recruiters will notice cleaner architecture and better separation between routing and business logic. Router-to-router imports couple two layers that should be independent.

- **Task:** Fix the `MAX_TEXT_LENGTH` mismatch: `text_cleaner.py` silently truncates at 2,000 characters but `FactCheckRequest` allows 20,000. Either align the values or emit a `logger.warning` when truncation occurs.
  **Why it matters:** Silent data loss is one of the hardest bugs to debug and signals a lack of design coordination between layers. The fix takes five minutes and prevents confusing partial-check results.

- **Task:** Replace `datetime.utcnow()` (used in `fact_check.py` and `schemas.py`) with `datetime.now(timezone.utc)`. `utcnow()` is deprecated in Python 3.12+.
  **Why it matters:** Deprecated stdlib calls generate warnings in modern Python environments and show a lack of currency with the language.

- **Task:** Introduce a shared types module at `extension/src/types/index.ts` and move `FactCheckResponse`, `ClaimAnalysis`, `ResultEntry`, `Surface`, and an `ExtensionMessage` union type into it. Remove all 6 `any` type usages in `background.ts` and `App.tsx`, and replace the `Function` type in `use-outside-click.tsx` with the correct callback signature.
  **Why it matters:** TypeScript with `any` is TypeScript turned off. A shared types module reduces drift between popup/background/content code and is the first thing a frontend reviewer looks for in a multi-file extension.

- **Task:** Create `server/requirements-dev.txt` for `pytest`, `pytest-asyncio`, and test utilities, and remove them from `server/requirements.txt`. Add the missing `pytest-asyncio` dependency to the dev file.
  **Why it matters:** `pytest` in a production requirements file is a packaging smell, and the missing `pytest-asyncio` means async test patterns currently work by accident via `asyncio.run()` workarounds.

- **Task:** Fix the current backend type issues and remove noisy debug logging in the fact-check/transcription flow.
  **Why it matters:** Clean type checks and professional logs are strong quality signals, especially for an AI-heavy project.

---

## High Impact Upgrades

- **Task:** Deploy the backend to a cloud provider (Railway, Render, or Fly.io — all free-tier capable) and wire the extension `API_BASE_URL` to the hosted endpoint for a demo mode build.
  **Why it matters:** A working live URL converts "here is my code" into "here is the product" — the difference between interesting and memorable. This is the single highest-ROI portfolio signal.

- **Task:** Add a GitHub Actions workflow at `.github/workflows/ci.yml` that runs `pytest` on the backend, `pyright` type checks on the server, and `tsc --noEmit` on the extension on every push and PR.
  **Why it matters:** A green CI badge on the README answers "how do you know it works?" before it is asked. This shows engineering discipline and gives you a strong answer when someone asks how you keep the project reliable.

- **Task:** Consolidate the three separate `browser.runtime.onMessage.addListener` calls in `background.ts` (~lines 187, 197, 207) into a single listener with a `switch` on `msg.type`, typed against the `ExtensionMessage` union from the new shared types module.
  **Why it matters:** Multiple message listeners on the same runtime is a resource and ordering bug waiting to happen. A single typed dispatcher makes the message protocol visible at a glance and is the idiomatic extension pattern.

- **Task:** Add a global React error boundary component wrapping the sidepanel root. It should catch render errors, show a minimal fallback UI, and log the boundary info to the console.
  **Why it matters:** Unhandled render errors currently crash the entire sidepanel silently with no recovery. An error boundary is a one-component addition that shows resilience thinking and prevents a panicked demo failure.

- **Task:** Add tests for the three untested critical paths: `_extract_json_from_response()` in `fact_checker.py` (the most complex parsing logic in the codebase, currently zero coverage), `_aggregate_verdict()` in `fact_check.py`, and `clean_text()` in `text_cleaner.py`. Switch the `asyncio.run()` calls in existing tests to `@pytest.mark.asyncio`.
  **Why it matters:** Tests on the code most likely to break under edge-case LLM output is a strong signal. A reviewer checking test coverage will immediately notice that the most complex function has none.

- **Task:** Add an in-page verdict overlay — after a text fact-check completes, inject a small floating badge near the selected text showing the overall verdict (TRUE / FALSE / MIXED) and a "See details" button that opens the sidepanel.
  **Why it matters:** This makes VerifAI feel like a polished product instead of a popup-only prototype and demonstrates content script injection, a non-trivial Chrome extension capability.

- **Task:** Add a Makefile at the repo root with targets: `make dev` (starts both server and extension in parallel), `make test` (runs backend pytest), `make check` (runs pyright + tsc), `make install` (installs all dependencies).
  **Why it matters:** A single `make dev` is the fastest possible onboarding experience. Reviewers who clone the repo and run everything in one command form an immediately positive impression.

- **Task:** Rename the GitHub remote repository from `hack-the-sem` to `verifai` (create a new repo named `verifai`, update the remote URL, and push).
  **Why it matters:** The remote name is visible in every link you share. `hack-the-sem` signals hackathon origin; `verifai` signals a maintained project.

- **Task:** Add a size guard in `tiktok.content.ts` before calling `captureVideoBase64` — Chrome's `runtime.sendMessage` has a message size limit, and large video frames will silently fail. Surface a user-facing error if the video exceeds the safe threshold, and keep TikTok verification clearly labeled as beta in the UI until this is fully polished.
  **Why it matters:** A crashing beta feature is worse than no feature. The size guard is a two-line defensive check; the beta label is honest product communication.

---

## Polish / Nice to Have

- **Task:** Remove dead code: `extension/src/entrypoints/content.ts` is an empty stub with no functionality; `animated-theme-toggler.tsx`, `border-beam.tsx`, `spinner-inline-3.tsx`, and `tabs.tsx` in `src/components/ui/` are imported nowhere. Delete them along with the `popup-backup/` directory.
  **Why it matters:** Dead files inflate apparent codebase complexity and suggest lack of maintenance. Reviewers who navigate the component tree will find them.

- **Task:** Consolidate to one icon library (pick `lucide-react` or `react-icons`, migrate, and remove the other) and one component library (pick `@heroui/react` or `@base-ui/react`, remove the unused one and its dead `tabs.tsx`).
  **Why it matters:** Two icon libraries and two component libraries installed simultaneously is one of the most common "built in a hurry" signals in a frontend project and unnecessarily inflates the extension bundle.

- **Task:** Replace the six duplicated gradient strings across `App.tsx`, `ChatView.tsx`, and `App.css` with references to the `--gradient` CSS variable already defined in `App.css` but never actually used.
  **Why it matters:** Duplicated style constants are a maintainability smell — and this one is especially easy to fix because the variable is already defined and just needs to be referenced.

- **Task:** Replace `key={i}` (index-based keys) in `ChatView.tsx` and `ClaimCard.tsx` with stable identifiers (UUIDs assigned at message/claim creation time).
  **Why it matters:** Index-based keys are a well-known React anti-pattern that causes subtle reconciliation bugs when items are inserted or reordered. It is a standard code-review flag.

- **Task:** Replace the template name `"wxt-react-starter"` in `extension/package.json` with `"verifai-extension"` and update the description, author, and homepage fields.
  **Why it matters:** Template leftovers weaken the portfolio impression immediately. Thirty-second fix.

- **Task:** Build out the welcome page at `extension/src/entrypoints/welcome/index.html`, currently a blank shell with an empty `<div id="root">`. Add a React entrypoint with a product explanation, a "how it works" step list, and a call to action to try the extension.
  **Why it matters:** The welcome page is the first thing new users see after installing. A blank page signals an unfinished product.

- **Task:** Replace the internal error detail strings exposed in API responses — e.g., `f"Claim extraction failed: {str(e)}"` in `fact_check.py` — with generic user-facing messages and log the full exception server-side using `logger.exception(e)`.
  **Why it matters:** Internal exception messages in API responses are a security smell flagged in any security review. Log internally, return a generic message to the client.

- **Task:** Fix the typo "relaible" → "reliable" in `server/app/prompts/fact_verification.md` line 33.
  **Why it matters:** Prompt files are effectively production configuration. Typos in prompts reflect on overall attention to detail.

- **Task:** Add rate limiting to the FastAPI backend using `slowapi` with a per-IP limit on `/api/fact-check` and `/api/transcribe-and-check`.
  **Why it matters:** An AI backend with no rate limiting will exhaust your API quota in minutes if the URL leaks. `slowapi` is a five-line addition that shows production awareness and is a strong talking point in any engineering conversation.

- **Task:** Add a `LICENSE` file (MIT recommended for a portfolio project).
  **Why it matters:** A portfolio project without a license is technically all-rights-reserved by default. A LICENSE file signals open-source awareness and makes the project properly usable by others.

- **Task:** Add screenshots or a short GIF to the main README showing the extension flow end to end: highlighting text, the sidepanel opening, and a verdict with sources.
  **Why it matters:** Visual proof makes the project easier to remember and evaluate. Most recruiters spend under thirty seconds on a README.

- **Task:** Add a Chrome keyboard shortcut (via the `commands` key in `wxt.config.ts` manifest) to trigger fact-checking on selected text without requiring the context menu.
  **Why it matters:** Power-user shortcuts differentiate "developer thought about UX" from "developer built it for themselves." It is a small addition with a visible polish payoff.

- **Task:** Improve error and retry UX in chat and fact-check flows — show a dismissible inline error banner instead of silent failure and offer a retry button for network errors.
  **Why it matters:** Better failure states make the app feel intentional and production-aware rather than fragile.
