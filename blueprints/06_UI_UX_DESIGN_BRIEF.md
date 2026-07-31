# NeuroSync — UI/UX Design Brief

**Version**: 1.0.0  
**Author**: Priyabrata Biswal  
**Date**: June 2026  
**Status**: ACTIVE

---

## 1. Design Philosophy

### Core Principles

> **"Intelligence made visible. Data made actionable. Complexity made simple."**

NeuroSync is not a resume scanner with a pretty dashboard. It is a **decision system** — and the UI must reflect that authority. Every screen should feel like consulting with a career strategist who has data to back every claim.

| Principle | Meaning | Anti-Pattern |
| --- | --- | --- |
| **Authority** | The UI should feel like an expert speaking | Generic pastel dashboards with no conviction |
| **Clarity** | Every number, every chart has a reason | Decorative charts with no actionable insight |
| **Action-Orientation** | Every screen ends with "what to do next" | Reports that leave users confused |
| **Progressive Disclosure** | Summary first → detail on demand | Walls of data dumped on screen |
| **Trust Through Transparency** | Show HOW scores are computed | Black-box numbers with no explanation |

### Design DNA

```text
SCA was:    Bright colors + basic cards + flat scores
NeuroSync:  Dark mode + intelligence panels + evidence-backed decisions
```

---

## 2. Visual Identity

### Color System

#### Primary Palette — Dark Intelligence Theme

| Token | Hex | Usage |
| --- | --- | --- |
| `--bg-primary` | `#0A0E1A` | Main background (deep navy-black) |
| `--bg-secondary` | `#111827` | Card backgrounds, panels |
| `--bg-elevated` | `#1A2035` | Elevated surfaces, modals |
| `--bg-glass` | `rgba(17, 24, 39, 0.7)` | Glassmorphism overlays |
| `--border-subtle` | `rgba(255, 255, 255, 0.06)` | Card borders |
| `--border-active` | `rgba(99, 102, 241, 0.3)` | Active/focused borders |

#### Accent Colors — Intelligence Signals

| Token | Hex | Usage |
| --- | --- | --- |
| `--accent-primary` | `#6366F1` | Primary actions, key metrics (Indigo) |
| `--accent-secondary` | `#8B5CF6` | Secondary highlights (Violet) |
| `--accent-glow` | `#818CF8` | Glow effects, hover states |
| `--gradient-hero` | `linear-gradient(135deg, #6366F1, #8B5CF6, #EC4899)` | Hero elements |

#### Semantic Colors — Decision Signals

| Token | Hex | Usage |
| --- | --- | --- |
| `--signal-strong` | `#10B981` | Strong fit, strengths, matched (Emerald) |
| `--signal-good` | `#3B82F6` | Good fit, positive indicators (Blue) |
| `--signal-potential` | `#F59E0B` | Potential fit, warnings (Amber) |
| `--signal-weak` | `#EF4444` | Weak/No fit, critical gaps (Red) |
| `--signal-neutral` | `#6B7280` | Neutral data, disabled states (Gray) |

#### Score Gradient

```css
/* Score ring gradient: red (0) → amber (40) → blue (65) → green (85) → emerald (100) */
--score-gradient: conic-gradient(
  from 180deg,
  #EF4444 0%,
  #F59E0B 35%,
  #3B82F6 55%,
  #10B981 80%,
  #059669 100%
);
```

### Typography

| Element | Font | Weight | Size |
| --- | --- | --- | --- |
| Headlines (H1) | `Inter` | 700 (Bold) | 32px / 2rem |
| Section headers (H2) | `Inter` | 600 (Semibold) | 24px / 1.5rem |
| Subheaders (H3) | `Inter` | 600 | 18px / 1.125rem |
| Body text | `Inter` | 400 (Regular) | 15px / 0.9375rem |
| Labels | `Inter` | 500 (Medium) | 13px / 0.8125rem |
| Scores / Numbers | `JetBrains Mono` | 700 | 28px / 1.75rem |
| Code / Technical | `JetBrains Mono` | 400 | 14px / 0.875rem |

