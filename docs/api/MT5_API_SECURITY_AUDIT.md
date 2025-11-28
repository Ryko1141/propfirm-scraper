# MT5 REST API Security Audit Report

**Date:** November 28, 2025  
**Auditor:** GitHub Copilot  
**API Version:** 1.0.0  
**Focus Areas:** Session Handling, Rate Limits, Input Validation, Reverse Proxy Configuration

---

## Executive Summary

The MT5 REST API has been audited for security vulnerabilities across four key areas. This report identifies critical findings and provides actionable recommendations.

**Overall Risk Assessment:** MEDIUM  
**Critical Issues:** 2  
**High Priority Issues:** 3  
**Medium Priority Issues:** 2

---

## 1. Session Management Security

### Current Implementation

**Location:** `src/mt5_api.py` lines 95-165

#### ✅ Strengths:
- **Secure Token Generation:** Uses `secrets.token_urlsafe(32)` (256-bit entropy)
- **Password Hashing:** SHA-256 hashing prevents plain-text password storage
- **Expiration Mechanism:** 24-hour token expiration (configurable)
- **Automatic Cleanup:** Expired sessions checked on access
- **Bearer Token Authentication:** Industry-standard HTTP authentication
- **Session Isolation:** Each client gets independent MT5Client connection

#### ❌ Critical Issues:

1. **In-Memory Session Storage (CRITICAL)**
   - **Risk:** Server restart = all sessions lost
   - **Attack Vector:** DoS via memory exhaustion
   - **Impact:** Sessions not persistent across restarts
   - **Recommendation:** 
     ```python
     # Migrate to Redis
     import redis
     redis_client = redis.Redis(host='localhost', port=6379, db=0)
     
     def create_session(account_number, password, server, path, client):
         token = generate_session_token()
         session_data = {
             "account_number": account_number,
             "password_hash": hashlib.sha256(password.encode()).hexdigest(),
             "server": server,
             "created_at": datetime.now().isoformat(),
             "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
         }
         redis_client.setex(f"session:{token}", 86400, json.dumps(session_data))
         return token
     ```

2. **No Session Refresh Mechanism (HIGH)**
   - **Risk:** Users forced to re-authenticate every 24 hours
   - **Impact:** Poor UX, credential exposure risk
   - **Recommendation:** Add refresh token endpoint
     ```python
     @app.post("/api/v1/refresh")
     async def refresh_token(session: Dict = Depends(get_current_session)):
         # Extend expiration by 24 hours
         new_expires = datetime.now() + timedelta(hours=24)
         session["expires_at"] = new_expires
         return {"expires_at": new_expires.isoformat()}
     ```

3. **No Session Revocation List (MEDIUM)**
   - **Risk:** Compromised tokens valid until expiration
   - **Recommendation:** Implement token blacklist in Redis

4. **Weak Password Hashing (MEDIUM)**
   - **Current:** SHA-256 (fast, vulnerable to rainbow tables)
   - **Recommendation:** Use bcrypt/Argon2
     ```python
     import bcrypt
     password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
     ```

5. **No Concurrent Session Limits (HIGH)**
   - **Risk:** Single account can spawn unlimited sessions
   - **Attack Vector:** Session flooding
   - **Recommendation:** Track sessions per account, limit to 5

---

## 2. Rate Limiting

### Current Implementation

**Status:** ❌ **NOT IMPLEMENTED** (CRITICAL)

#### Vulnerabilities:

1. **No Request Rate Limiting**
   - **Risk:** Brute force attacks on `/api/v1/login`
   - **Risk:** API abuse and resource exhaustion
   - **Attack Scenario:** Attacker can attempt 1000s of login attempts/second

2. **No Account Lockout**
   - **Risk:** Unlimited password attempts

3. **No IP-based Throttling**
   - **Risk:** Single IP can flood API

#### Recommendations:

**Option 1: Application-Level (SlowAPI)**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/login")
@limiter.limit("5/minute")  # 5 login attempts per minute
async def login(request: Request, login_data: MT5LoginRequest):
    ...

@app.get("/api/v1/account")
@limiter.limit("60/minute")  # 60 requests per minute
async def get_account_info(session: Dict = Depends(get_current_session)):
    ...
```

**Option 2: Nginx Reverse Proxy (RECOMMENDED)**
```nginx
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;

server {
    location /api/v1/login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://localhost:8000;
    }
    
    location /api/v1/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://localhost:8000;
    }
}
```

**Priority:** CRITICAL - Implement immediately

---

## 3. Input Validation

### Current Implementation

**Location:** `src/mt5_api.py` Pydantic models (lines 36-89)

#### ✅ Strengths:
- **Pydantic Validation:** Type-safe request/response models
- **Field Constraints:** Required fields enforced
- **Type Coercion:** Automatic type checking

#### ⚠️ Issues Found:

1. **No Account Number Range Validation (LOW)**
   ```python
   # Current
   account_number: int
   
   # Should be
   account_number: int = Field(..., ge=1000, le=99999999, 
                               description="MT5 account (4-8 digits)")
   ```

2. **No Password Complexity Requirements (MEDIUM)**
   ```python
   password: str = Field(..., min_length=8, max_length=128)
   ```

3. **No Server Name Whitelist (MEDIUM)**
   - **Risk:** Connection attempts to arbitrary servers
   - **Recommendation:**
     ```python
     from enum import Enum
     
     class MT5Server(str, Enum):
         FTMO_DEMO = "FTMO-Demo"
         FTMO_LIVE = "FTMO-Live"
         METAQUOTES_DEMO = "MetaQuotes-Demo"
         # Add approved servers
     
     server: MT5Server = Field(...)
     ```

4. **No Path Traversal Protection (HIGH)**
   ```python
   # Current
   path: Optional[str] = None
   
   # Should validate and sanitize
   import os
   if path:
       path = os.path.normpath(path)
       if not path.startswith("C:\\Program Files\\"):
           raise ValueError("Invalid MT5 path")
   ```

5. **No Request Size Limits (MEDIUM)**
   - FastAPI default: 100MB (too large)
   - **Recommendation:**
     ```python
     app = FastAPI(max_request_size=1_000_000)  # 1MB limit
     ```

#### Overall Input Validation: ✅ GOOD (with recommended improvements)

---

## 4. Reverse Proxy Configuration

### Recommended Setup: Nginx + SSL/TLS

#### Configuration File: `nginx_mt5_api.conf`

```nginx
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
limit_req_zone $binary_remote_addr zone=global:10m rate=100r/m;

