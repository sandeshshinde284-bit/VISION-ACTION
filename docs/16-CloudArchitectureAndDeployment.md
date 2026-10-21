# V.I.S.I.O.N. Cloud Architecture & Google Cloud Deployment Specification

**Document Reference:** V-CAD-2026-V1  
**Target Audience:** Engineering Leads, Cloud Architects, InfoSec Reviewers, Platform Teams  
**Author:** Sandesh (Lead System Architect)  
**Status:** Approved & Released  

This document defines the production-grade, highly-secure, and cost-efficient cloud architecture engineered for the V.I.S.I.O.N. Suite within Magellon's private Google Cloud Platform (GCP) network topology.

---

## 1. Cloud Infrastructure Diagram (Mermaid.js)

The following diagram defines the complete full-stack networking, hosting, and data routing paths. This can be copied and pasted directly into your Confluence page, where it will render into an interactive visual layout.

```mermaid
graph TD
    %% Define Styles & Colors matching our theme
    classDef user fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
    classDef gcp fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#e65100;
    classDef private fill:#efebe9,stroke:#5d4037,stroke-width:2px,color:#3e2723;
    classDef secret fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;

    %% 1. The Entry Point
    Dev[Magellon Software Developers]:::user
    User[End Users / Lead]:::user

    %% 2. Public GCP Ingress Layer
    subgraph Ingress_Layer [GCP Public Front End]
        DNS[Google Cloud DNS]:::gcp
        XLB[Global L7 External Load Balancer]:::gcp
        CertMap[GCP Certificate Map & SSL Policy]:::gcp
    end

    %% Connect Entry to Ingress
    Dev -->|Query/Chat| DNS
    User -->|Open Dashboard| DNS
    DNS -->|HTTPS Route| XLB
    XLB -.->|SSL Handshake| CertMap

    %% 3. Serverless Cloud Run Services
    subgraph Cloud_Run_Services [GCP Serverless Cloud Run Subnet]
        Frontend[vision-action-frontend <br> min: 0, max: 3]:::gcp
        Backend[vision-action-backend <br> min: 0, max: 3]:::gcp
    end

    %% Route Traffic from LB to Services
    XLB -->|Path: '/'| Frontend
    XLB -->|Path: '/api/*'| Backend

    %% 4. Secrets Vault
    subgraph Secret_Manager [Google Secret Manager]
        DB_Pass[vision-db-password <br> Version: latest]:::secret
        Conf_PAT[confluence-api-token <br> Version: latest]:::secret
        ADO_PAT[ado-pat-token <br> Version: latest]:::secret
    end

    %% Bind Secrets
    Backend -.->|Bind: PG_PASSWORD| DB_Pass
    Backend -.->|Bind: CONFLUENCE_PAT| Conf_PAT
    Backend -.->|Bind: ADO_PAT| ADO_PAT

    %% 5. Private VPC Network (Magellon Shared VPC)
    subgraph Magellon_Private_VPC [Magellon Shared VPC Network]
        VPC_Con[Serverless VPC Access Connector <br> 'vpc-con']:::private
        SQL_Gw[Cloud SQL Gateway VM Proxy <br> Port 5432]:::private
        Cloud_SQL[(Google Cloud SQL <br> PostgreSQL with pgvector <br> 10.102.16.5)]:::private
    end

    %% Route Backend Traffic (VPC Egress: PRIVATE_RANGES_ONLY)
    Backend -->|VPC Egress: PRIVATE_RANGES_ONLY| VPC_Con
    
    %% Private Routing
    VPC_Con -->|Private IP: 10.102.16.0/20| SQL_Gw
    SQL_Gw -->|Relational & Vector Data| Cloud_SQL

    %% 6. Public Internet SaaS
    subgraph Public_Internet [External Public SaaS]
        Confluence[Atlassian Confluence <br> worldline.atlassian.net]:::private
        ADO[Azure DevOps Cloud <br> dev.azure.com]:::private
    end

    %% Route Public Traffic (Bypasses VPC Connector!)
    Backend -->|Public IP Route| Confluence
    Backend -->|Public IP Route| ADO

    %% 7. Cloud Scheduler (Automated Loop)
    Scheduler[Google Cloud Scheduler <br> 'vision-confluence-sync-scheduler']:::gcp
    Scheduler -->|Every 3 Hours: POST /api/sync| XLB
```

