<!--
YouthPath — A Multi-Agent Assistant for Youth Social Entry
Initial proposal deck for Hanyang University · Deep Learning Methods and Application

Written in Marp Markdown.
To render to PPTX:  npx @marp-team/marp-cli@latest YouthPath_Proposal.md --pptx
To render to PDF :  npx @marp-team/marp-cli@latest YouthPath_Proposal.md --pdf
Or open this file in VS Code with the "Marp for VS Code" extension and export.

Design system: Navy Editorial Report (cool lavender canvas + deep navy primary).
-->

---
marp: true
size: 16:9
paginate: false
theme: default
style: |
  /* ---- Navy Editorial Report — design tokens ---- */
  :root {
    --navy:       #1C2C5A;
    --canvas:     #E9EDF6;
    --lavender:   #C9D1E5;
    --light-lav:  #DBE0EE;
    --mid-lav:    #A9B4D2;
    --blue-grey:  #7C8AAE;
    --border:     #D6DCE9;
    --white:      #FFFFFF;
  }

  section {
    background: var(--canvas);
    color: var(--navy);
    font-family: 'Pretendard', 'Noto Sans KR', -apple-system, 'Segoe UI', sans-serif;
    font-weight: 300;
    padding: 0;
    position: relative;
  }

  /* Top navy bar across every slide */
  section::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 8px;
    background: var(--navy);
  }

  /* Body slide header zone */
  section > h1 {
    color: var(--navy);
    font-weight: 800;
    font-size: 44px;
    margin: 56px 0 0 64px;
    line-height: 1.05;
  }

  /* Right-side ALL CAPS kicker (rendered via blockquote convention) */
  .kicker {
    position: absolute;
    top: 56px;
    right: 64px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.2em;
    color: var(--navy);
    text-align: right;
  }
  .subtitle {
    position: absolute;
    top: 92px;
    right: 64px;
    font-size: 12px;
    font-weight: 300;
    color: var(--blue-grey);
    text-align: right;
    line-height: 1.4;
    max-width: 480px;
  }

  /* Page number bottom right */
  .pn {
    position: absolute;
    bottom: 32px;
    right: 64px;
    font-size: 12px;
    font-weight: 700;
    color: var(--navy);
  }
  .pn::before {
    content: '■ ';
    color: var(--navy);
    font-size: 8px;
    margin-right: 6px;
    vertical-align: middle;
  }

  /* Body content area */
  section > .body {
    margin: 168px 64px 80px 64px;
  }

  /* Generic card */
  .card {
    background: var(--white);
    border: 1px solid var(--border);
    padding: 20px 24px;
    border-radius: 0;
  }
  .card h3 {
    margin: 0 0 6px 0;
    font-weight: 700;
    color: var(--navy);
    font-size: 18px;
  }
  .card p { margin: 4px 0; color: var(--navy); font-size: 13px; line-height: 1.5; }
  .card .fact {
    margin-top: 10px;
    font-size: 11px;
    font-weight: 700;
    color: var(--blue-grey);
    letter-spacing: 0.18em;
  }

  /* Number badge */
  .badge {
    display: inline-block;
    width: 30px; height: 30px;
    background: var(--navy);
    color: var(--white);
    font-weight: 700;
    text-align: center;
    line-height: 30px;
    font-size: 13px;
    margin-right: 10px;
    vertical-align: middle;
  }

  /* Big number block */
  .bignum {
    font-size: 144px;
    font-weight: 800;
    color: var(--navy);
    line-height: 0.95;
    letter-spacing: -0.02em;
  }
  .bignum-label {
    font-size: 11px;
    font-weight: 700;
    color: var(--blue-grey);
    letter-spacing: 0.2em;
    margin-top: 8px;
  }

  /* Tables */
  table { width: 100%; border-collapse: collapse; }
  table th {
    background: var(--navy);
    color: var(--white);
    padding: 12px 16px;
    text-align: left;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
  }
  table td {
    padding: 12px 16px;
    color: var(--navy);
    font-size: 13px;
    border-bottom: 1px solid var(--border);
    background: var(--white);
  }
  table td:first-child { font-weight: 700; }

  /* Layered architecture bands */
  .layer {
    padding: 16px 28px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
  }
  .layer.core { background: var(--navy); color: var(--white); }
  .layer.edge { background: var(--white); border: 1px solid var(--border); color: var(--navy); }
  .layer .lbl {
    font-weight: 700;
    letter-spacing: 0.15em;
    width: 280px;
    font-size: 13px;
  }
  .layer .comp { font-size: 14px; }

  /* Chip */
  .chip {
    display: inline-block;
    padding: 8px 14px;
    margin: 4px 6px 4px 0;
    background: var(--lavender);
    color: var(--navy);
    font-size: 11px;
    font-weight: 700;
  }

  /* Two-column body grid */
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .grid-2x2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
  .grid-5 { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }

  /* Cover page */
  section.cover h1 { font-size: 88px; font-weight: 800; margin: 0; }
  section.cover .pre { font-size: 36px; font-weight: 300; margin: 0; }
  section.cover .sub {
    font-size: 14px; font-weight: 700; color: var(--blue-grey);
    letter-spacing: 0.25em;
    margin-top: 16px;
  }
  section.cover .meta {
    position: absolute; bottom: 64px; right: 64px;
    text-align: right; font-size: 12px; line-height: 1.6;
    color: var(--navy);
  }
  section.cover .date {
    position: absolute; top: 32px; right: 64px;
    font-size: 13px; font-weight: 700; color: var(--navy);
  }
  section.cover .vlabel {
    position: absolute; left: 24px; top: 50%;
    transform: translateY(-50%) rotate(-90deg);
    font-size: 12px; font-weight: 700;
    letter-spacing: 0.4em; color: var(--navy);
  }

  /* Closing page */
  section.closing h1 { font-size: 96px; font-weight: 800; text-align: center; margin: 180px 0 0 0; }
  section.closing .more { font-size: 48px; font-weight: 300; text-align: center; margin: 12px 0 0 0; color: var(--navy); }
  section.closing .qa-sub {
    font-size: 14px; font-weight: 700; letter-spacing: 0.3em;
    color: var(--blue-grey); text-align: center; margin-top: 24px;
  }
  section.closing .strip {
    position: absolute; left: 64px; right: 64px; bottom: 56px;
    border-top: 1px solid var(--border); padding-top: 14px;
    display: grid; grid-template-columns: 1fr 1fr 1fr;
    font-size: 12px; color: var(--navy);
  }

  /* Contents page (left lavender panel + right list) */
  section.contents { padding: 0; }
  section.contents .panel {
    position: absolute; left: 0; top: 8px; bottom: 0; width: 33%;
    background: var(--lavender);
    padding: 240px 48px 0 48px;
  }
  section.contents .panel h1 {
    font-size: 72px; font-weight: 800; margin: 0;
  }
  section.contents .panel .lbl {
    font-size: 12px; font-weight: 700;
    letter-spacing: 0.25em; color: var(--navy);
    margin-top: 8px;
  }
  section.contents ol {
    position: absolute; left: 38%; top: 120px; right: 64px;
    list-style: none; padding: 0; margin: 0;
  }
  section.contents li { margin-bottom: 22px; }
  section.contents li h3 { margin: 0; font-size: 22px; font-weight: 700; color: var(--navy); }
  section.contents li p { margin: 4px 0 0 0; font-size: 13px; color: var(--blue-grey); }
