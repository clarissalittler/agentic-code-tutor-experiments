# Shared Linux Server API Key Lockdown Plan (Deferred)

Status: Deferred (planning only, no implementation in this document)  
Date: February 10, 2026  
Owner: Code Tutor maintainers

## 1. Problem

We want students on a shared Linux server to use Code Tutor, while preventing access to the real upstream LLM provider key.

Directly running Code Tutor with the upstream key in user-visible config/env is not secure on a shared host. Even if edits are locked, a determined local user can often recover secrets from process/env/config exposure paths.

## 2. Security Goal

- Students can use Code Tutor normally.
- The real Anthropic/OpenAI key never appears in student-owned files, env vars, or processes.
- Access can be revoked/rate-limited per student.

## 3. Recommended Architecture

Use a server-side LLM gateway/proxy:

1. Root-owned gateway service stores upstream provider key.
2. Code Tutor clients talk only to gateway (OpenAI-compatible endpoint).
3. Students authenticate with scoped gateway credentials (or Unix-socket identity), not upstream key.
4. Gateway enforces policy: model allowlist, quotas, rate limits, audit logs.

### Logical Flow

```
Student code-tutor CLI
  -> local/shared gateway endpoint
  -> gateway attaches upstream provider key
  -> upstream provider API
```

## 4. Why This Works

- Secret boundary moves to root-controlled service.
- Student credentials are replaceable and limited.
- Central policy controls abuse, spend, and model scope.

## 5. Deployment Shape

## 5.1 Gateway Service

- Run as dedicated system user (for example: `code-tutor-gateway`), managed by `systemd`.
- Bind to:
  - `127.0.0.1:<port>` if only local server users need access, or
  - private network interface + firewall rules if remote clients are allowed.
- Store upstream key in root-owned env file:
  - permissions: `root:root`, mode `0600`
- Optional gateway choices:
  - lightweight custom FastAPI proxy,
  - or existing OpenAI-compatible proxy tooling.

## 5.2 Student Authentication

Preferred options (strongest to simplest):

1. Per-user token issued by gateway (header-based auth).
2. Unix domain socket + group permission model (single-host deployments).
3. Internal-network unauthenticated mode (only if host isolation is strong and acceptable).

## 5.3 Policy Controls at Gateway

- Per-user rate limits (requests/minute).
- Daily/monthly token or cost quotas.
- Model allowlist/blocklist.
- Max prompt/completion size caps.
- Timeout and retry policy.
- Structured request/response audit (redacted where required).

## 6. Code Tutor Integration Plan

Current Code Tutor already supports:

- `provider = "openai_compatible"`
- configurable `base_url`

So students can be pointed to gateway with minimal client-side change.

Recommended shared-server config model:

- System config (`/etc/code-tutor/config.json`) sets:
  - `provider: "openai_compatible"`
  - `base_url: "http://127.0.0.1:<gateway-port>/v1"`
  - default `model`
  - `api_key_locked: true` (for student config control)
- Student user config keeps personal preferences only.

Important: if students need gateway tokens, those tokens are still credentials. They are lower-risk than upstream keys, but should still be scoped, rotatable, and monitored.

## 7. Phased Rollout

## Phase 0: Design Decisions

- Choose gateway implementation.
- Decide auth mode (per-user token vs socket identity).
- Define quota/rate policy and model allowlist.
- Define logging/privacy policy.

Exit criteria:
- Written policy doc and threat model approved.

## Phase 1: Pilot (1 shared server)

- Deploy gateway as systemd service.
- Configure Code Tutor system config to gateway.
- Onboard small student cohort.
- Enable strict spend + rate limits.

Exit criteria:
- Students can run review/teach/proof/roguelike without upstream key exposure.
- No key leakage path found in pilot review.

## Phase 2: Hardening

- Add credential rotation workflow.
- Add per-user usage dashboards/alerts.
- Add incident response playbook for compromised student token.
- Add integration tests for gateway failure modes (timeouts, 429, 5xx).

Exit criteria:
- Operational runbook complete.
- Monitoring and alerting active.

## Phase 3: Production Rollout

- Expand to all sections/classes.
- Enforce quotas and automated alerting.
- Schedule periodic security review.

## 8. Operational Runbook Requirements

- Key rotation: upstream provider key and gateway signing/secret keys.
- Student token issuance and revocation process.
- Budget alarms and automatic throttling policy.
- Gateway outage fallback behavior and communication plan.

## 9. Risks and Mitigations

- Risk: students share gateway tokens.
  - Mitigation: per-user tokens, anomaly detection, quick revoke/rotate.
- Risk: overuse/spend spikes.
  - Mitigation: quotas + hard caps + alerts.
- Risk: sensitive prompt data in logs.
  - Mitigation: redaction defaults, minimum-retention logs, access controls.

## 10. Acceptance Criteria (Future Implementation)

1. Upstream provider key is never present in student-owned files or shell env.
2. Students can still use core Code Tutor modes successfully.
3. Per-student revocation and quota control is verified.
4. Gateway and Code Tutor configs are reproducible from documented runbook.

## 11. Deferred Scope Note

This document intentionally defers implementation.  
No gateway service, auth flow, or Code Tutor behavior was changed as part of this planning artifact.