**Google Fonts import:**

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
```

### Spacing System

```text
--space-xs:  4px
--space-sm:  8px
--space-md:  16px
--space-lg:  24px
--space-xl:  32px
--space-2xl: 48px
--space-3xl: 64px
```

### Border Radius

```text
--radius-sm:  6px    (small elements, tags)
--radius-md:  10px   (cards, inputs)
--radius-lg:  16px   (panels, modals)
--radius-xl:  24px   (hero sections)
--radius-full: 9999px (pills, avatars)
```

### Shadows & Effects

```css
/* Card shadow */
--shadow-card: 0 4px 20px rgba(0, 0, 0, 0.3);

/* Elevated shadow */
--shadow-elevated: 0 8px 32px rgba(0, 0, 0, 0.5);

/* Glow effect (for primary actions) */
--glow-primary: 0 0 20px rgba(99, 102, 241, 0.3);

/* Glassmorphism */
--glass: backdrop-filter: blur(16px) saturate(180%);
```

---

## 3. User Journey

### Flow 1: First-Time Analysis (Primary Journey)

```text
Landing Page
     │
     │  "Analyze Your Career Fit"
     ▼
Upload/Paste Screen
     │
     │  Paste resume + JD (or upload PDF)
     │  Click "Analyze"
     ▼
Loading State (2-5 seconds)
     │
     │  Animated neural network visualization
     │  Progress indicators per component
     ▼
Results Dashboard
     │
     ├── Hero: Score Ring (animated 0→72)
     │   + Decision Badge ("Apply with Preparation")
     │   + Confidence bar
     │
     ├── Skills Panel: Matched vs Missing
     │   + Category breakdown
     │   + Proficiency indicators
     │
     ├── Gap Intelligence Panel
     │   + Priority-sorted gaps
     │   + Reasoning expandable
     │   + Learning time estimates
     │
     ├── Improvement Path
     │   + ROI-ranked skill cards
     │   + "What If" simulation buttons
     │
     ├── Strengths & Weaknesses
     │   + Evidence-backed claims
     │
     └── Action Bar
         + "Learn {top_skill}" CTA
         + "Save Analysis"
         + "Give Feedback"
```

### Flow 2: Feedback Loop

```text
After interview/rejection
     │
     ▼
Click "Report Outcome"
     │
     │  Select: Got Interview / Hired / Rejected / Ghosted
     │  Optional: notes
     ▼
Confirmation
     │
     │  "Thanks! This helps us improve."
     │  Show updated system accuracy stats
     ▼
Return to Dashboard
```

### Flow 3: Simulation Playground (Phase 2)

```text
From Results Dashboard
     │
     │  Click "What if I learn Kubernetes?"
     ▼
Simulation View
     │
     │  Side-by-side comparison:
     │  Current state → Projected state
     │
     │  Score: 62 → 78 (+16)
     │  Fit: Potential → Good
     │  Shortlist: 35% → 64%
     │
     │  "Add another skill to simulate"
     ▼
Stacked simulations
     │
     │  K8s + Terraform: 62 → 84
     │  Visual skill graph showing coverage