---

<!-- _class: cover -->

<span class="vlabel">PRESENTATION</span>
<span class="date">2026.05.05</span>

<p class="pre">A Multi-Agent Assistant for</p>

# Youth Social Entry

<p class="sub">YOUTHPATH — INITIAL PROPOSAL</p>

<div class="meta">
Hanyang University · Deep Learning Methods and Application<br>
Five-Person Team<br>
LLM · RAG · Multi-Agent · MCP
</div>

---

<!-- _class: contents -->

<div class="panel">

# Contents

<div class="lbl">YOUTHPATH PROPOSAL</div>

</div>

<ol>
  <li><h3><span class="badge">01</span> Problem Definition</h3><p>A fragmented path into society.</p></li>
  <li><h3><span class="badge">02</span> Solution and Differentiation</h3><p>YouthPath and what makes it different.</p></li>
  <li><h3><span class="badge">03</span> System Design</h3><p>A four-layer architecture with a multi-agent core.</p></li>
  <li><h3><span class="badge">04</span> Evaluation Plan</h3><p>Quantitative and qualitative dual-track evaluation.</p></li>
  <li><h3><span class="badge">05</span> Execution Plan</h3><p>Team, schedule, and cost.</p></li>
  <li><h3><span class="badge">06</span> Expected Outcomes</h3><p>User impact and a five-phase roadmap.</p></li>
</ol>

