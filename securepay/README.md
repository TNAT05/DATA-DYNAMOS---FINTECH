# SecurePay - Build2Break Hackathon

**Domain**: FinTech - Policy-driven secure payment and approval workflow for high-risk transactions.

## Problem Statement
In high-stakes financial environments, single points of failure (checking your own work) lead to fraud. SecurePay implements a strict **Maker-Checker** workflow with **Policy-Driven Approvals** to ensure no transaction, especially high-value or to new beneficiaries, occurs without appropriate oversight.

## Architecture
- **Stack**: Django 5.0 (Python 3.11), PostgreSQL 15.
- **Deployment**: Docker Compose.
- **Security**: 
  - Role-Based Access Control (RBAC).
  - State Machine enforcement (PENDING -> APPROVED -> EXECUTED).
  - Immutable Audit Logs.

## Setup Instructions

### Prerequisites
- Docker & Docker Compose

### Running the App (Docker)
1. **Build and Start**:
   ```bash
   docker-compose up --build
   ```
   *The app will be available at `http://localhost:8000`.*

### Running the App (Local Python)
If you prefer running without Docker:
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Apply Migrations**:
   ```bash
   python manage.py migrate
   ```
3. **Start Server**:
   ```bash
   python manage.py runserver
   ```
   *Access at `http://127.0.0.1:8000`*

2. **Default Users** (Password: `password123`):
   - **Initiator**: `initiator` (Can create payments)
   - **Approver 1**: `approver1` (Can approve/reject)
   - **Approver 2**: `approver2` (Can approve/reject)
   - **Admin**: `admin` (Can approve & **execute** payments)

## Key Invariants & Rules
1. **Maker-Checker**: Initiators cannot approve their own payments.
2. **Double Approval**: Payments > ₹50,000 require 2 distinct approvals.
3. **High Risk Config**: Payments to NEW beneficiaries require Admin approval.
4. **Execution Gate**: Only Admins can execute, and ONLY after status is APPROVED.
5. **Audit Trail**: Every action (Create, Approve, Execute) is logged.

## Testing Guide (Happy Paths)

### Scenario 1: Simple Payment
1. Login as `initiator`.
2. Create payment for ₹10,000 to "TrustedVendor".
3. Status: **PENDING**.
4. Login as `approver1`.
5. Approve payment.
6. Status: **APPROVED** (Ready for execution).
7. Login as `admin`.
8. Click **Execute**.
9. Status: **EXECUTED**.

### Scenario 2: High Value Transaction
1. Login as `initiator`.
2. Create payment for ₹60,000 to "BigCorp".
3. Login as `approver1`. Approve. Status remains **PENDING** (Needs 1 more).
4. Login as `approver2`. Approve. Status becomes **APPROVED**.
5. Login as `admin`. Execute.

### Scenario 3: New Beneficiary Risk
1. Login as `initiator`.
2. Create payment to "UnknownGuy".
3. Login as `approver1`. Approve. Status **PENDING**.
4. Login as `admin`. Approve. Status **APPROVED**. (Admin approval was mandatory).
5. Admin executes.

## Assumptions
- "New Beneficiary" is defined as any beneficiary name not associated with a previously EXECUTED payment.
- Currency is fixed to INR.
