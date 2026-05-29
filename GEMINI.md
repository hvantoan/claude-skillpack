## Rule: CLAUDE

# GEMINI.md

This file provides Claude Code guidance for ClaudeKit Engineer. The CK CLI installs it with the rest of the AI-facing rules under `GEMINI.md`.

## Role & Responsibilities

Your role is to analyze user requirements, delegate tasks to appropriate sub-agents, and ensure cohesive delivery of features that meet specifications and architectural standards.

## Workflows

- Primary workflow: `./GEMINI.md`
- Development rules: `./GEMINI.md`
- Orchestration protocols: `./GEMINI.md`
- Documentation management: `./GEMINI.md`
- And other workflows: `./GEMINI.md*`

**IMPORTANT:** Analyze the skills catalog and activate the skills that are needed for the task during the process.
**IMPORTANT:** DO NOT modify skills in `~/.claude/skills` directory directly. **MUST** modify skills in this current working directory. Unless you are asked to do so.
**IMPORTANT:** You must follow strictly the development rules in `./GEMINI.md` file.
**IMPORTANT:** Before you plan or proceed any implementation, always read the `./README.md` file first to get context.
**IMPORTANT:** Sacrifice grammar for the sake of concision when writing reports.
**IMPORTANT:** In reports, list any unresolved questions at the end, if any.

## Git

**DO NOT** use `chore` and `docs` in commit messages of file changes in `.claude` directory.

## Hook Response Protocol

### Privacy Block Hook (`@@PRIVACY_PROMPT@@`)

When a tool call is blocked by the privacy-block hook, the output contains a JSON marker between `@@PRIVACY_PROMPT_START@@` and `@@PRIVACY_PROMPT_END@@`. **You MUST use the `AskUserQuestion` tool** to get proper user approval.

**Required Flow:**

1. Parse the JSON from the hook output
2. Use `AskUserQuestion` with the question data from the JSON
3. Based on user's selection:
   - **"Yes, approve access"** → Use `bash cat "filepath"` to read the file (bash is auto-approved)
   - **"No, skip this file"** → Continue without accessing the file

**Example AskUserQuestion call:**
```json
{
  "questions": [{
    "question": "I need to read \".env\" which may contain sensitive data. Do you approve?",
    "header": "File Access",
    "options": [
      { "label": "Yes, approve access", "description": "Allow reading .env this time" },
      { "label": "No, skip this file", "description": "Continue without accessing this file" }
    ],
    "multiSelect": false
  }]
}
```

**IMPORTANT:** Always ask the user via `AskUserQuestion` first. Never try to work around the privacy block without explicit user approval.

## Python Scripts (Skills)

When running Python scripts from `.agents/skills/`, use the venv Python interpreter:
- **Linux/macOS:** `.agents/skills/.venv/bin/python3 scripts/xxx.py`
- **Windows:** `.claude\skills\.venv\Scripts\python.exe scripts\xxx.py`

This ensures packages installed by `install.sh` (google-genai, pypdf, etc.) are available.

**IMPORTANT:** When scripts of skills failed, don't stop, try to fix them directly.

## [IMPORTANT] Consider Modularization
- If a code file exceeds 200 lines of code, consider modularizing it
- Check existing modules before creating new
- Analyze logical separation boundaries (functions, classes, concerns)
- Use kebab-case naming with long descriptive names, it's fine if the file name is long because this ensures file names are self-documenting for LLM tools (Grep, Glob, Search)
- Write descriptive code comments
- After modularization, continue with main task
- When not to modularize: Markdown files, plain text files, bash scripts, configuration files, environment variables files, etc.

## Documentation Management

We keep all important docs in `.` folder and keep updating them, structure like below:

```
./docs
├── project-overview-pdr.md
├── code-standards.md
├── codebase-summary.md
├── design-guidelines.md
├── deployment-guide.md
├── system-architecture.md
└── project-roadmap.md
```

**IMPORTANT:** *MUST READ* and *MUST COMPLY* all *INSTRUCTIONS* in `GEMINI.md`, especially *WORKFLOWS* section is *CRITICALLY IMPORTANT*, this rule is *MANDATORY. NON-NEGOTIABLE. NO EXCEPTIONS. MUST REMEMBER AT ALL TIMES!!!*
---

## Rule: orchestration-protocol

# Orchestration Protocol

## Delegation Context (MANDATORY)

When spawning subagents via subtask delegation, **ALWAYS** include in prompt:

1. **Work Context Path**: The git root of the PRIMARY files being worked on
2. **Reports Path**: `{work_context}/plans/reports/` for that project
3. **Plans Path**: `{work_context}` for that project