<span class="kicker">CONTENTS</span>
<span class="pn">02</span>

---

# Problem Definition

<span class="kicker">PROBLEM DEFINITION</span>
<span class="subtitle">Youth career-entry information is fragmented,<br>and qualification matching, real-time data, and alerts are missing.</span>

<div class="body">

<div class="grid-2">
<div>

<div class="bignum">~12M</div>
<div class="bignum-label">KOREAN YOUTH AGED 19–34</div>

Average information-search cost: 2 hours.

</div>
<div>

<div class="grid-2x2">
<div class="card"><h3>Youth Policy</h3><p>Government24, Ontongchungnyeon</p><p>List-only search; no eligibility match.</p></div>
<div class="card"><h3>Job Postings</h3><p>WorkNet, JobKorea, Saramin</p><p>Per-employer fragmentation; no resume linkage.</p></div>
<div class="card"><h3>Resume &amp; Interview</h3><p>Standalone tools</p><p>No company-specific reference data.</p></div>
<div class="card"><h3>Schedule Management</h3><p>Personal calendar apps</p><p>No automatic deadline sync.</p></div>
</div>

</div>
</div>

</div>

<span class="pn">03</span>

---

# Pain Points

<span class="kicker">PAIN POINTS</span>
<span class="subtitle">Four structural problems compound on each other,<br>so no single existing tool can resolve them.</span>

<div class="body">

<div class="grid-2x2">

<div class="card">
<span class="badge">01</span> <strong>Information Fragmentation</strong>
<p>Information lives across 5–6 separate platforms.</p>
<div class="fact">~2 HOURS PER TASK</div>
</div>

<div class="card">
<span class="badge">02</span> <strong>No Qualification Matching</strong>
<p>Policy sites list policies but never decide whether you qualify.</p>
<div class="fact">MANUAL ELIGIBILITY CHECK</div>
</div>

<div class="card">
<span class="badge">03</span> <strong>LLM Knowledge Cutoff</strong>
<p>General-purpose LLMs cannot see new policies, filings, or postings.</p>
<div class="fact">STALE ANSWERS</div>
</div>

<div class="card">
<span class="badge">04</span> <strong>Missed Application Deadlines</strong>
<p>Deadlines are scattered; users miss eligible policies.</p>
<div class="fact">NO UNIFIED ALERTS</div>
</div>

</div>
</div>

<span class="pn">04</span>

---

# Solution

<span class="kicker">SOLUTION OVERVIEW</span>
<span class="subtitle">One profile entry, four domains.<br>A single interface replaces five to six platform visits.</span>

<div class="body">

**YOUTHPATH** — an LLM-based multi-agent assistant.

<div class="grid-2x2">

<div class="card"><span class="badge">01</span> <strong>Policy Agent</strong><p>Eligibility match and application guide.</p></div>
<div class="card"><span class="badge">02</span> <strong>Job Agent</strong><p>GitHub-aware posting matching.</p></div>
<div class="card"><span class="badge">03</span> <strong>Resume Agent</strong><p>Company-specific coaching from DART filings.</p></div>
<div class="card"><span class="badge">04</span> <strong>Calendar Agent</strong><p>Unified deadline alerts.</p></div>

</div>
</div>

<span class="pn">05</span>

---

# Differentiation

<span class="kicker">DIFFERENTIATION</span>
<span class="subtitle">Existing tools cover only part of one domain.<br>YouthPath integrates all four through hybrid RAG, multi-agent, MCP, and matching.</span>

<div class="body">

<div class="grid-2">
<div>

| Existing Tool | Limitation | YouthPath Differentiator |
|---------------|------------|---------------------------|
| Government24 | Keyword search; no eligibility decision. | Profile-based eligibility match. |
| JobKorea AI Match | Postings only; no resume linkage. | Postings + resume + interview unified. |
| ChatGPT | Knowledge cutoff; cannot see new filings. | RAG and MCP for live data. |
| Personal Calendar | Manual entry required. | Automatic deadline sync from agents. |

</div>
<div>

<div class="card"><span class="badge">01</span> <strong>Hybrid RAG</strong><p>Static + Dynamic indexing.</p></div>
<div class="card"><span class="badge">02</span> <strong>Multi-Agent Orchestration</strong><p>Router + four domain experts.</p></div>
<div class="card"><span class="badge">03</span> <strong>MCP Integration</strong><p>Five external APIs unified.</p></div>
<div class="card"><span class="badge">04</span> <strong>Personalized Matching</strong><p>Profile-to-eligibility automation.</p></div>

