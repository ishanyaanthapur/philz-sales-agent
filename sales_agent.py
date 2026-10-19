"""Run the Philz Coffee wholesale sales-research agent."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from playwright.async_api import Browser, Page, async_playwright


ROOT = Path(__file__).resolve().parent
ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR = ROOT / "output"
PROMPT_PATH = ROOT / "prompts" / "sales_agent.md"
PROFILE_PATH = ASSETS_DIR / "company_profile.json"
AUDIT_PATH = OUTPUT_DIR / "audit_log.json"
TARGETS_PATH = OUTPUT_DIR / "targets.json"
LEGACY_TARGETS_PATH = OUTPUT_DIR / "target.json"
EMAILS_PATH = OUTPUT_DIR / "emails.json"
MAX_PAGES = 10
MAX_TEXT_CHARS = 8_000


class CompanyProfile(BaseModel):
    company_name: Any = None
    company_website: Any = None
    business_type_and_industry: Any = None
    location_and_service_area: Any = None
    number_of_locations: Any = None
    workplace_or_customer_traffic: Any = None
    existing_coffee_service: Any = None
    products_or_services_offered: Any = None
    hospitality_or_food_and_beverage_evidence: Any = None
    target_contact_and_job_title: Any = None
    contact_information: Any = None
    business_need_or_sales_use_case: Any = None
    budget_or_purchasing_signals: Any = None
    growth_hiring_or_expansion_signals: Any = None
    brand_and_customer_experience_fit: Any = None
    qualification_evidence_and_source_links: Any = None
    prospect_priority_and_rationale: Any = None


class TargetCandidate(BaseModel):
    company_name: str
    company_website: str
    fit_percentage: float
    criteria_evaluated: list[str]
    criteria_met: list[str]
    business_context: str
    contact_email: str | None = None
    evidence_sources: list[str]
    fit_rationale: str


class OutreachEmail(BaseModel):
    company_name: str
    recipient_email: str | None = None
    subject: str
    body: str


class ProspectResult(BaseModel):
    targets: list[TargetCandidate]
    emails: list[OutreachEmail]


class CrawlState:
    def __init__(self, seed_url: str | None = None) -> None:
        self.seed_url = seed_url
        self.profile_path: str = str(PROFILE_PATH)
        self.domain = self._domain(seed_url) if seed_url else None
        self.discovered_domains: set[str] = set()
        self.visited: list[str] = []
        self.pages: list[dict[str, str]] = []
        self.audit: list[dict[str, Any]] = []
        self.browser: Browser | None = None

    @staticmethod
    def _domain(url: str | None) -> str | None:
        if not url:
            return None
        return urlparse(url).netloc.lower().removeprefix("www.")

    def log(self, event: str, tool: str | None = None, arguments: Any = None, summary: str = "") -> None:
        entry: dict[str, Any] = {"event": event, "summary": summary}
        if tool:
            entry["tool"] = tool
        if arguments is not None:
            entry["arguments"] = arguments
        self.audit.append(entry)
        OUTPUT_DIR.mkdir(exist_ok=True)
        AUDIT_PATH.write_text(json.dumps(self.audit, indent=2), encoding="utf-8")


def clean_url(raw_url: str, base_url: str) -> str:
    url = urldefrag(urljoin(base_url, raw_url))[0]
    parsed = urlparse(url)
    return parsed._replace(query="").geturl().rstrip("/") or url


def domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def is_relevant(url: str) -> bool:
    path = urlparse(url).path.lower()
    blocked = ("/cart", "/checkout", "/login", "/account", "/privacy", "/terms")
    return not any(part in path for part in blocked)


def relevance_score(url: str) -> int:
    path = urlparse(url).path.lower()
    keywords = ("about", "product", "wholesale", "location", "sustain", "contact", "career", "menu", "service")
    return sum(keyword in path for keyword in keywords)


@asynccontextmanager
async def browser_for(state: CrawlState):
    async with async_playwright() as playwright:
        state.browser = await playwright.chromium.launch(headless=True)
        try:
            yield state.browser
        finally:
            await state.browser.close()


def portkey_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.environ["PORTKEY_API_KEY"],
        base_url="https://api.portkey.ai/v1",
        default_headers={"x-portkey-provider": "openai"},
    )


def make_model() -> OpenAIChatModel:
    return OpenAIChatModel("gpt-5.6-luna", provider=OpenAIProvider(openai_client=portkey_client()))


async def crawl_site(ctx: RunContext[CrawlState], url: str) -> str:
    """Crawl one allowed official-company page and return concise text and useful links."""
    state = ctx.deps
    state.log("agent_iteration", summary="Agent requested a website crawl")
    state.log("tool_call", "crawl_site", {"url": url}, "Starting page crawl")
    candidate_domain = domain(url)
    allowed = state.domain if state.domain else candidate_domain
    if state.domain is None:
        if state.discovered_domains and candidate_domain not in state.discovered_domains:
            result = "URL rejected: the domain was not discovered by web search."
            state.log("tool_result", "crawl_site", {"url": url}, result)
            return result
        state.discovered_domains.add(candidate_domain)
    if candidate_domain != allowed or not is_relevant(url):
        result = "URL rejected: it is outside the allowed company domain or is irrelevant."
        state.log("tool_result", "crawl_site", {"url": url}, result)
        return result
    if url in state.visited or len(state.visited) >= MAX_PAGES:
        result = "Page skipped: duplicate URL or maximum page limit reached."
        state.log("tool_result", "crawl_site", {"url": url}, result)
        return result
    if state.browser is None:
        raise RuntimeError("Browser is not available")

    page: Page = await state.browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        text = (await page.locator("body").inner_text())[:MAX_TEXT_CHARS]
        links = await page.locator("a[href]").evaluate_all(
            "els => els.map(a => ({text: (a.innerText || '').trim(), href: a.href}))"
        )
        state.visited.append(url)
        state.pages.append({"url": url, "text": text})
        candidates = []
        for link in links:
            candidate = clean_url(link["href"], url)
            if domain(candidate) == allowed and is_relevant(candidate) and candidate not in state.visited:
                candidates.append(candidate)
        candidates = sorted(set(candidates), key=relevance_score, reverse=True)[:20]
        result = json.dumps({"url": url, "text": text, "relevant_links": candidates})
        state.log("tool_result", "crawl_site", {"url": url}, f"Extracted {len(text)} characters and found {len(candidates)} candidate links")
        return result
    finally:
        await page.close()


async def load_company_profile(ctx: RunContext[CrawlState], path: str | None = None) -> str:
    """Load the seller profile that defines the target-customer criteria."""
    state = ctx.deps
    state.log("agent_iteration", summary="Agent requested the seller profile")
    path = path or state.profile_path
    state.log("tool_call", "load_company_profile", {"path": path}, "Loading company profile")
    profile_path = Path(path)
    if not profile_path.is_absolute():
        profile_path = ROOT / profile_path
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    result = json.dumps(profile)
    state.log("tool_result", "load_company_profile", {"path": path}, f"Loaded {len(profile)} profile criteria")
    return result


async def search_web(ctx: RunContext[CrawlState], query: str) -> str:
    """Use OpenAI web search through Portkey to discover potential customer companies."""
    state = ctx.deps
    state.log("agent_iteration", summary="Agent requested web search")
    state.log("tool_call", "search_web", {"query": query}, "Searching the web through Portkey")
    client = portkey_client()
    response = await client.responses.create(
        model="gpt-5.6-luna",
        tools=[{"type": "web_search_preview"}],
        input=query,
    )
    result = getattr(response, "output_text", None) or json.dumps(response.model_dump())
    for found_url in re.findall(r"https?://[^\s\"<>]+", result):
        state.discovered_domains.add(domain(found_url.rstrip(".,)")))
    state.log("tool_result", "search_web", {"query": query}, f"Received web-search results ({len(result)} characters)")
    return result


def _save_targets(state: CrawlState, targets: list[TargetCandidate]) -> str:
    state.log("tool_call", "write_targets", {"path": str(TARGETS_PATH)}, "Writing qualified customer targets")
    OUTPUT_DIR.mkdir(exist_ok=True)
    serialized = json.dumps([target.model_dump() for target in targets], indent=2)
    TARGETS_PATH.write_text(serialized, encoding="utf-8")
    LEGACY_TARGETS_PATH.write_text(serialized, encoding="utf-8")
    result = f"Saved {len(targets)} targets to {TARGETS_PATH}"
    state.log("tool_result", "write_targets", {"path": str(TARGETS_PATH)}, result)
    return result


async def write_targets(ctx: RunContext[CrawlState], targets: list[TargetCandidate]) -> str:
    """Save qualified customer targets to output/target.json."""
    return _save_targets(ctx.deps, targets)


def _save_emails(state: CrawlState, emails: list[OutreachEmail]) -> str:
    state.log("tool_call", "write_emails", {"path": str(EMAILS_PATH)}, "Writing outreach drafts")
    OUTPUT_DIR.mkdir(exist_ok=True)
    EMAILS_PATH.write_text(json.dumps([email.model_dump() for email in emails], indent=2), encoding="utf-8")
    result = f"Saved {len(emails)} email drafts to {EMAILS_PATH}"
    state.log("tool_result", "write_emails", {"path": str(EMAILS_PATH)}, result)
    return result


async def write_emails(ctx: RunContext[CrawlState], emails: list[OutreachEmail]) -> str:
    """Save unsent targeted outreach drafts to output/emails.json."""
    return _save_emails(ctx.deps, emails)


def make_profile_agent() -> Agent:
    agent = Agent(make_model(), system_prompt=PROMPT_PATH.read_text(encoding="utf-8"), output_type=CompanyProfile)
    agent.tool(crawl_site)
    agent.tool(write_profile)
    return agent


def make_target_agent() -> Agent:
    agent = Agent(make_model(), system_prompt=PROMPT_PATH.read_text(encoding="utf-8"), output_type=ProspectResult)
    agent.tool(load_company_profile)
    agent.tool(search_web)
    agent.tool(crawl_site)
    agent.tool(write_targets)
    agent.tool(write_emails)
    return agent


def _save_profile(state: CrawlState, profile: CompanyProfile) -> str:
    state.log("tool_call", "write_profile", {"path": str(PROFILE_PATH)}, "Writing validated company profile")
    ASSETS_DIR.mkdir(exist_ok=True)
    PROFILE_PATH.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    result = f"Saved company profile to {PROFILE_PATH}"
    state.log("tool_result", "write_profile", {"path": str(PROFILE_PATH)}, result)
    return result


async def write_profile(ctx: RunContext[CrawlState], profile: CompanyProfile) -> str:
    return _save_profile(ctx.deps, profile)


async def run_profile(query: str, url: str) -> CompanyProfile:
    state = CrawlState(url)
    state.log("run_start", arguments={"query": query, "url": url}, summary="Company-profile run started")
    async with browser_for(state):
        result = await make_profile_agent().run(query, deps=state)
        _save_profile(state, result.output)
    state.log("run_end", summary="Company-profile run completed")
    return result.output


async def run_targets(query: str, profile_path: str) -> ProspectResult:
    state = CrawlState()
    state.profile_path = profile_path
    state.log("run_start", arguments={"query": query, "profile": profile_path}, summary="Customer-target run started")
    async with browser_for(state):
        result = await make_target_agent().run(query, deps=state)
        _save_targets(state, result.output.targets)
        _save_emails(state, result.output.emails)
    state.log("run_end", summary="Customer-target run completed; drafts were not sent")
    return result.output


def main() -> None:
    # Looks for .env in this folder, then in parent folders.
    load_dotenv(override=True)
    if not os.getenv("PORTKEY_API_KEY"):
        raise RuntimeError("PORTKEY_API_KEY was not found. Copy .env.example to .env and add your key.")
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url")
    group.add_argument("--profile")
    args = parser.parse_args()
    if args.profile:
        asyncio.run(run_targets(args.query, args.profile))
    else:
        asyncio.run(run_profile(args.query, args.url))


if __name__ == "__main__":
    main()