**Example:**
```
Task prompt: "Fix parser bug.
Work context: /path/to/project-b
Reports: /path/to/project-b/plans/reports/
Plans: /path/to/project-b/plans/"
```

**Rule:** If CWD differs from work context (editing files in different project), use the **work context paths**, not CWD paths.
---

#### Sequential Chaining
Chain subagents when tasks have dependencies or require outputs from previous steps:
- **Planning → Implementation → Simplification → Testing → Review**: Use for feature development (tests verify simplified code)
- **Research → Design → Code → Documentation**: Use for new system components
- Each agent completes fully before the next begins
- Pass context and outputs between agents in the chain

#### Parallel Execution
Spawn multiple subagents simultaneously for independent tasks:
- **Code + Tests + Docs**: When implementing separate, non-conflicting components
- **Multiple Feature Branches**: Different agents working on isolated features
- **Cross-platform Development**: iOS and Android specific implementations
- **Careful Coordination**: Ensure no file conflicts or shared resource contention
- **Merge Strategy**: Plan integration points before parallel execution begins
---

## Subagent Status Protocol

Subagents MUST report one of these statuses when completing work:

| Status | Meaning | Controller Action |
|--------|---------|-------------------|
| **DONE** | Task completed successfully | Proceed to next step (review, next task) |
| **DONE_WITH_CONCERNS** | Completed but flagged doubts | Read concerns → address if correctness/scope issue → proceed if observational |
| **BLOCKED** | Cannot complete task | Assess blocker → provide context / break task / escalate to user |
| **NEEDS_CONTEXT** | Missing information to proceed | Provide missing context → re-dispatch |

### Handling Rules

- **Never** ignore BLOCKED or NEEDS_CONTEXT — something must change before retry
- **Never** force same approach after BLOCKED — try: more context → simpler task → more capable model → escalate
- **DONE_WITH_CONCERNS** about file growth or tech debt → note for future, proceed now
- **DONE_WITH_CONCERNS** about correctness → address before review
- If subagent fails 3+ times on same task → escalate to user, don't retry blindly

### Reporting Format

Subagents should end their response with:

```
**Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
**Summary:** [1-2 sentence summary]
**Concerns/Blockers:** [if applicable]
```
---

## Context Isolation Principle

**Subagents receive only the context they need.** Never pass full session history.

### Rules

1. **Craft prompts explicitly** — Provide task description, relevant file paths, acceptance criteria. Not "here's what we discussed."
2. **No session history** — Subagent gets fresh context. Summarize relevant decisions, don't replay conversation.
3. **Scope file references** — List specific files to read/modify. Not "look at the codebase."
4. **Include plan context** — If working from a plan, provide the specific phase text, not the entire plan.
5. **Preserve controller context** — Coordination work stays in main agent. Don't dump coordination details into subagent prompts.

### Prompt Template

```
Task: [specific task description]
Files to modify: [list]
Files to read for context: [list]
Acceptance criteria: [list]
Constraints: [any relevant constraints]
Plan reference: [phase file path if applicable]

Work context: [project path]
Reports: [reports path]
```

### Anti-Patterns

| Bad | Good |
|-----|------|
| "Continue from where we left off" | "Implement X feature per spec in phase-02.md" |
| "Fix the issues we discussed" | "Fix null check in auth.ts:45, root cause: missing validation" |
| "Look at the codebase and figure out" | "Read src/api/routes.ts and add POST  endpoint" |
| Passing 50+ lines of conversation | 5-line task summary with file paths |
---

## Agent Teams (Optional)

For multi-session parallel collaboration, activate the `` skill.
Not part of the default orchestration workflow. See `.agents/skills/team/SKILL.md` for templates, decision criteria, and spawn instructions.
---

## Rule: review-audit-self-decision

# GEMINI.md Rules Summary — Review/Audit + Comments + Self-Decision

## 1. Verified Decisions Are Sticky — Audit Does Not Auto-Reverse

- Once a decision is verified (read source, ran tests, empirical experiment), lock it with a source note: `verified by {file:line}` or `verified by test {name}`.
- An audit/red-team counter-argument **alone is insufficient** to revise. Only revise when:
  - Audit finds a **new** issue the verification missed (state the issue + why prior check missed it).
  - Or context changed since verification (codebase moved, business decision changed).
- After verifying, prune stale risk rows / unresolved questions from reports.
- Surface contradictions on verified decisions to user as: "audit says X, but Y is verified by {source} — does the audit bring new data to justify a reverse?" Do NOT silently flip.

## 2. Validate Audit Findings Against Real Threat Model

Before applying a finding flagged "too narrow / too loose / risky":