</div>
</div>

</div>

<span class="pn">06</span>

---

# System Architecture

<span class="kicker">SYSTEM ARCHITECTURE</span>
<span class="subtitle">A four-layer design where each layer<br>is joined by standard protocols (MCP, HTTP).</span>

<div class="body">

<div class="layer edge">
<div class="lbl">L1 / FRONTEND</div>
<div class="comp">Streamlit  ·  Profile Form  ·  Unified Dashboard</div>
</div>

<div class="layer core">
<div class="lbl">L2 / MULTI-AGENT ORCHESTRATION</div>
<div class="comp">LangGraph  ·  Router  ·  4 Sub-Agents</div>
</div>

<div class="layer core">
<div class="lbl">L3 / DATA LAYER</div>
<div class="comp">Static RAG  ·  Dynamic RAG  ·  5 MCP Servers</div>
</div>

<div class="layer edge">
<div class="lbl">L4 / INFRASTRUCTURE</div>
<div class="comp">AWS EC2  ·  AWS S3  ·  LUXIA Platform</div>
</div>

</div>

<span class="pn">07</span>

---

# Multi-Agent Design

<span class="kicker">MULTI-AGENT DESIGN</span>
<span class="subtitle">A supervisor pattern: the Router classifies queries<br>and delegates to four domain experts.</span>

<div class="body">

**Router Agent** classifies the user query and delegates to one of four specialized agents.

<div class="grid-2">
<div>

<div class="card"><strong>Policy Agent</strong><p>Eligibility match  ·  Static RAG + Ontongchungnyeon MCP</p></div>
<div class="card"><strong>Job Agent</strong><p>Posting match  ·  WorkNet MCP + GitHub analysis</p></div>

</div>
<div>

<div class="card"><strong>Resume Agent</strong><p>Company coaching  ·  Dynamic RAG + DART MCP</p></div>
<div class="card"><strong>Calendar Agent</strong><p>Deadline aggregation across agents</p></div>

</div>
</div>

</div>

<span class="pn">08</span>

---

# Hybrid RAG and MCP

<span class="kicker">DATA STRATEGY</span>
<span class="subtitle">Static and Dynamic RAG split by update frequency,<br>external APIs unified through MCP.</span>

<div class="body">

<div class="grid-2">
<div>

|  | Static RAG | Dynamic RAG |
|---|-----------|-------------|
| **Data** | Policy docs / Resumes / NCS | DART filings |
| **Cadence** | Weekly to yearly | Per-request, runtime |
| **Method** | Pre-indexed (Chroma + bge-m3) | Indexed at request, ephemeral |

</div>
<div>

### MCP

<div>
<span class="chip">Ontongchungnyeon</span>
<span class="chip">Public Data Portal</span>
<span class="chip">WorkNet</span>
<span class="chip">DART</span>
<span class="chip">Naver News</span>
</div>

<p style="font-size: 12px; color: var(--blue-grey); margin-top: 24px; font-style: italic;">
RAG over fine-tuning: live data updates, source citation, $50 budget feasible.
</p>

</div>
</div>

</div>

<span class="pn">09</span>

---

# Dataset and Evaluation

<span class="kicker">DATASET &amp; EVALUATION</span>
<span class="subtitle">Seven open-license datasets,<br>quantitative and qualitative dual-track evaluation.</span>

<div class="body">

<div class="grid-2">
<div>

| Dataset | Source | Use | License |
|---------|--------|-----|---------|
| Youth Policy | Ontongchungnyeon API | Static RAG | KOGL |
| Government Policy | Public Data Portal | Static RAG | KOGL |
| Job Postings | WorkNet API | Tool Use (live) | KOGL |
| Corporate Filings | DART API | Dynamic RAG | Free |
| Accepted Resumes | Public posts | Static RAG | Public |
| NCS Standards | NCS competency | Static RAG | KOGL |
| Eval Q&A | Built in-house, n=50 | Benchmark | Internal |

</div>
<div>

<div style="background: var(--navy); color: var(--white); padding: 12px 24px; font-weight: 700; letter-spacing: 0.2em; font-size: 12px;">QUANTITATIVE</div>
<div class="card">
<p>Precision <strong>≥ 0.85</strong></p>
<p>Recall <strong>≥ 0.80</strong></p>
<p>Citation Accuracy <strong>≥ 0.90</strong></p>
<p>Response Time <strong>≤ 5s</strong></p>
</div>

