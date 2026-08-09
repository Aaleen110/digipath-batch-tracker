# Task 7 — Delegation Brief

## What I'd hand off

I would delegate the `/batches/{id}/notify` webhook functionality to a freelance developer.
This is a well-defined unit of work with clear inputs and outputs.
Send completed batch results to a partner webhook, handle failures, and ensure reliable delivery.

I would keep core components such as authentication, database schema, and concurrency-safe status transitions in-house because they directly impact system security and data integrity.

## Task Brief

Implement webhook notification handling for completed batches.

The service should:
- Send batch results to the partner webhook URL stored for that batch.
- Handle partner failures using retries with exponential backoff.
- Provide clear success and failure responses.

## Acceptance Criteria

1. All outbound webhook requests must have a timeout configured to prevent indefinite blocking.

2. Failed requests caused by network errors, timeouts, or server errors should retry a limited number of times using increasing delays.

3. The API should only report success after receiving a successful response from the partner system.

4. Webhook URLs must be validated before sending requests to prevent unsafe outbound calls (for example, internal/private network targets).

5. Duplicate notification requests should be handled safely to avoid accidental duplicate delivery.

6. Automated tests should cover:
   - Successful webhook delivery
   - Partner API failure and retry behavior
   - Timeout scenarios
   - Duplicate notification handling

7. No secrets should be committed in code. Configuration values must come from environment variables.

## Freelancer Security Considerations

Before providing access:
- Share only a development/staging environment, never production credentials.
- Provide limited repository permissions and require changes through pull requests only.
- We enable branch protection rules, before delegation.
- Review any new dependencies before approval.
- Remove access and rotate credentials after the task is completed.
- Ensure an NDA is signed before sharing proprietary code.