```

---

## 4. Dashboard Layout

### Results Dashboard — Desktop (1440px)

```text
┌─────────────────────────────────────────────────────────────────┐
│  NeuroSync ■                                    [User] [Logout] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    HERO SECTION                           │  │
│  │                                                           │  │
│  │   ┌─────────┐   OVERALL SCORE        DECISION            │  │
│  │   │         │                                             │  │
│  │   │  ◉ 72   │   ████████░░  72/100   🟡 APPLY WITH      │  │
│  │   │         │                           PREPARATION       │  │
│  │   └─────────┘   Confidence: 78%      Shortlist: 55%      │  │
│  │     Score Ring                                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────────────┐    │
│  │  SKILLS MATCHED      │  │  GAP INTELLIGENCE            │    │
│  │                      │  │                              │    │
│  │  ✅ Python (0.92)    │  │  🔴 Kubernetes  CRITICAL     │    │
│  │  ✅ Docker (0.85)    │  │     "Mentioned 4× in JD..." │    │
│  │  ✅ React  (0.78)    │  │     ⏱ 3-4 weeks             │    │
│  │  ✅ SQL    (0.71)    │  │                              │    │
│  │  ✅ AWS    (0.68)    │  │  🟠 Terraform   HIGH        │    │
│  │  ✅ Git    (0.95)    │  │     "Infrastructure as..."  │    │
│  │                      │  │     ⏱ 2-3 weeks             │    │
│  │  6 matched / 8 req.  │  │                              │    │
│  │  Overlap: 75%        │  │  🟡 GraphQL     MEDIUM      │    │
│  └──────────────────────┘  └──────────────────────────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  IMPROVEMENT PATH (ROI-Ranked)                           │  │
│  │                                                           │  │
│  │  #1 ⭐ Kubernetes   +14 pts   3-4 weeks   [Simulate]    │  │
│  │  #2    Terraform    +8 pts    2-3 weeks   [Simulate]    │  │
│  │  #3    GraphQL      +4 pts    1-2 weeks   [Simulate]    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────┐  ┌────────────────────────────────┐   │
│  │  STRENGTHS          │  │  WEAKNESSES                    │   │
│  │                     │  │                                │   │
│  │  ✦ Strong backend   │  │  ⚠ Missing orchestration      │   │
│  │    fundamentals     │  │    skills (K8s, Terraform)     │   │
│  │  ✦ Production AWS   │  │  ⚠ No CI/CD evidence in       │   │
│  │    experience       │  │    resume                      │   │
│  └─────────────────────┘  └────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  [📊 Full Evidence]  [🔄 Report Outcome]  [💾 Save]     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ── Processing: 423ms │ Taxonomy v1.0 │ Engine v1.0 ──────────│
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Mobile Experience

### Breakpoints

| Breakpoint | Width | Layout |
| --- | --- | --- |
| Mobile | < 640px | Single column, stacked cards |
| Tablet | 640-1024px | 2-column where beneficial |
| Desktop | 1024-1440px | Full dashboard layout |
| Wide | > 1440px | Max-width 1440px, centered |

### Mobile Priorities

1. **Score + Decision** — always visible first
2. **Top 3 gaps** — collapsed with expand
3. **#1 Improvement action** — single hero CTA
4. **Skills** — horizontal scroll chips
5. **Evidence** — behind "Show details" accordion

### Mobile-Specific Patterns

- Score ring: 120px diameter (vs 160px desktop)
- Cards: full-width with 16px horizontal padding
- Gap cards: collapsed by default, tap to expand reasoning
- Bottom navigation bar (fixed): Dashboard | Analyze | History | Profile
- Pull-to-refresh for analysis list

---

## 6. Component Library

### Score Ring

```text
Animated circular gauge
- Starts at 0, animates to final score
- Color follows score gradient
- Center: large number (JetBrains Mono, 28px)
- Ring: 8px stroke, rounded caps
- Animation: 1.5s ease-out
- Glow effect at score position
```

### Decision Badge

```text
Rounded pill with semantic color
- STRONG_APPLY:          Green bg, white text, ✅ icon
- APPLY:                 Blue bg, white text, 👍 icon
- APPLY_WITH_PREPARATION: Amber bg, dark text, ⚡ icon
- UPSKILL_THEN_APPLY:   Orange bg, dark text, 📚 icon
- DO_NOT_APPLY:          Red bg, white text, ❌ icon
```

### Skill Chip

```text
Rounded pill (radius-full)
- Background: bg-secondary
- Border: 1px solid border-subtle
- Left dot: category color
- Text: skill canonical name (13px, medium)
- Right: proficiency mini-bar (4px tall)
- Hover: border-active + glow
- Click: expands to show evidence
```

### Gap Card

```text
Card (radius-md, bg-secondary)
- Left stripe: priority color (4px)
  - CRITICAL: signal-weak (red)
  - HIGH: amber
  - MEDIUM: signal-good (blue)
  - LOW: signal-neutral (gray)
- Header: skill name + priority badge
- Body (collapsed): one-line reasoning preview
- Body (expanded): full reasoning + learning time + related skills
- Footer: "Simulate" button
```

