---
name: Output Restructure and Chat UI
overview: Restructure the analysis output into three distinct sections (novelty, expected impact, pivot suggestions), add a new LLM-based expected-impact assessment separate from literature FWCI, and redesign the UI as a chat-forward Claude-like experience with guided questions.
todos: []
isProject: false
---

# Output Restructure and Chat-Forward UI

## Part 1: Output Restructuring (Backend)

### 1.1 Clarify Novelty vs Expected Impact

**Current problem:** The system conflates:

- **Literature impact** (FWCI of related papers) = what past work in the field achieved
- **Expected impact** (what we want) = predicted impact of the researcher's work if it goes through

**Schema changes** in [app/models/schemas.py](research-advisor-backend/app/models/schemas.py):

- Add `expected_impact_assessment` and `expected_impact_reasoning` to `NoveltyAssessment` (or create a new `ImpactAssessment` model)
- Keep `impact_assessment` / `impact_reasoning` as "literature impact" (from FWCI) for context
- Rename or document clearly: `impact_assessment` = "field/literature impact" (from FWCI), `expected_impact_assessment` = "predicted impact of this research"

### 1.2 Novelty Analyzer

**File:** [app/services/novelty_analyzer.py](research-advisor-backend/app/services/novelty_analyzer.py)

- Add a second LLM call (or extend existing) to produce **expected impact** of the researcher's work:
  - Input: research question, profile (skills, motivations), literature context (related papers, FWCI)
  - Output: HIGH/MEDIUM/LOW + reasoning for "If this research goes through, what impact do we expect?"
- Update `_build_impact_reasoning` to clarify: "Average FWCI of related papers in the field" (literature impact)
- When verdict is MARGINAL or SOLVED: ensure the novelty reasoning explicitly references which papers/literature may have answered or saturated the question

### 1.3 Report Generator and Output Structure

**File:** [app/services/report_generator.py](research-advisor-backend/app/services/report_generator.py)

- Change prompt to produce **three separate sections** instead of one narrative:
  1. **Novelty Analysis** – Whether the question is novel, marginal, or solved. If marginal/solved: references to literature that may have answered it ( citations from evidence)
  2. **Expected Impact Analysis** – Predicted impact of *this* research (not the literature). Use `expected_impact_assessment` and `expected_impact_reasoning`
  3. **Pivot Suggestions** – Only when PIVOT is recommended. What to pivot to, based on skills and interests
- Option: Return structured `novelty_section`, `impact_section`, `pivot_section` from the LLM (structured output) instead of one markdown narrative

### 1.4 Pivot Suggestions

- Only include pivot suggestions when recommendation is PIVOT (driven by poor novelty or expected impact)
- Already matches current logic; ensure pivot section is clearly labeled and only rendered when PIVOT

---

## Part 2: Frontend Output Display

**File:** [research-advisor-frontend/src/components/results-view.tsx](research-advisor-frontend/src/components/results-view.tsx)

**Current:** Single narrative report + NoveltySection + Pivot cards + Citations

**New structure:**

1. **Section 1: Novelty of Your Question**
  - Verdict (NOVEL / MARGINAL / SOLVED)
  - Reasoning
  - When MARGINAL/SOLVED: list of related literature with links (from `evidence`/citations)
  - Remove FWCI metrics from prominence here (or keep as secondary)
2. **Section 2: Expected Impact of Your Research**
  - Distinct block: "Expected impact of this research if it goes through"
  - Impact level (HIGH/MEDIUM/LOW) + reasoning
  - NOT the literature impact
3. **Section 3: Pivot Suggestions** (only when PIVOT)
  - What to pivot to
  - How to use skills
  - Links to gap map sources
4. **Recommendation badge** (CONTINUE / PIVOT / UNCERTAIN) at top

**Schema/API:** If backend returns structured sections, update `ResearchRecommendation` type and ResultsView to render them separately. If backend returns one markdown narrative, parse or split by headings.

---

## Part 3: Chat-Forward UI (Frontend)

### 3.1 Layout and Flow

**Target:** Claude-like single-column chat layout