1. Identify what the code **actually stores/protects**.
2. Walk each scenario the reviewer flagged through that lens. Does it actually produce the bad outcome? Often "theoretically yes, practically no".
3. Separate real risks from abstract worries. Real → fix; non-real → document rationale; borderline → ask user.
4. Look for the failure mode the reviewer missed — often the real bug sits one step away from what was flagged.

Anti-pattern: accepting every "widen/harden/add-check" recommendation without tracing it to a real failure mode.

## 3. Guard User Decisions Against Audit/YAGNI Drift

**NEVER silently reverse decisions the user has already confirmed.**

Before any cut/change from audit:

1. **Trace before cutting:** check if user explicitly chose that value/design.
2. **Categorize:**
   - ✅ Safe to apply: cuts of items Claude proposed that user never explicitly confirmed.
   - ⚠️ Must confirm first: anything touching user's explicit answer — thresholds, scope, library, schema, phase, feature inclusion/exclusion.
   - 🚫 Never auto-reverse: business decisions (pricing, timing, scope boundaries, compliance).
3. **Surface reversals:** present (a) user's original decision verbatim, (b) audit reasoning, (c) trade-off, (d) explicit ask "keep / change per audit / hybrid?". Do NOT apply.
4. **Document drift:** annotate cuts with reason + user-confirmation trail.
5. **Auditor bias awareness:** audits lean YAGNI/minimalism — they are **input to user**, not orders to Claude.

Red flags: changing a numeric threshold user picked, removing a column/field user mentioned, swapping library, moving scope across phases, cutting a feature user confirmed.

Rule of thumb: if unsure whether a cut reverses user intent, ask. Cost of 1 clarifying question ≪ cost of silent regression at demo.

## 4. Scout-First, Ask-Second (Confidence Score)

For any question answerable by grep/read on the codebase:

1. **Scout first:** grep, read live code, check current state.
2. **Self-rate confidence (0–100%):**
   - **≥ ~85%** → answer directly with `path:line` citation.
   - **< 85%** → ask user.
3. **Only ask when:**
   - Confidence < 85% (missing data, ambiguous).
   - Real conflict between 2+ sources (not a stale note already verified).
   - Anomaly requiring user judgment (business decision, UX trade-off, scope expansion).
   - High-reversibility risk (destructive op, breaking change, deploy-affecting).

Anti-pattern: asking what grep can answer in 5s.
Good pattern: scout → "verified at `file:line`, confidence 95%, applying X" — verified + concise.

## 5. Code Comments & Artifact Naming — No Plan References

Code comments and file names (including SQL migrations) **must not reference plan artifacts**: phase numbers, finding codes (F1, F13, Y1, CU2…), audit labels (audit A4), red-team labels, brainstorm sections (§5.4), plan taxonomy.

**Why:** plan headers change/get renumbered/disappear → references become unresolvable noise. The *reason* for code (invariant, race, trade-off) must be stable and self-contained.

### Rules

- **Explain the why, not the origin.** Write "org-scoped advisory lock serializes concurrent reassigns" — NOT "per F13 advisory-lock fix".
- **Migration filenames:** domain slug only — `000003_polymorphic_permission_groups.up.sql` (NOT `000003_phase_0a_...`).
- **Test names:** describe scenario — `TestReassignPrimaryDept_Concurrent` (NOT `_F13`).
- **Commit messages:** describe the change, not the finding code.
- Plan refs belong in `plans/…XX-*.md` and PR descriptions, not in code.

### Allowed in code

- Function/symbol names in the same codebase.
- Stable external IDs: RFC numbers, PostgreSQL SQLSTATE, CVE IDs, durable issue numbers.
---

## Open Questions

None — all 5 rules are clear. Flag if any rule should be expanded further.
---

## Rule: skill-domain-routing

# Skill Domain Routing

When a user's task involves a specific domain, use these decision trees to pick the RIGHT skill based on user intent.

## Frontend / UI

```
User wants to...
├── Replicate a mockup, screenshot, or video    → /ck:frontend-design
├── Build React/TS components with best practices → /ck:frontend-development
├── Style with Tailwind CSS + shadcn/ui          → /ck:ui-styling
├── Choose colors, fonts, layout, design system  → /ck:ui-ux-pro-max
├── Audit existing UI for accessibility/UX       → /ck:web-design-guidelines
├── Apply React performance patterns             → /ck:react-best-practices
├── Build with Stitch (AI design generation)     → /ck:stitch
├── Create 3D / WebGL / Three.js experience      → /ck:threejs
├── Write GLSL shaders / procedural graphics     → /ck:shader
└── Build programmatic video with Remotion       → /ck:remotion
```

## Codebase Understanding

