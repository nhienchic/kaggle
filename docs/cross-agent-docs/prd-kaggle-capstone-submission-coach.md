# PRD: Kaggle Capstone Submission Coach

## Problem Statement

The user needs to finish a project for Kaggle's AI Agents: Intensive Vibe Coding Capstone Project. The competition requires more than a working prototype: the final submission must include a Kaggle Writeup, media gallery, YouTube video, public project link, codebase, setup instructions, and clear evidence that at least three course concepts were applied. Starting from an almost empty repository, the user needs a focused, judge-visible project that can be built quickly and communicated clearly.

The core risk is not only building an AI agent, but building the right amount of product, documentation, architecture evidence, security evidence, and demo material before the deadline. The user needs a tool that turns a competition brief and project repository into an actionable submission readiness package.

## Solution

Build a Streamlit web app called Kaggle Capstone Submission Coach. It will analyze the competition requirements and a selected repository, run a multi-agent submission readiness workflow, and produce the artifacts needed to complete a judge-ready capstone submission.

The product will use a multi-agent pipeline coordinated by an orchestrator. Four specialist agents will handle requirement analysis, repo auditing, submission strategy, and communication coaching. The workflow will prioritize judge-visible scoring evidence over broad product completeness.

The first implementation slice will be a thin end-to-end vertical slice: a Streamlit page loads the competition requirements, scans the current repo, runs deterministic fallback agents, renders one readiness report, and lets the user download Markdown artifacts. Gemini / Google ADK integration, MCP tools, security checks, and deployability evidence will then be layered in without changing the user-facing workflow.

## User Stories

1. As a capstone participant, I want to load the competition requirements, so that the product can evaluate my project against the actual judging criteria.
2. As a capstone participant, I want the app to read my project repository, so that I do not have to manually list what evidence exists.
3. As a capstone participant, I want a submission requirements checklist, so that I can see what is still missing before the deadline.
4. As a capstone participant, I want a judging rubric readiness score, so that I can prioritize the highest-value work.
5. As a capstone participant, I want the app to identify required submission assets, so that I do not forget the Kaggle Writeup, media gallery, video, or project link.
6. As a capstone participant, I want the app to map evidence for required course concepts, so that my submission clearly demonstrates what the competition asks for.
7. As a capstone participant, I want the app to check for a multi-agent or agent architecture, so that I can verify agents are central to the solution.
8. As a capstone participant, I want the app to check for MCP-related implementation evidence, so that I can show the MCP concept in code and documentation.
9. As a capstone participant, I want the app to check for security features, so that my project handles secrets and unsafe files responsibly.
10. As a capstone participant, I want the app to check for deployability evidence, so that judges can understand how to run or deploy the project.
11. As a capstone participant, I want a repo gap analysis, so that I know which files, modules, or docs are missing.
12. As a capstone participant, I want prioritized next steps, so that I can work in the order most likely to improve the submission score.
13. As a capstone participant, I want the app to generate a README draft, so that my public project link has clear setup and architecture documentation.
14. As a capstone participant, I want the app to generate a Kaggle Writeup draft, so that I can submit a polished project report faster.
15. As a capstone participant, I want the app to generate a five-minute video script, so that my demo covers the problem, agents, architecture, build, and result within the time limit.
16. As a capstone participant, I want the app to produce a single Markdown readiness report, so that I can save and review the full recommendation package.
17. As a capstone participant, I want downloadable artifacts, so that I can reuse the report, writeup draft, README draft, and script outside the app.
18. As a capstone participant, I want deterministic fallback output when no API key is available, so that the project remains reviewable without committed secrets.
19. As a capstone participant, I want Gemini / Google ADK support when an API key is configured, so that the project aligns with the Google-focused course ecosystem.
20. As a capstone participant, I want clear error states when LLM access is unavailable, so that the demo does not fail silently.
21. As a judge, I want to see why the product uses agents, so that I can evaluate whether agent behavior is meaningful rather than decorative.
22. As a judge, I want to see the multi-agent architecture explained, so that I can understand how responsibilities are divided.
23. As a judge, I want to see tool usage and MCP integration, so that I can evaluate the technical implementation beyond prompt-only generation.
24. As a judge, I want to see security safeguards, so that I can trust the project does not expose keys or read arbitrary files unsafely.
25. As a judge, I want to see deployability instructions, so that I can reproduce or understand the running product.
26. As a demo viewer, I want the first screen to be the usable app rather than a marketing page, so that I can immediately understand the workflow.
27. As a demo viewer, I want the report to be structured by judging criteria, so that the value is easy to follow in a short video.
28. As a developer, I want the core analysis workflow separated from Streamlit, so that I can test it without a browser.
29. As a developer, I want the repo scanner separated from the agent orchestration, so that file discovery and analysis behavior can be tested independently.
30. As a developer, I want the LLM provider behind an adapter, so that deterministic fallback and Gemini-backed execution share the same workflow contract.
31. As a developer, I want MCP tools behind a narrow interface, so that the app can demonstrate MCP without spreading protocol details across the codebase.
32. As a developer, I want security scanning to be explicit and testable, so that secret-detection behavior is not buried inside generated text.
33. As a developer, I want the report schema to be stable, so that Streamlit rendering, downloads, tests, and future agents can rely on the same output shape.
34. As a developer, I want the first slice to run locally with one command, so that the project can be demoed and judged easily.
35. As a developer, I want clear setup documentation for environment variables, so that secrets stay out of the repository.
36. As a future contributor, I want implementation decisions documented in the README and PRD, so that additional agents or integrations can be added without rethinking the product.
37. As a future contributor, I want the product to avoid automatic repo modification in v1, so that analysis remains safe and predictable.
38. As a capstone participant, I want a project that solves my actual submission workflow, so that the competition entry itself is useful rather than a throwaway demo.

