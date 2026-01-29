# Postman Test Cases for API + Postgres Playground

These cases validate core API behavior using Postman. Use `X-API-Key: local-dev-key`.

## Environment setup
- `baseUrl`: `http://localhost:8000`
- `apiKey`: `local-dev-key`

## Common headers
- `X-API-Key`: `{{apiKey}}`
- `Content-Type`: `application/json`

## Test Cases

### 1) Health Check
- Method: `GET`
- URL: `{{baseUrl}}/health`
- Expected: `200`, body `{ "status": "ok" }`
- Tests:
  - Status code is 200
  - Response JSON has `status == "ok"`

### 2) Readiness Check
- Method: `GET`
- URL: `{{baseUrl}}/health/ready`
- Expected: `200`
- Tests:
  - `status` is `ok` or `degraded`
  - `db` is boolean
  - `pool_ready` is boolean

### 3) Create Item (Valid)
- Method: `POST`
- URL: `{{baseUrl}}/items`
- Body:
  ```json
  { "name": "postman-item", "description": "from postman" }
  ```
- Expected: `201`
- Tests:
  - `id` is present
  - `name` and `description` match
- Save `id` to environment: `itemId`

### 4) Get Item by ID
- Method: `GET`
- URL: `{{baseUrl}}/items/{{itemId}}`
- Expected: `200`
- Tests:
  - `id` matches `itemId`
  - `name` and `description` match

### 5) List Items
- Method: `GET`
- URL: `{{baseUrl}}/items`
- Expected: `200`
- Tests:
  - Response is array
  - Contains at least one item

### 6) List Items with Pagination
- Method: `GET`
- URL: `{{baseUrl}}/items?limit=1&offset=0`
- Expected: `200`
- Tests:
  - Response is array
  - Array length equals 1

### 7) Search Items
- Method: `GET`
- URL: `{{baseUrl}}/items/search?name=postman`
- Expected: `200`
- Tests:
  - Response is array
  - Array contains item with `name` including `postman`

### 8) Search without name
- Method: `GET`
- URL: `{{baseUrl}}/items/search`
- Expected: `200`
- Tests:
  - Response is empty array

### 9) Update Item
- Method: `PUT`
- URL: `{{baseUrl}}/items/{{itemId}}`
- Body:
  ```json
  { "name": "postman-item", "description": "updated" }
  ```
- Expected: `200`
- Tests:
  - `description` equals `updated`

### 10) Delete Item
- Method: `DELETE`
- URL: `{{baseUrl}}/items/{{itemId}}`
- Expected: `204`

### 11) Get Deleted Item
- Method: `GET`
- URL: `{{baseUrl}}/items/{{itemId}}`
- Expected: `404`

### 12) Unauthorized (Missing API Key)
- Method: `POST`
- URL: `{{baseUrl}}/items`
- Body:
  ```json
  { "name": "no-auth", "description": "fail" }
  ```
- Expected: `401`

### 13) Unauthorized (Invalid API Key)
- Method: `POST`
- URL: `{{baseUrl}}/items`
- Header: `X-API-Key: wrong-key`
- Body:
  ```json
  { "name": "bad-auth", "description": "fail" }
  ```
- Expected: `401`

### 14) Validation (Missing name)
- Method: `POST`
- URL: `{{baseUrl}}/items`
- Body:
  ```json
  { "description": "missing name" }
  ```
- Expected: `422`

### 15) Validation (Name too long)
- Method: `POST`
- URL: `{{baseUrl}}/items`
- Body:
  ```json
  { "name": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "description": "too long" }
  ```
- Expected: `422`

### 16) Not Found (Update missing)
- Method: `PUT`
- URL: `{{baseUrl}}/items/999999`
- Body:
  ```json
  { "name": "missing", "description": "none" }
  ```
- Expected: `404`

### 17) Not Found (Delete missing)
- Method: `DELETE`
- URL: `{{baseUrl}}/items/999999`
- Expected: `404`

### 18) Security Headers
- Method: `GET`
- URL: `{{baseUrl}}/health`
- Expected headers:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `Cache-Control: no-store`

### 19) Rate Limit Headers
- Method: `GET`
- URL: `{{baseUrl}}/items`
- Expected headers:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`

### 20) Request ID Echo
- Method: `GET`
- URL: `{{baseUrl}}/health`
- Header: `X-Request-Id: postman-req-1`
- Expected:
  - Response header `X-Request-Id` equals `postman-req-1`

### 21) Security Headers on Authenticated Endpoint
- Method: `GET`
- URL: `{{baseUrl}}/items`
- Expected headers:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `Cache-Control: no-store`

### 22) Search with Pagination
- Method: `GET`
- URL: `{{baseUrl}}/items/search?name=postman&limit=1&offset=0`
- Expected: `200`
- Tests:
  - Response is array
  - Array length <= 1

### 23) Rate Limit Enforcement (Optional)
- Method: `GET`
- URL: `{{baseUrl}}/items`
- Steps:
  - Send requests quickly in a loop to exceed limit (default 1000/min; set `RATE_LIMIT_PER_MINUTE=5` to test).
- Expected:
  - Eventually returns `429` with `Retry-After`

### 24) Invalid Query Params (Optional)
- Method: `GET`
- URL: `{{baseUrl}}/items?limit=-1&offset=-1`
- Expected:
  - Behavior documented (either returns 200 with defaults or 422 if validation is added)

### 25) SQL Injection-like Payload
- Method: `POST`
- URL: `{{baseUrl}}/items`
- Body:
  ```json
  { "name": "x'); DROP TABLE items; --", "description": "inj" }
  ```
- Expected: `201`
- Tests:
  - Item is created and data is stored as plain text