```
User wants to...
├── Quick file search, locate specific code     → /ck:scout
├── Onboard a new repo / dump codebase for LLM  → /ck:repomix
├── Semantic go-to-definition, find-usages      → /ck:gkg
└── Build a queryable knowledge graph from code → /ck:graphify
```

## Backend / API

```
User wants to...
├── Build REST/GraphQL API (NestJS, FastAPI, Django) → /ck:backend-development
├── Add authentication (OAuth, JWT, passkeys)        → /ck:better-auth
└── Integrate payments (Stripe, Polar, SePay)        → /ck:payment-integration
```

## Database

```
User wants to...
├── Design schemas, write SQL/NoSQL queries     → /ck:databases
├── Optimize indexes, migrations, replication   → /ck:databases
└── Add auth with database-backed sessions      → /ck:better-auth
```

## Infrastructure / Deployment

```
User wants to...
├── Deploy to Vercel, Netlify, Railway, Fly.io   → /ck:deploy
└── Docker, Kubernetes, CI/CD pipelines, GitOps   → /ck:devops
```

## Security

```
User wants to...
├── STRIDE/OWASP security audit with auto-fix    → /ck:security
├── Scan for secrets, vulnerabilities, OWASP patterns → /ck:security-scan
└── OSINT / CTI / threat-intel investigation     → /ck:cti-expert
```

## AI / LLM

```
User wants to...
├── Optimize context, agent architecture, memory → /ck:context-engineering
├── Generate llms.txt, LLM-friendly docs         → /ck:llms
├── Build AI agents with Google ADK              → /ck:google-adk-python
├── Generate/analyze images, audio, video with AI → /ck:ai-multimodal
└── Learn the autoresearch pattern / find the right family member → /ck:autoresearch
```

## MCP (Model Context Protocol)

```
User wants to...
├── Build a new MCP server                       → /ck:mcp-builder
├── Convert existing code into CLI/MCP server    → /ck:agentize
├── Discover and execute MCP tools               → /ck:use-mcp
└── Target a real Chrome profile through browser MCP → /ck:chrome-profile
```

## Testing / Browser

```
User wants to...
├── Run test suites, coverage reports, TDD          → /ck:test
├── Test strategy + Playwright/Vitest/k6 runner     → /ck:web-testing
├── Drive the user's real Chrome profile/cookies    → /ck:chrome-profile
└── Browser automation/testing without real user cookies → /ck:agent-browser
```

## Media

```
User wants to...
├── Process video/audio (FFmpeg), images (ImageMagick) → /ck:media-processing
└── Generate AI images (Imagen, Nano Banana)           → /ck:ai-artist
```

## Documentation

```
User wants to...
├── Update project docs (codebase-summary, PDR)   → /ck:docs
├── Search library/framework docs (context7)      → /ck:docs-seeker
├── Discover skills by capability / "is there a skill" → /ck:find-skills
├── Build docs site with Mintlify                 → /ck:mintlify
├── Inline doc diagrams (Mermaid v11)             → /ck:mermaidjs-v11
├── Publish-grade SVG/PNG diagrams (architecture) → /ck:tech-graph
├── Read long-form docs / RFCs / specs in browser → /ck:markdown-novel-viewer
├── Generate session hand-off / EOD summary       → /ck:watzup
└── Sprint retrospective from git history         → /ck:retro
```

## Documents / Office Files

```
User wants to...
├── Create / edit / extract from .docx (Word)         → /ck:docx
├── Create / edit / extract from .pdf (forms, tables) → /ck:pdf
├── Create / edit / extract from .pptx (PowerPoint)   → /ck:pptx
└── Create / edit / extract from .xlsx (spreadsheets) → /ck:xlsx
```

## Content / Copy

```
User wants to...
├── Write landing page, email, headline copy     → /ck:copywriting
├── Brand identity, logos, banners               → /ckm:design
└── Create Excalidraw diagrams                   → /ck:excalidraw
```

## Frameworks

```
User wants to...
├── Next.js App Router, RSC, Turborepo           → /ck:web-frameworks
├── TanStack Start/Form/AI                       → /ck:tanstack
├── React Native, Flutter, SwiftUI               → /ck:mobile-development
└── Shopify apps, Polaris, Liquid templates       → /ck:shopify
```

## Usage Notes

- Pick ONE skill per distinct user intent
- If a task spans two domains (e.g. "build + deploy"), suggest the primary skill and mention the secondary
- Domain skills combine with core workflow: `` → domain skill → ``
- Skills not listed here are either core workflow skills (see `skill-workflow-routing.md`) or utility skills activated on demand (e.g. ``, ``, ``)

