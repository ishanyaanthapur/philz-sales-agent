# Philz Coffee Wholesale Sales Agent

## First task: build a company profile

The company website URL is provided through the terminal. Use that URL as the starting point and crawl the homepage and relevant linked pages, such as About, Careers, Locations, Sustainability, Contact, Menu, Services, and Wholesale pages when available.

Collect only information verified on the company’s own website. Do not guess, infer, or fabricate facts. If a field cannot be verified from the company website, set its value to `null`. Keep the profile concise, practical, and useful to a salesperson.

Save the completed profile as JSON at `assets/company_profile.json`.

The JSON object must include these fields:

```json
{
  "company_name": null,
  "company_website": null,
  "business_type_and_industry": null,
  "location_and_service_area": null,
  "number_of_locations": null,
  "workplace_or_customer_traffic": null,
  "existing_coffee_service": null,
  "products_or_services_offered": null,
  "hospitality_or_food_and_beverage_evidence": null,
  "target_contact_and_job_title": null,
  "contact_information": null,
  "business_need_or_sales_use_case": null,
  "budget_or_purchasing_signals": null,
  "growth_hiring_or_expansion_signals": null,
  "brand_and_customer_experience_fit": null,
  "qualification_evidence_and_source_links": null,
  "prospect_priority_and_rationale": null
}
```

For every populated field, include a concise factual value and a source URL from the company’s website where the information was verified. Do not use third-party sources, search-result snippets, or unsupported assumptions. Treat missing, ambiguous, or unavailable information as `null`.

The agent should prioritize meaningful details and accuracy over filling every field.

## Second task: find business customers and draft outreach

When asked to find potential business customers for the wholesaler company:

1. Read `assets/company_profile.json` to understand the wholesaler and the customer-fit criteria.
2. Use OpenAI web search through Portkey to discover candidate business customers.
3. Evaluate each candidate against the relevant criteria in the company profile. Keep a candidate only when it meets at least 65% of the applicable criteria and no more than 85% of the criteria are claimed without evidence. Record the criteria evaluated, the criteria met, the fit percentage, and the evidence supporting the evaluation.
4. Use Playwright to crawl each retained candidate’s official website and collect useful business context. Verify the company’s fit using only information found on its official website.
5. Find a publicly listed contact email for each candidate when available. Use `null` when no email can be verified.
6. Organize the qualified candidates and save them to `output/target.json`.
7. Draft a specific, personalized outreach email for each qualified candidate and save the drafts to `output/emails.json`. Never send an email.
8. Record every agent-loop iteration and tool call in `output/audit_log.json`, including tool names, arguments, and short result summaries. Do not record full webpage contents or hidden chain-of-thought.

For this task, crawl no more than 10 pages total per run. Avoid duplicate URLs and irrelevant pages such as cart, checkout, login, account, privacy, and terms pages. Limit extracted text from each page to approximately 8,000 characters. Use one model call at a time and never spawn parallel agents.
