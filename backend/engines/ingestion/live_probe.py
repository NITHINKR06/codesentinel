import httpx
from typing import List, Dict
import structlog

log = structlog.get_logger()

SECURITY_HEADERS = [
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Strict-Transport-Security",
    "Referrer-Policy",
    "Permissions-Policy",
    "X-XSS-Protection",
]

EXPOSED_PATHS = [
    "/.env", "/.env.local", "/.env.production",
    "/admin", "/admin/login", "/phpmyadmin",
    "/wp-admin", "/wp-login.php",
    "/.git/config", "/.git/HEAD",
    "/api/v1/users", "/api/users",
    "/debug", "/console", "/actuator/health",
    "/swagger-ui.html", "/api-docs", "/openapi.json",
    "/server-status", "/phpinfo.php",
]


async def probe_live_url(url: str) -> List[Dict]:
    findings = []
    url = url.rstrip("/")

    async with httpx.AsyncClient(
        timeout=10, follow_redirects=True,
        verify=False, headers={"User-Agent": "CodeSentinel-Scanner/1.0"}
    ) as client:

        # Check security headers
        try:
            resp = await client.get(url)
            missing_headers = [h for h in SECURITY_HEADERS if h.lower() not in {k.lower() for k in resp.headers}]
            for header in missing_headers:
                findings.append({
                    "type": "missing_security_header",
                    "severity": "medium",
                    "title": f"Missing {header}",
                    "description": f"The response is missing the {header} security header.",
                    "plain_impact": f"Attackers can exploit the missing {header} header to conduct clickjacking or injection attacks.",
                    "file_path": url,
                    "vuln_type": "missing_header",
                })

            # Check CORS misconfiguration
            cors = resp.headers.get("Access-Control-Allow-Origin", "")
            if cors == "*":
                findings.append({
                    "type": "cors_misconfiguration",
                    "severity": "high",
                    "title": "CORS allows all origins (*)",
                    "description": "Access-Control-Allow-Origin is set to wildcard.",
                    "plain_impact": "Any website can make authenticated requests to your API on behalf of your users.",
                    "file_path": url,
                    "vuln_type": "cors",
                })
        except Exception as e:
            log.warning("Could not fetch base URL", url=url, error=str(e))

        # Probe exposed paths
        for path in EXPOSED_PATHS:
            try:
                r = await client.get(f"{url}{path}")
                if r.status_code in (200, 403):
                    findings.append({
                        "type": "exposed_path",
                        "severity": "high" if ".env" in path or ".git" in path else "medium",
                        "title": f"Exposed path: {path}",
                        "description": f"The path {path} returned HTTP {r.status_code}.",
                        "plain_impact": f"Attackers can access sensitive data or admin interfaces at {path}.",
                        "file_path": f"{url}{path}",
                        "vuln_type": "exposed_endpoint",
                    })
            except Exception:
                pass

    log.info("Live probe complete", url=url, findings=len(findings))
    return findings
