# Internal Proposal: Deploying VISION AI to Unblock Developer Velocity

**From:** Sandesh, System Architect  
**To:** Engineering Leadership & InfoSec Teams  
**Subject:** 30-Day Pilot Proposal for VISION AI (Internal Dev Assistant)  
**Status:** Under Review  

---

## The Core Problem: The Requirements vs. Tickets Context Gap
Right now, our engineers are losing a lot of time (roughly 2 to 3 hours every day) simply hunting for information. We have product specifications, design docs, and architectural guidelines sitting in Confluence, while our active tasks, bugs, and discussions live in Azure DevOps (ADO). 

When a developer is assigned an ADO ticket, they have to open Confluence, run manual searches, and hope they find the right page to understand the context. This context gap leads to:
1. **Slower feature delivery:** Devs spend more time searching than coding.
2. **Regression bugs:** Bug fixes are often pushed without seeing the full requirements spec, leading to missed details.
3. **Onboarding bottlenecks:** Getting a new developer up to speed on our legacy codebases takes weeks of manual query hunting.

---

## Our Solution: VISION AI
We built **VISION** to bridge this gap. It's a secure, internal developer assistant that automatically syncs and connects Confluence spaces with ADO tickets. 

Instead of searching manually, a developer can ask VISION questions like, *"What are the specifications for ticket #108264?"* or *"How should we handle this C# database timeout based on our Confluence design doc?"* and get a highly accurate answer with full context in seconds.

### Why this is different from generic AI tools:
* **True context retention (Parent-Document Collapsing):** Most AI systems split pages into random, disconnected text snippets, which leads to hallucinations. VISION locates the right requirement, but then pulls in the **entire, unbroken specification page** so the AI has 100% of the context.
* **Heuristic ID pre-filtering:** Search models are notoriously bad at finding specific numbers like ticket IDs. We added a direct database query override that guarantees 100% accurate lookup whenever a developer mentions an ADO ticket number.
* **Live Web Troubleshooting:** In addition to indexing our internal Confluence and ADO spaces, VISION has live web search. If a developer runs into an obscure compiler error or Zscaler proxy block, VISION can crawl public technical docs or StackOverflow to provide instant troubleshooting steps.

---

## Security, Privacy, & Magellon Compliance
We know Magellon has incredibly strict security rules, so we designed VISION with compliance as a first-class citizen:
* **Strictly Read-Only:** VISION has no write permissions in Confluence or ADO. It cannot alter code, tickets, or documentation.
* **Automatic DLP (Data Loss Prevention) filter:** We built a local security scanner on the backend. If anyone tries to sync or upload restricted data (like private keys, plain-text credentials, or customer data), the scanner blocks the ingestion and deletes the file instantly.
* **Proxy-Friendly (Zscaler Compliant):** The application is configured to route external API requests securely through our corporate proxy, while using a strict `NO_PROXY` bypass for internal Google Cloud SQL (PostgreSQL) traffic.
* **Isolate Chats:** Conversation histories are saved in private, isolated session tables. Internal developer discussions are never added to the shared search index.

---

## Infrastructure & FinOps (Hosting Costs)
We’ve hosted the pilot on Google Cloud using highly efficient serverless components:
* **GCP Cloud Run:** Host of the main Python API. It automatically scales down to **zero** when developers aren't using it (nights, weekends), meaning we pay nothing for idle server time.
* **Google Cloud SQL (PostgreSQL with pgvector):** To store our unified relational data and vector coordinates. We are using a shared-core instance which keeps our monthly database bill flat at **less than $30/month**.

---

## Future Scope: IDE & MS Teams Integration
Once the core platform is stable, we plan to bring VISION directly to where our developers spend their day:
* **VS Code / IDE Integration (Copilot-Style Sidebar):** We can embed VISION as a sidebar in VS Code. Developers will be able to right-click on any highlighted code block, logs, or compiler errors and select *"Send to VISION"*. This will instantly audit their code or debug errors against our internal Confluence requirements and architectural rules without them ever leaving the editor.
* **Microsoft Teams Integration (ChatOps Bot):** We can deploy VISION as a Teams Bot inside our tenant. This would let developers tag `@VISION` directly in active threads to summarize long discussions, fetch linked ADO tickets, or query Confluence spaces without context switching.

---

## 30-Day Pilot Request
We are requesting approval to run a **30-Day Scoped Pilot** inside our `gbr-mts-wgh-hkt-dev` Google Cloud project. 

For less than $30.00 in cloud resources, this pilot will prove that we can dramatically increase developer velocity, eliminate context switching, and make onboarding seamless. 

I’d love to walk you through the live dashboard and show you how it works. Let me know when you have 10 minutes this week!