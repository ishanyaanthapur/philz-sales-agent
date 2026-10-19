# Sales Agent Harness Guide

This document explains how the Philz Coffee wholesale sales agent works. It is written for a manager who wants to understand what the agent can do, when it stops, and what protections apply to its research.

## 1. Tools the agent can use

The agent has different tools for the two stages of the project.

### Part 1: Company profile

| Tool | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| `crawl_site` | Visits the company website and useful internal pages, such as About, Products, Wholesale, Locations, Sustainability, Careers, and Contact. | A company-page URL. | A short extract of the page, plus links to other relevant pages on the same website. The page extract is limited to about 8,000 characters. |
| `write_profile` | Saves the completed company profile. | The structured company profile produced by the agent. | `assets/company_profile.json`. |

### Part 2: Customer discovery and outreach drafts

| Tool | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| `load_company_profile` | Reads the wholesaler’s profile and the criteria used to judge potential customers. | The profile file path, normally `assets/company_profile.json`. | The company profile and its customer-fit criteria. |
| `search_web` | Uses OpenAI web search through Portkey to find possible business customers. | A focused search question, such as businesses likely to need wholesale coffee. | Web-search results that help identify candidate companies and their official websites. |
| `crawl_site` | Checks a candidate’s official website and gathers useful business context. | A candidate company’s website URL. | A short page extract, plus relevant internal links. |
| `write_targets` | Saves the companies that pass the fit review. | A list of qualified candidates, their fit scores, evidence, and contact details. | `output/targets.json`. The earlier filename `output/target.json` is also retained for compatibility. |
| `write_emails` | Saves personalized outreach drafts without sending them. | A list of draft emails, including recipient, subject, and body. | `output/emails.json`. |

### Shared record

| Tool or record | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| Audit logging | Records what the agent did so a person can review the run. | Run details, tool names, tool arguments, and short result summaries. | `output/audit_log.json`. It does not store full webpage contents or hidden chain-of-thought. |

## 2. Stopping rules

The agent should stop when any of the following applies:

- It has completed the requested task and produced the required output files.
- It has found enough qualified targets for the request. For example, a request for three targets is complete after three acceptable targets and their drafts have been prepared.
- It has crawled 10 pages in the run. This is the maximum, even if more research would be useful.
- There are no more relevant, same-company pages to review.
- A required file, such as `company_profile.json`, cannot be read.
- A website repeatedly fails to load or a tool repeatedly fails. The agent should record the failure in the audit log and stop rather than repeatedly retrying indefinitely.
- A candidate cannot be verified from its official website. The agent should discard that candidate and continue only if the page limit and task request allow it.
- An email address cannot be verified. The agent should use `null` for the email and may still keep the candidate if the candidate otherwise qualifies.

The agent must never continue research merely to fill an empty field. Missing or unverifiable information is left as `null` or clearly marked as unavailable.

## 3. Guardrails

### Part 1: Company-profile guardrails

- The starting company URL is provided through the terminal.
- The agent may crawl only pages on the same domain as the provided company URL.
- It may crawl no more than 10 pages in one run.
- It prioritizes likely useful pages, including About, Products, Wholesale, Locations, Sustainability, Careers, and Contact.
- It avoids duplicate URLs.
- It avoids irrelevant pages such as cart, checkout, login, account, privacy, and terms pages.
- It limits extracted text from each page to approximately 8,000 characters.
- It uses one model call at a time and does not create parallel agents.
- It uses only facts verified on the company’s own website.
- It does not guess, infer, or fabricate facts. If a field cannot be verified, its value is `null`.
- It saves the completed profile to `assets/company_profile.json`.
- It records tool calls and short summaries in `output/audit_log.json`, without saving full webpage contents or hidden chain-of-thought.

### Part 2: Customer-discovery and outreach guardrails

- The agent must first read `assets/company_profile.json` before evaluating prospects.
- It uses OpenAI web search through Portkey to discover candidates, then uses Playwright to verify candidates on their official websites.
- It evaluates each candidate against the relevant company-profile criteria.
- It keeps only candidates meeting at least 65% of the relevant criteria, and records the criteria evaluated, criteria met, fit score, and supporting evidence.
- It does not claim a criterion is met without evidence from the candidate’s official website.
- It may crawl no more than 10 pages total in one run.
- It avoids duplicate URLs and irrelevant pages such as cart, checkout, login, account, privacy, and terms pages.
- It limits extracted text from each page to approximately 8,000 characters.
- It uses one model call at a time and does not spawn parallel agents.
- It looks for a publicly listed business contact email and uses `null` when none can be verified.
- It writes qualified targets to `output/targets.json` and outreach drafts to `output/emails.json`.
- Outreach drafts must be specific to each candidate, but the agent must never send an email.
- It records tool names, arguments, and short result summaries in `output/audit_log.json`.
- It does not put full webpage contents or hidden chain-of-thought in the audit log.
