from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

import requests

class HttpClient:
    def __init__(
        self,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: int = 20,
        max_retries: int = 2,
        backoff_seconds: float = 0.5,
        proxy_url: Optional[str] = None,
    ) -> None:
        self.session = requests.Session()
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", {})
        merged_headers = {**self.default_headers, **headers}
        attempt = 0
        last_exc = None

        while attempt <= self.max_retries:
            try:
                resp = self.session.request(
                    method=method,
                    url=url,
                    headers=merged_headers,
                    timeout=self.timeout,
                    proxies=self.proxies,
                    **kwargs,
                )
                if 200 <= resp.status_code < 300:
                    return resp
                elif 400 <= resp.status_code < 500:
                    # Do not retry on client errors
                    resp.raise_for_status()
                else:
                    # Server error -> retry
                    last_exc = Exception(f"HTTP {resp.status_code}: {resp.text[:256]}")
            except requests.RequestException as e:
                last_exc = e

            attempt += 1
            if attempt <= self.max_retries:
                time.sleep(self.backoff_seconds * attempt)

        if last_exc:
            raise last_exc
        raise RuntimeError("Request failed without an exception (unexpected)")

    def get_text(self, url: str, **kwargs) -> str:
        resp = self._request("GET", url, **kwargs)
        return resp.text

    def get_json(self, url: str, **kwargs) -> Any:
        resp = self._request("GET", url, **kwargs)
        # Try content-type first
        ctype = resp.headers.get("content-type", "")
        if "application/json" in ctype:
            return resp.json()
        # Best-effort parse
        return json.loads(resp.text)