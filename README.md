# Philz Coffee Wholesale Sales Agent

An AI sales-research agent that does a sales rep's first pass: it learns what a seller offers, finds and verifies likely business customers, and drafts tailored outreach for each one.

**[See the project write-up in my portfolio →](https://ishanya-anthapur.vercel.app/#sales)**

The agent works for the wholesale side of [Philz Coffee](https://philzcoffee.com/wholesale). It does two things:

1. **Builds a company profile.** It crawls Philz Coffee's website and writes a structured profile using only facts it can verify on that site.
2. **Finds customers and drafts outreach.** It reads the profile, searches the web for businesses that could buy wholesale coffee, checks each one on its official website, keeps the ones that match at least 65% of the fit criteria, and writes a personalized outreach email for each. The emails are drafts only. The agent never sends them.

**[Open the dashboard](dashboard.html)** (download it and open it in a browser) to see the profile, the three targets, and the draft emails in one place.

## What's in this repo

| Path | What it is |
| --- | --- |
| `sales_agent.py` | The agent (PydanticAI + Playwright, with the model called through Portkey). |
| `prompts/sales_agent.md` | The agent's system prompt. |
| `HARNESS.md` | Plain-English guide to the agent's tools, stopping rules, and guardrails. |
| `assets/seller_brief.md` | Why Philz Coffee was chosen and what makes a good wholesale customer. |
| `assets/company_profile.json` | The profile the agent built in Part 1. |
| `output/targets.json` | The qualified customer targets, with fit scores and evidence. |
| `output/emails.json` | The draft outreach emails (not sent). |
| `output/audit_log.json` | A log of every tool call the agent made. |
| `output/reflection.md` | My ranking of the targets and feedback on the emails. |
| `dashboard.html` | A self-contained dashboard of the results. |
| `AI-prompts.md` | The prompts I used with an AI coding assistant to build this. |

## Results

The agent found three targets in the Bay Area:

1. **Genentech**: a large South San Francisco campus with steady employee demand for office coffee and events.
2. **Stanford University**: Stanford Catering runs coffee service for meetings and conferences.
3. **UCSF**: multiple campuses and conference services, though it already has a main catering partner.

See [`output/reflection.md`](output/reflection.md) for the reasoning behind this ranking.

## Guardrails

- Crawls at most 10 pages per run, skipping duplicates and pages like cart, login, and privacy.
- Reads about 8,000 characters per page at most.
- Leaves a field as `null` when it can't be verified, instead of guessing.
- Drafts emails but never sends them.
- Logs tool calls and short summaries without full page contents.

See [`HARNESS.md`](HARNESS.md) for the full list.

## Running it yourself

You need Python 3.11+ and a [Portkey](https://portkey.ai) API key with access to an OpenAI model.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # then add your PORTKEY_API_KEY
```

**Part 1: build the company profile**

```bash
python sales_agent.py "Build a profile of this company." --url https://philzcoffee.com
```

**Part 2: find customers and draft emails**

```bash
python sales_agent.py "Find 3 good customer targets for this company and draft outreach emails." --profile assets/company_profile.json
```

Each run overwrites the files in `assets/` and `output/`.