### Improvement Row

```text
Horizontal card in list
- Rank badge (#1 ⭐, #2, #3)
- Skill name (bold)
- Impact: "+14 pts" in signal-strong
- Time: "3-4 weeks" in muted
- CTA: "Simulate" button (accent-primary)
```

### Evidence Accordion

```text
Expandable section
- Header: "Why this score?" or "Full evidence chain"
- Content: List of EvidenceItem cards
  - Source badge (semantic | extraction | gap)
  - Claim text
  - Weight bar (visual percentage)
  - Confidence dot
```

### Loading State

```text
Neural network animation
- Connected nodes pulsing
- Labels showing current step:
  "Extracting skills..." → "Computing similarity..." → "Analyzing gaps..." → "Making decision..."
- Progress bar (determinate if possible)
- Estimated time: "~3 seconds"
```

---

## 7. Interaction Patterns

### Micro-Animations

| Element | Animation | Duration | Trigger |
| --- | --- | --- | --- |
| Score ring fill | Counter 0→N + ring fill | 1.5s ease-out | Page load |
| Decision badge | Fade in + subtle bounce | 0.5s | After score |
| Skill chips | Stagger fade in (50ms offset) | 0.3s each | Section visible |
| Gap cards | Slide up + fade in | 0.4s stagger | Section visible |
| Improvement rows | Slide in from right | 0.3s stagger | Section visible |
| Simulate button → result | Card flip / morph | 0.6s | Click |
| Hover on card | Subtle lift (translateY: -2px) + glow | 0.2s | Hover |

### Hover Effects

- Cards: lift + shadow increase + border glow
- Buttons: background lightens + glow pulse
- Skill chips: border → accent-primary + tooltip with evidence
- Gaps: expand preview of reasoning

### Scroll Behavior

- Sticky header with navigation
- Smooth scroll between sections
- Intersection Observer for section animations (animate on scroll into view)
- Parallax-subtle on hero score section

---

## 8. Accessibility

### Standards

- WCAG 2.1 AA compliance minimum
- All interactive elements keyboard-focusable
- Focus-visible rings (accent-primary, 2px)
- Screen reader labels for all charts and scores
- Color is never the ONLY signal — always paired with text/icon

### Color Contrast