## Implementation Decisions

- Build a Streamlit web app as the primary demo surface.
- Keep the first screen focused on the usable workflow: load requirements, scan repo, analyze readiness, display and download artifacts.
- Build the core product around a multi-agent pipeline coordinated by an orchestrator.
- Use four specialist agents: Requirement Analyst, Repo Auditor, Submission Strategist, and Communication Coach.
- The Requirement Analyst extracts hard submission requirements, scoring criteria, required assets, and required course concepts from the competition brief.
- The Repo Auditor scans the repository and identifies evidence for code, documentation, demo instructions, security notes, tests, deployment documentation, and submission artifacts.
- The Submission Strategist compares requirements against repo state and produces gaps, readiness scoring, priorities, and a build plan.
- The Communication Coach drafts the README sections, Kaggle Writeup outline or draft, pitch language, and five-minute video script.
- Use Gemini / Google ADK as the intended LLM and agent runtime integration.
- Supply model credentials through a `GOOGLE_API_KEY` environment variable. Do not commit secrets.
- Provide deterministic fallback behavior when no model credential is configured, so the app remains runnable and reviewable.
- Add a local MCP server or MCP-compatible tool layer exposing repository and requirement analysis tools.
- Include MCP-facing tools for reading competition requirements, scanning repository files, checking submission assets, checking security signals, and producing readiness checklist data.
- Add security features focused on likely secret detection, unsafe public credential files, and file-read boundary restrictions.
- Restrict repository reads to the selected project directory.
- Document the no-secrets policy and environment-variable setup.
- Optimize for judge-visible scoring evidence before product polish.
- Treat the public GitHub repository as an acceptable project link if a live deployment is not finished.
- Document deployability with clear local setup and a suggested deployment path such as Streamlit Community Cloud or Hugging Face Spaces.
- Keep v1 analysis-only. The app should not automatically modify the target repo, create GitHub issues, deploy the project, or generate a full production app.
- Represent the readiness output as a stable structured report that can be rendered in the app and exported as Markdown.
- Use the current competition requirement brief as the seed input for the first vertical slice.
- Current repository state is minimal: agent setup docs and the competition requirement brief exist, but no app implementation exists yet.

## Testing Decisions

- The primary test seam is the submission readiness analysis workflow.
- Tests should exercise external behavior: given requirement text, a repo snapshot, and model availability state, the workflow returns the expected checklist, readiness score, evidence map, gap analysis, build plan, drafts, script, and Markdown report.
- Tests should avoid coupling to internal agent prompts, private helper functions, or Streamlit rendering details.
- The orchestrator-level workflow is the highest-value seam because it captures the product behavior while leaving room to change individual agent implementations.
- Repo scanning should be tested through observable scan results for representative repository snapshots.
- Requirement parsing should be tested through observable extracted requirements and rubric fields from representative competition text.
- Security scanning should be tested with representative safe files and likely-secret examples.
- Markdown artifact generation should be tested by checking expected sections and core content, not exact prose where model output may vary.
- LLM integration should be adapter-based so tests can use deterministic fake responses.
- Streamlit should receive light smoke coverage where practical, but the main confidence should come from the workflow and artifact-generation tests.
- There is no prior app test suite in this repository, so new tests should establish the initial testing pattern.

## Out of Scope

- Automatically editing the analyzed project repository.
- Automatically creating GitHub issues from the generated build plan in v1.
- Automatically deploying the app to a public endpoint.
- Building a general-purpose SaaS product with authentication, persistence, billing, or multi-user collaboration.
- Supporting every possible issue tracker or project hosting platform in the first version.
- Requiring a live LLM call for the demo to function.
- Requiring users to provide private credentials in the UI.
- Generating a full production application unrelated to submission readiness.
- Polishing visual design before the core scoring evidence and artifacts exist.

## Further Notes

- The accepted product concept is Kaggle Capstone Submission Coach.
- The accepted track recommendation is Concierge Agents or Freestyle.
- The accepted product surface is Streamlit.
- The accepted architecture is multi-agent rather than a single agent with tools.
- The accepted required course concepts are multi-agent system with ADK, MCP server, security features, and deployability.
- The accepted model/runtime assumption is Gemini / Google ADK using `GOOGLE_API_KEY`.
- The accepted MVP boundary is analysis and artifact generation, not automatic repo modification.
- The accepted first implementation slice is a thin end-to-end workflow with deterministic fallback agents.
- The accepted priority is judge-visible scoring evidence first.
- The accepted build order is: runnable Streamlit app, multi-agent workflow, MCP/security/deployability evidence, README, Kaggle Writeup draft, video script, then UI polish.
- The accepted definition of done is a complete submission package: runnable app, multi-agent report, MCP/tools documentation, security scan, README, Kaggle Writeup draft, video script, and a public project link.
