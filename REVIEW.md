## Task 4 — Code Review

I'd classify the issues into 3 groups
(I) Blockers - must fix before merge
(II) High Priority - fix soon
(III) Improvements - not blocker, but improvements to do.

### BLOCKERS

### 1. SQL Injection issue

**Issue:**  
The database query directly uses user input:

```python
f"SELECT * FROM batches WHERE id = {batch_id}"
```
This allows attackers to inject malicious SQL commands.

**Request:**
Use parameterized queries or ORM filters instead of building SQL strings manually.

### 2. Missing authentication and authorization

**Issue:**
The endpoint does not verify who is calling it. Anyone who can access this API could trigger partner notifications.

**Request:**
Add authentication and authorization checks before allowing notification requests.


### 3. Hardcoded API key

**Issue:**
The API key is stored directly in source code and may be exposed through git history.

**Request:**
Move secrets to environment variables or a secrets manager. Remove this key from the repository and rotate it.

### 4. Unsafe webhook URL handling (SSRF risk)

**Issue:**
The application sends requests to a webhook URL without validating it. A malicious URL could potentially target internal services.

**Request:**
Validate webhook URLs before making outbound requests. Only allow safe destinations (for example HTTPS URLs and block private/internal IP addresses).

### HIGH PRIORITY

### 5. Missing batch existence handling

**Issue:**
If the batch does not exist, accessing batch['partner_webhook'] will cause an exception and return an unclear server error.

**Request:**
Check whether the batch exists and return a proper 404 Not Found response.

### 6. No timeout on external API call

**Issue:**
requests.post() does not define a timeout. A slow partner service could block application workers indefinitely.

**Request:**
Add an explicit timeout for outbound requests.

Example:

```python
requests.post(
    partner_url,
    json=payload,
    timeout=5
)
```

### 7. Incorrect success response

**Issue:**
The endpoint always returns:
```json
{
  "sent": true
}
```

even if the webhook request fails.

**Request:**
Handle request failures properly and only return success after confirming the partner received the notification.

### IMPROVEMENTS

### 8. Add retry handling

**Issue:**
Partner services can fail temporarily due to network issues or downtime.

**Request:**
Add bounded retries with exponential backoff, and move webhook delivery to a background queue.

### 9. Add idempotency protection

**Issue:**
Repeated calls to this endpoint could send duplicate notifications.

**Request:**
Track notification status or use an idempotency key to prevent duplicate webhook deliveries.

### 10. Add logging and monitoring

**Issue:**
There is no visibility into notification attempts or failures.

**Request:**
Add structured logs containing batch ID, webhook status, response code, and failure reason.

### 11. Validate request input

**Issue:**
batch_id is not validated before being used.

**Request:**
Validate input format and reject invalid values early.