# Connection limiting
limit_conn_zone $binary_remote_addr zone=addr:10m;

# Upstream backend
upstream mt5_api_backend {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# HTTP redirect to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your_cert.pem;
    ssl_certificate_key /etc/ssl/private/your_key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Request size limit
    client_max_body_size 1M;
    
    # Connection limit (max 10 connections per IP)
    limit_conn addr 10;
    
    # Global rate limit
    limit_req zone=global burst=50 nodelay;

    # Login endpoint (strict rate limit)
    location /api/v1/login {
        limit_req zone=login burst=3 nodelay;
        
        proxy_pass http://mt5_api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }

    # API endpoints (moderate rate limit)
    location /api/v1/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://mt5_api_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Pass Authorization header
        proxy_pass_header Authorization;
        
        # Timeout settings
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Health check (no rate limit)
    location /health {
        proxy_pass http://mt5_api_backend;
        access_log off;
    }

    # Documentation (light rate limit)
    location /docs {
        limit_req zone=api burst=5 nodelay;
        proxy_pass http://mt5_api_backend;
    }

    # Block direct access to internal endpoints
    location /internal/ {
        deny all;
        return 403;
    }

    # Logging
    access_log /var/log/nginx/mt5_api_access.log;
    error_log /var/log/nginx/mt5_api_error.log warn;
}
```

#### Setup Script: `setup_nginx_proxy.sh`

```bash
#!/bin/bash

echo "Setting up Nginx reverse proxy for MT5 API..."

# Install Nginx
sudo apt-get update
sudo apt-get install -y nginx

# Copy configuration
sudo cp nginx_mt5_api.conf /etc/nginx/sites-available/mt5_api
sudo ln -s /etc/nginx/sites-available/mt5_api /etc/nginx/sites-enabled/

# Generate self-signed certificate (for testing)
sudo mkdir -p /etc/ssl/private
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/mt5_api.key \
    -out /etc/ssl/certs/mt5_api.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=api.yourdomain.com"

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

echo "✓ Nginx reverse proxy configured"
echo "Access API at: https://api.yourdomain.com"
```

#### Benefits:
- ✅ SSL/TLS encryption
- ✅ Rate limiting (5 login/min, 60 API requests/min)
- ✅ Connection limiting (10 per IP)
- ✅ DDoS protection
- ✅ Request size limiting
- ✅ Security headers
- ✅ Access logging
- ✅ Load balancing ready

---

## 5. Additional Security Recommendations

### 5.1 API Key Authentication (Alternative)

For server-to-server communication, consider API keys:

```python
API_KEYS = {
    "sk_live_abc123": {"name": "Production Client", "rate_limit": 1000},
    "sk_test_xyz789": {"name": "Test Client", "rate_limit": 100}
}

async def verify_api_key(api_key: str = Header(...)):
    if api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return API_KEYS[api_key]
```

### 5.2 Audit Logging

```python
import logging

audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
handler = logging.FileHandler("audit.log")
audit_logger.addHandler(handler)

@app.post("/api/v1/login")
async def login(request: Request, login_data: MT5LoginRequest):
    ip = request.client.host
    audit_logger.info(f"Login attempt - Account: {login_data.account_number}, IP: {ip}")
    ...
```

### 5.3 HTTPS Enforcement

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if os.getenv("ENV") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

### 5.4 Content Security Policy

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

## Priority Action Items

### Immediate (Critical)
1. ✅ Implement rate limiting (Nginx or SlowAPI)
2. ✅ Set up Nginx reverse proxy with SSL/TLS
3. ✅ Migrate session storage to Redis

### Short-term (High)
4. Add session refresh mechanism
5. Implement concurrent session limits
6. Add path traversal protection
7. Strengthen password hashing (bcrypt)

### Medium-term
8. Add API key authentication option
9. Implement audit logging
10. Add request size limits
11. Server name whitelist

---

## Testing Recommendations

1. **Penetration Testing:**
   - OWASP ZAP automated scan
   - Burp Suite manual testing
   - SQL injection attempts (not applicable - no SQL)
   - Session fixation tests

2. **Load Testing:**
   - Use provided `test_mt5_api_load.py`
   - Test rate limiting effectiveness
   - Measure response times under load

3. **Security Scanning:**
   ```bash
   # Dependency vulnerability scan
   pip-audit
   
   # Static analysis
   bandit -r src/
   
   # Secret scanning
   truffleHog --regex --entropy=False .
   ```

---

## Compliance Considerations

- **GDPR:** Session data contains account numbers (PII) - add privacy policy
- **PCI DSS:** Not applicable (no card data)
- **SOC 2:** Audit logging required for Type II certification
- **ISO 27001:** Implement all critical recommendations

---

## Conclusion

The MT5 REST API has a solid foundation with good session management and input validation. However, **critical vulnerabilities exist** around rate limiting and production session storage. 

**Action Required:** Implement rate limiting and reverse proxy configuration **before production deployment**.

**Estimated Implementation Time:** 4-6 hours

---

**Report End**