<div style="background: var(--white); border: 1px solid var(--border); color: var(--navy); padding: 12px 24px; font-weight: 700; letter-spacing: 0.2em; font-size: 12px; margin-top: 12px;">QUALITATIVE</div>
<div class="card">
<p>■ User Survey (n = 20, 5-point Likert)</p>
<p>■ LLM-as-Judge (GPT-4o-mini scoring)</p>
<p>■ Head-to-Head vs ChatGPT and Government24+JobKorea</p>
</div>

</div>
</div>

</div>

<span class="pn">10</span>

---

# Execution Plan

<span class="kicker">TEAM · SCHEDULE · COST</span>
<span class="subtitle">Five domain experts, seven-week roadmap,<br>total budget under $52.</span>

<div class="body">

| Workstream | W10 | W11 | W12 | W13 | W14 | W15 | W16 |
|------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A · Policy + Static RAG** |  | ░ | █ | ░ | ░ |  |  |
| **B · Job + DART/MCP** |  | ░ | ░ | █ | ░ |  |  |
| **C · Resume + Evaluation** |  | ░ | ░ | ░ | ░ | █ |  |
| **D · Frontend + UX** |  |  | ░ | ░ | █ | ░ |  |
| **E · Backend + LangGraph** |  | ░ | ░ | █ | █ | ░ |  |

<div class="grid-2" style="margin-top: 24px;">
<div>
<div style="font-size: 48px; font-weight: 800; color: var(--navy);">~$52 total</div>
<p>LUXIA $50 (course-provided)  +  GPT-4o-mini $2</p>
<p style="color: var(--blue-grey); font-size: 12px;">AWS Academy / open-source tooling at $0.</p>
</div>
<div class="card">
<div class="fact">KEY RISKS</div>
<div class="grid-2" style="margin-top: 8px; font-size: 12px;">
<div>■ LUXIA credit exhaustion</div>
<div>■ DART filing size</div>
<div>■ Multi-agent debugging</div>
<div>■ Dataset licensing</div>
</div>
</div>
</div>

</div>

<span class="pn">11</span>

---

# Expected Outcomes

<span class="kicker">EXPECTED OUTCOMES</span>
<span class="subtitle">User impact and technical capability,<br>extensible through a five-phase roadmap.</span>

<div class="body">

<div class="grid-2">
<div>

<div class="bignum">95%</div>
<div class="bignum-label">REDUCTION IN INFORMATION-SEARCH TIME</div>

<p style="font-size: 18px; font-weight: 700; margin-top: 12px;">2 hours → 5 minutes</p>

<p>Across ~12M Korean youth in scope.</p>

</div>
<div>

<div class="card">
<div class="fact">TECHNICAL OUTCOMES</div>
<p>■ Integrated LLM + RAG + Multi-Agent + MCP system</p>
<p>■ Hybrid RAG (Static + Dynamic) in practice</p>
<p>■ Korean-domain LUXIA usage at production scale</p>
</div>

<div class="fact" style="margin-top: 20px;">FUTURE ROADMAP</div>
<div class="grid-5" style="margin-top: 8px;">
<div class="chip" style="text-align: center;"><div style="font-size: 9px; color: var(--blue-grey);">PHASE 2</div>Multilingual</div>
<div class="chip" style="text-align: center;"><div style="font-size: 9px; color: var(--blue-grey);">PHASE 3</div>Voice</div>
<div class="chip" style="text-align: center;"><div style="font-size: 9px; color: var(--blue-grey);">PHASE 4</div>Mobile App</div>
<div class="chip" style="text-align: center;"><div style="font-size: 9px; color: var(--blue-grey);">PHASE 5</div>KakaoTalk</div>
<div class="chip" style="text-align: center;"><div style="font-size: 9px; color: var(--blue-grey);">PHASE 6</div>Learning</div>
</div>

</div>
</div>

</div>

<span class="pn">12</span>

---

<!-- _class: closing -->

<span class="kicker">Q&amp;A</span>

# Thank You

<p class="more">for Your Attention</p>

<p class="qa-sub">QUESTIONS AND DISCUSSION WELCOME</p>

<div class="strip">
<div>Hanyang University · Deep Learning<br>Five-Person Team</div>
<div style="text-align: center;">Team contact: [team@hanyang.ac.kr]</div>
<div style="text-align: right;">Online Q&amp;A by May 7</div>
</div>