| Current                 | New                                       |
| ----------------------- | ----------------------------------------- |
| Grid: Chat + FileUpload | Full-width chat                           |
| User types freely       | Assistant asks questions one at a time    |
| Separate Analyze button | Analysis auto-triggers when info complete |


### 3.2 Guided Question Flow

**Questions (in order):**

1. "What are you interested in?" (or "What are your research interests?")
2. "What is your research proposal?" (or "Describe your research question")
3. "What are your skills?"

**Flow:**

1. App loads → assistant sends first question
2. User replies with text **and/or** file upload (inline, like Claude)
3. Assistant acknowledges, sends next question
4. Repeat until all 3 answered
5. Assistant: "I have enough information. Analyzing your research..."
6. Trigger analysis (API call)
7. Display results in chat (as assistant message with ResultsView or summary)

### 3.3 Implementation Approach

**Option A (recommended):**

- Frontend-only flow: no new backend endpoints
- State: `currentStep` (0=interests, 1=proposal, 2=skills, 3=analyzing, 4=done)
- Messages: assistant questions + user responses (text + optional file attachments)
- On each user reply: advance step; if step 3 complete, call analyze and show results
- When building payload for API: convert conversation + files into `messages` + `files` for `/analyze`

**Option B:**

- Backend: `POST /chat/guided` returns next question and processes answers
- More stateful; adds session complexity

**Recommendation:** Option A. Frontend orchestrates conversation; `/analyze` stays as-is.

### 3.4 Components to Create/Modify

**New/Modified:**

- [research-advisor-frontend/src/components/chat-interface.tsx](research-advisor-frontend/src/components/chat-interface.tsx):
  - Full-width layout
  - Support for file upload **inline** (attach button or drag-drop in input area)
  - Render assistant messages (questions) and user messages (text + attached files)
  - Progress indicator (e.g. "Step 1 of 3")
- [research-advisor-frontend/src/App.tsx](research-advisor-frontend/src/App.tsx):
  - Remove grid layout
  - State: `step`, `messages`, `files`, `sessionId`, `recommendation`
  - Logic: which question to show, when to call analyze, when to show results
- [research-advisor-frontend/src/components/file-upload.tsx](research-advisor-frontend/src/components/file-upload.tsx):
  - Refactor as inline attachment for chat input (attach icon, small preview chips)
  - Or create new `ChatInputWithAttachments` component

### 3.5 Visual Styling (Claude-like)

- Single column, max-width ~768px centered
- Assistant messages: left-aligned, subtle background
- User messages: right-aligned or distinct styling
- Input bar fixed at bottom: text area + attach button
- Clean, minimal spacing

---

## Part 4: Summary of File Changes


| File                                                          | Changes                                                                                              |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `app/models/schemas.py`                                       | Add `expected_impact_assessment`, `expected_impact_reasoning`; optionally structured report sections |
| `app/services/novelty_analyzer.py`                            | Add LLM call for expected impact; sharpen novelty reasoning                                          |
| `app/services/report_generator.py`                            | Generate 3 distinct sections; use expected impact                                                    |
| `app/services/report_generator.py`                            | Update `_determine_recommendation` to use expected impact                                            |
| `research-advisor-frontend/src/components/results-view.tsx`   | Three sections: Novelty, Expected Impact, Pivot (only when PIVOT)                                    |
| `research-advisor-frontend/src/components/chat-interface.tsx` | Full-width chat; inline file attach; guided flow                                                     |
| `research-advisor-frontend/src/App.tsx`                       | Step-based flow; remove grid; trigger analyze when complete                                          |
| `research-advisor-frontend/src/types/index.ts`                | Update types for new schema fields                                                                   |
| `research-advisor-frontend/src/api/client.ts`                 | No change if analyze payload stays same                                                              |


---

## Part 5: Decision Logic Update

**Current:** PIVOT if verdict SOLVED/MARGINAL **or** impact LOW.

**New:** PIVOT if:

- Novelty poor (SOLVED/MARGINAL) **or**
- Expected impact poor (LOW)

Use `expected_impact_assessment` and `novelty.verdict` for recommendation.

---

## Dependencies

- Backend schema changes must be done before report generator and frontend
- Frontend can be developed in parallel once schema is clear
- Tests will need updates for new fields and decision logic

