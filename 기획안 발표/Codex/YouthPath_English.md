---
marp: true
theme: default
paginate: false
size: 16:9
style: |
  section {
    font-family: Aptos, Arial, sans-serif;
    background: #FAFCFF;
    color: #162033;
    padding: 44px 54px;
  }
  h1 {
    color: #0E2559;
    font-size: 42px;
    letter-spacing: 0;
    margin: 0 0 24px;
  }
  h2 {
    color: #184ED2;
    font-size: 22px;
    margin: 0 0 16px;
  }
  p, li {
    font-size: 22px;
    line-height: 1.35;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 18px;
  }
  th {
    background: #1446AF;
    color: white;
    padding: 12px;
  }
  td {
    border: 1px solid #BFD4F5;
    padding: 11px;
    background: white;
  }
---

# YouthPath

## Total Assistant for Youth Career Entry

A generative AI service that connects policy matching, job recommendations, resume coaching, and deadline management.

Policy Matching | Job Search | Resume Coaching | Schedule Alerts

Deep Learning and Applications Project Proposal | Team aaa | 2026

---

# Why young job seekers need an integrated assistant

| Scattered Information | Eligibility Ambiguity | Missed Deadlines |
|---|---|---|
| Policies, jobs, resumes, and deadlines live across separate platforms. | It is hard to quickly know which programs fit a specific profile. | Application and hiring schedules are fragmented, so opportunities are easy to miss. |
| Search cost increases. | Personalized guidance is missing. | Execution timing is lost. |

Proposal criterion: Problem definition and motivation

---

# Gaps in existing services

| Service | Strength | Limitation | YouthPath Improvement |
|---|---|---|---|
| OnTong Youth | Integrated policy information | Weak personal context | Profile-based policy matching |
| WorkNet / JobKorea | Rich job listings | Separated from policy and schedules | Connect jobs and policies |
| General LLM | Natural language consultation | Unstable recency and sources | RAG-based grounded answers |
| Personal Calendar | Schedule management | Disconnected from opportunity search | Automatic deadline registration |

---

# The integrated YouthPath experience

User Profile: major, experience, region, target role

| Policy Matching | Job Recommendation |
|---|---|
| Interprets eligibility rules and explains likely application fit. | Recommends postings by role, region, and experience. |

| Resume and Interview Coaching | Calendar and Deadline Alerts |
|---|---|
| Gives role-aware feedback and improvement suggestions. | Connects policy and hiring deadlines into the user's schedule. |

Turn scattered opportunities into one actionable workflow.

---

# System architecture

| Layer | Role |
|---|---|
| User UI | Web/app interface, profile input, result review |
| Router / Orchestrator | Classifies intent and calls specialist agents |
| Specialist Agents | Policy Agent, Job Agent, Essay Agent, Calendar Agent |
| RAG / MCP Data Layer | Vector search, public API, job API, calendar tool |
| Storage / Memory | User profile, search logs, schedule data |

Data sources: youth policies, job postings, successful resumes, disclosures and news.

---

# Agent role design

Router Agent: analyzes the user request and calls the needed specialist agent.

| Agent | Input | Process | Output |
|---|---|---|---|
| Policy Agent | Profile, region, income | Eligibility matching | Applicable programs |
| Job Agent | Target role, experience | Posting filtering | Recommended openings |
| Essay Agent | Resume draft | Rubric-based feedback | Edits and interview questions |
| Calendar Agent | Policy and hiring deadlines | Conflict checking | Calendar events and alerts |

---

# Why a RAG and MCP-based approach

| Project Condition | Technical Choice | Expected Effect |
|---|---|---|
| Policy and job data changes constantly | RAG-based runtime retrieval | Grounded answers with current sources |
| External APIs and tools are required | MCP / Tool Calling | Connect public data and calendars |
| Credits and training cost are limited | Lightweight orchestration | Fast prototype without retraining |

User Query -> Retrieve -> Agent -> Answer with Sources

---

# Dataset and processing strategy

| Data Source | Purpose | Update Method | Processing Strategy |
|---|---|---|---|
| Youth policy data | Policy matching and eligibility | Public API / scheduled crawl | Normalize condition fields |
| Job postings | Role and region recommendations | Job API / RSS | Tag roles and skills |
| Successful resume examples | Feedback criteria | Curated public material | Chunk by prompt and competency |
| Evaluation rubrics | Resume and interview coaching | Course rubric and guides | Convert to prompt rules |
| Disclosures and news | Company context enrichment | Search and disclosure links | Source-based summaries |

Use only public data with checked licenses and privacy constraints.

---

# Experiment and evaluation plan

| Quantitative Evaluation | Qualitative Evaluation |
|---|---|
| Policy Match Accuracy: fit between user profile and recommended policies | Resume Feedback Quality: specificity, role relevance, actionability |
| Source Agreement: consistency between answer evidence and source conditions | User Satisfaction: ease of exploration and intent to reuse |
| Response Time: latency for practical conversational use |  |

Baseline: single LLM answer vs. YouthPath RAG + Agent answer.

---

# Execution plan and role split

| Stage | Output |
|---|---|
| Proposal Presentation | Confirm problem and design |
| Data Collection and Indexing | Build policy, job, and resume corpora |
| Prototype Integration | Connect Agent, RAG, and UI |
| Evaluation and Final Presentation | Improve with quantitative and qualitative tests |

Roles: Policy Data, Job Data, Resume and Evaluation, UI and Testing, Deployment and Integration.

---

# Expected impact and risk response

| Expected Impact | Risk Response |
|---|---|
| Shorter search time: policies, jobs, and deadlines in one place | Credit exhaustion: caching, free tiers, summary-first processing |
| Fewer missed policies: eligibility conditions and deadlines shown together | External data instability: prioritize public APIs and preserve source links |
| More efficient job preparation: recommendations, feedback, and scheduling linked to action | Long documents and debugging: chunking and module-by-module tests |
|  | Privacy concerns: minimal collection and local storage options |

---

# Q and A

An integrated AI assistant for fragmented youth career-entry information.

Policy matching, job recommendations, resume coaching, schedule management.

Validated through a prototype and evaluation dataset.

YouthPath | Deep Learning and Applications Project Proposal