| Combination | Contrast Ratio | Pass? |
| --- | --- | --- |
| White text on bg-primary (#0A0E1A) | 18.1:1 | ✅ AAA |
| White text on bg-secondary (#111827) | 15.4:1 | ✅ AAA |
| accent-primary on bg-primary | 5.2:1 | ✅ AA |
| signal-strong on bg-secondary | 6.8:1 | ✅ AA |
| signal-weak on bg-secondary | 4.6:1 | ✅ AA |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
```

---

## 9. Page Inventory (Planned)

| # | Page | Route | Priority |
| --- | --- | --- | --- |
| 1 | Landing / Hero | `/` | Phase 2 |
| 2 | Analyze (Upload) | `/analyze` | Phase 2 |
| 3 | Results Dashboard | `/results/:id` | Phase 2 |
| 4 | Simulation Playground | `/simulate/:id` | Phase 3 |
| 5 | Career Roadmap | `/roadmap` | Phase 3 |
| 6 | History / Past Analyses | `/history` | Phase 3 |
| 7 | Profile / Settings | `/profile` | Phase 3 |
| 8 | Market Intelligence | `/market` | Phase 4 |
| 9 | Career Command Center | `/career` | Phase 2-3 |
| 10 | API Documentation | `/docs` (Swagger) | Phase 1 ✅ |

---

## 9.5. Career Command Center (Phase 2-3) ★ NEW

> The Career Command Center is where Human State Intelligence becomes visible. It transforms NeuroSync from a one-shot analyzer into a continuous career companion.

### Dashboard Widgets

```text
┌─────────────────────────────────────────────────────────────────┐
│  NeuroSync ■  Career Command Center         [User] [Settings]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │  CAREER      │ │  CONFIDENCE  │ │  GROWTH      │           │
│  │  MOMENTUM    │ │  SCORE       │ │  VELOCITY    │           │
│  │              │ │              │ │              │           │
│  │   ◉ 0.76    │ │   ◉ 0.68    │ │  5.7 pts/mo  │           │
│  │   ↑ +0.12   │ │   ↑ +0.26   │ │  ↑ trending  │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │  BURNOUT     │ │  INTERVIEW   │ │  CAREER      │           │
│  │  RISK        │ │  READINESS   │ │  READINESS   │           │
│  │              │ │              │ │              │           │
│  │   🟢 0.15   │ │   🟡 0.62   │ │   🟡 0.58   │           │
│  │   LOW        │ │   PREPARING  │ │   WAIT 3 WKS │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  BEHAVIOR TIMELINE                                        │  │
│  │  ═══════●═══════●═══════●═══════●═══════●════►            │  │
│  │       Mon     Tue     Wed     Thu     Fri               │  │
│  │  engagement  0.82    0.78    0.45    0.34    0.67        │  │
│  │  focus       HIGH    HIGH    LOW     LOW     MED         │  │
│  │  sessions    2       2       0       1       2           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌────────────────────┐  ┌─────────────────────────────────┐   │
│  │  CAREER XP         │  │  AGENT RECOMMENDATIONS          │   │
│  │                    │  │                                 │   │
│  │  Level 12          │  │  💡 "Focus on Docker today —   │   │
│  │  ████████████░░░░  │  │     K8s can wait until         │   │
│  │  2,450 / 3,000 XP  │  │     engagement recovers"       │   │
│  │                    │  │                                 │   │
│  │  +45 XP today      │  │  📊 "Your momentum is up 12%  │   │
│  │  Streak: 5 days 🔥 │  │     since last week"           │   │
│  └────────────────────┘  └─────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  📷 CAMERA PANEL                          [Disabled]      │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Camera is DISABLED. Enable to add attention and   │  │  │
│  │  │  focus signals to your career state.               │  │  │
│  │  │  [Enable Camera] — requires explicit consent       │  │  │
│  │  │                                                    │  │  │
│  │  │  • No raw video is stored — ever                   │  │  │
│  │  │  • Only derived signals (attention, focus) saved   │  │  │
│  │  │  • Images deleted immediately after inference      │  │  │
│  │  │  • You can disable at any time                     │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Widget Color Coding

| Metric | Green (0.7+) | Amber (0.4-0.7) | Red (<0.4) |
| --- | --- | --- | --- |
| Momentum | Strong progress | Moderate | Stalling |
| Confidence | High self-efficacy | Building | Needs support |
| Burnout Risk | LOW (<0.3) | MEDIUM (0.3-0.7) | HIGH (>0.7) ← inverted |
| Interview Readiness | Ready | Preparing | Not ready |
| Career Readiness | Apply now | Wait | Significant gaps |

### Camera Panel Rules

- **Disabled by default** — always
- **Explicit consent required** — modal with privacy policy
- **No raw video stored** — frames deleted immediately after inference
- **Only derived signals** — attention, focus, engagement scores
- **Revocable** — user can disable at any time
- **GDPR-ready** — all camera data is ephemeral

---

## 10. Design Inspiration & References

### Aesthetic References

| Reference | What to Learn |
| --- | --- |
| **Linear.app** | Clean dark UI, subtle animations, authority |
| **Vercel Dashboard** | Card layouts, dark mode, data density |
| **Raycast** | Glassmorphism, keyboard-first, polish |
| **GitHub Copilot** | Intelligence UI, progressive disclosure |
| **Stripe Dashboard** | Data visualization, clarity, trust |

### What NeuroSync UI Should Feel Like

- Not like a student project (no Bootstrap defaults, no bright random colors)
- Not like a corporate dashboard (no boring charts, no gray-on-gray)
- Like a **premium AI product** that a recruiter or developer would pay for
- Like consulting with a data-backed career strategist
- **Dark, clean, intelligent, confident**

---

*This document defines what NeuroSync feels like. Frontend implementation follows these specifications exactly.*
