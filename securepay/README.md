# SecurePay – Policy-Driven Secure Payment Workflow

## Problem Statement

Design and implement a policy‑driven secure payment and approval workflow for high‑risk transactions, ensuring that no sensitive payment can be executed without passing clearly defined role‑based checks, policy rules, and auditability guarantees.

**Domain:** FinTech – financial systems with strong security and trust, focused on secure transaction workflows with budget limits and risk policies.[file:36]

## Core Features

- Roles: Admin, Initiator, Approver.
- Payment requests with beneficiaries, amounts, purposes, and status lifecycle.
- Policy engine:
  - High-amount threshold → multiple approvals.
  - New beneficiary → high-risk flag, admin approval required.
- Maker–checker enforcement (no self-approval).
- Approval workflow: Pending → Approved/Rejected → Executed (simulated).
- Full audit log of all actions.

## Architecture Overview

- Django web app (`securepay` project, `payments` app).
- PostgreSQL database (via Docker Compose).
- Containerized deployment with:
  - `web`: Django + Gunicorn/dev server.
  - `db`: Postgres 15.

## Setup and Run

Prerequisites: Docker and Docker Compose installed.[file:36]

```bash
docker compose up --build