---

## 2. Text-Based Layout Diagram

For inclusion inside internal memos, emails, or markdown-based logs, use the following clean layout structure:

```text
  [ Users / Developers ]
           │
           ▼ (HTTPS / Public DNS Domain)
  +───────────────────────────────────────────────────────────────────+
  │             GCP Global L7 External Load Balancer (XLB)            │
  +───┬───────────────────────────────────────────────────────────┬───+
      │ (Path: '/')                                               │ (Path: '/api/*')
      ▼                                                           ▼
  +─────────────────────────+                         +─────────────────────────+
  │ vision-action-frontend  │                         │  vision-action-backend  │
  │ (Cloud Run: scale 0-3)  │                         │ (Cloud Run: scale 0-3)  │
  +─────────────────────────+                         +───┬───────────────────┬─+
                                                          │                   │
                                     (Bind Secrets at Boot)                   │ (VPC Egress: PRIVATE_RANGES_ONLY)
                                                          ▼                   ▼
                                              +───────────────────────+   +───────────────────────+
                                              │ Google Secret Manager │   │ Serverless VPC Access │
                                              │  - vision-db-password │   │   Connector (vpc-con) │
                                              │  - confluence-pat     │   +───────────┬───────────+
                                              │  - ado-pat            │               │
                                              +───────────────────────+               ▼ (Private IP: 10.102.16.5)
                                                                          +───────────────────────+
                                                                          │  Cloud SQL PostgreSQL │
                                                                          │ (Relational/pgvector) │
                                                                          +───────────────────────+
```

---

## 3. Core Architectural Pillars (How It Works)

### 💸 3.1. True Serverless FinOps (Scale-to-Zero)
To eliminate any unnecessary cloud spend during off-hours, weekends, and holidays, both the Frontend and Backend Cloud Run services are configured via Terraform to scale down automatically:
*   **`min_instance_count = 0`**
*   *Financial Impact:* When there is no active developer traffic, GCP completely deallocates all running containers. Your operational computing cost drops to exactly **€0.00**, making the entire pilot cost **less than $30.00/month** (only paying for the quiet, static PostgreSQL storage SSD).

### 🔒 3.2. Private, Locked Database Communication
The Google Cloud SQL PostgreSQL instance (`10.102.16.5`) is deployed **without a public IP address**. It is entirely isolated from the public internet:
*   The Cloud Run backend communicates with the database securely using your project's **Serverless VPC Access Connector (`vpc-con`)** over private IP ranges.
*   This private route is protected by Magellon's central VPC firewalls and gateways, preventing any external data-access vulnerabilities.

### 🌐 3.3. Hybrid Traffic Egress Routing (`PRIVATE_RANGES_ONLY`)
One of the most powerful optimizations is the split-egress routing configured in your Cloud Run networking settings:
*   By setting the VPC egress parameter to **`PRIVATE_RANGES_ONLY`** (instead of routing all traffic through the private subnet), we split outgoing requests:
    *   **Private requests (PostgreSQL / private IPs):** Safely route through the VPC connector.
    *   **Public requests (Atlassian Confluence & Azure DevOps):** Route directly over Google's public network backbone. This completely unblocks the 20-second connection timeout, bypassing the need for complex proxy setups while maintaining complete database isolation!

### ⚙️ 3.4. Secure Runtime Secrets Binding
Highly sensitive credentials (database passwords, Confluence PATs, Azure DevOps PATs) are **never** stored inside the container images or written to local disks in plain text.
*   All credentials are saved in **GCP Secret Manager** as secure, encrypted secrets.
*   On boot, Google's hypervisor dynamically and securely mounts these secrets directly into the container's memory space (as `PG_PASSWORD`, `CONFLUENCE_PAT`, and `ADO_PAT`).
*   This ensures the platform complies 100% with Magellon's strict InfoSec regulations.
