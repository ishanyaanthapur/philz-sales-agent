# Philz Coffee Wholesale Sales Agent — AI Prompts

Prompts used with an AI coding assistant to build this project, one section per assignment problem.

## Problem 2

### Initial prompt

Create an `assets` folder in `hw2` and add a file named `seller_brief.md`. The seller brief should describe Philz Coffee and its wholesale business. Include: (1) the company name and wholesale website, https://philzcoffee.com/wholesale?utm_source=chatgpt.com; (2) why I chose Philz Coffee, including my interest in gaining retail experience for my resume, missing Philz Coffee, and the fact that Philz meets the project’s business qualifiers; and (3) the information an agent should collect to identify appropriate B2B sales targets, including the fields that matter and why each field matters.

### Follow-up prompt

The initial prompt did not specify the agent framework, the location of the sales-agent prompt, or the project dependencies. Create a `prompts` folder containing `sales_agent.md`. Build the sales agent with `pydantic-ai-slim[openai]>=1.0.0`, and create a `requirements.txt` containing:

```text
pydantic-ai-slim[openai]>=1.0.0
portkey-ai>=1.0.0
python-dotenv>=1.0.1
dash>=2.17.0
```

## Problem 3

### Initial prompt

The sales agent’s first task is to accept a company website URL through the terminal, crawl the homepage and relevant company pages, and build a concise company profile using only facts verified on that company’s website. Include the specified sales-target research fields from `assets/seller_brief.md`, set unverifiable fields to `null`, include source URLs for populated fields, and save the JSON result to `assets/company_profile.json`.

## Problem 4

### Initial prompt

Create `sales_agent.py` as a PydanticAI agent that loads `prompts/sales_agent.md` as its system prompt. Give it Playwright tools to crawl the provided company URL and relevant same-domain internal pages, write the completed profile to `assets/company_profile.json`, and record each agent-loop iteration and tool call in `output/audit_log.json`. Enforce a maximum of 10 pages, prioritize About, Products, Wholesale, Locations, Sustainability, and Contact pages, avoid duplicates and irrelevant pages, limit extracted text to approximately 8,000 characters per page, use one model call at a time, and log tool names, arguments, and short result summaries without full webpage contents or hidden chain-of-thought. Accept a text query and required `--url`, runnable as `python sales_agent.py "Build a profile of this company." --url https://philzcoffee.com`.

## Problem 5

### Initial prompt

Update `prompts/sales_agent.md` and `sales_agent.py` for the customer-discovery task. When asked, the agent must read `assets/company_profile.json`, use OpenAI web search through Portkey to find potential business customers, and use Playwright to verify each retained candidate on its official website. Keep only candidates meeting at least 65% of the relevant company-profile criteria, record which criteria they meet and the evidence, find a publicly listed contact email when available, save qualified targets to `output/target.json`, and save personalized unsent outreach drafts to `output/emails.json`. Record each agent-loop iteration and tool call in `output/audit_log.json` with tool names, arguments, and short result summaries, excluding full webpage contents and hidden chain-of-thought. Enforce a maximum of 10 pages per run, avoid duplicate and irrelevant URLs, limit page text to approximately 8,000 characters, and use one model call at a time. The script must accept a query and `--profile`, runnable as `python sales_agent.py "Find 3 good customer targets for this company and draft outreach emails." --profile assets/company_profile.json`.

## Problem 6

### Initial prompt

Create a manager-readable `HARNESS.md` in `hw2`. Document every tool the sales agent can use, including each tool’s name, purpose, inputs, and outputs. Document stopping rules, including maximum steps or pages, enough targets found, missing required files, repeated failures, and unverifiable candidates. Document all guardrails, separated into the company-profile and customer-discovery/outreach parts of `prompts/sales_agent.md`. Keep the document clear and readable for a nontechnical manager.

## Problem 7

### Initial prompt

Create `output/reflection.md` with sections for me to complete. It should include a section for ranking each target company from best to worst, with space to explain the ranking, and a section for feedback on each target outreach email, with space to record strengths, improvements, and suggested revisions.

## Problem 8

### Initial prompt

Build a polished, self-contained `dashboard.html` that displays the Philz Coffee wholesaler profile, the three customer targets, their contact information, supporting details, and personalized draft outreach emails. Use a warm Philz-inspired visual style with rich coffee brown, burnt orange, cream, subtle green accents, rounded cards, playful typography, coffee-inspired visual elements, clear hierarchy, and links to the Philz wholesale website. Display each target in its own independently expandable card with the customer name and dropdown indicator visible when collapsed. Embed all content directly in the HTML so it works locally without setup.
