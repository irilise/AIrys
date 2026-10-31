#!/usr/bin/env python3
"""Smoke-test the running frontend, backend, and Ollama-backed chat flow."""
import argparse
import json
import os
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


FRONTEND_URL = os.getenv("AIRYS_FRONTEND_URL", "http://localhost:3000").rstrip("/")
BACKEND_URL = os.getenv("AIRYS_BACKEND_URL", "http://localhost:7860").rstrip("/")
OLLAMA_URL = os.getenv("OLLAMA_TEST_HOST", "http://localhost:11434").rstrip("/")
FALLBACK_MODEL = os.getenv("OLLAMA_TEST_MODEL", "llama3.2:1b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TEST_TIMEOUT", "3600"))
REQUEST_TIMEOUT = int(os.getenv("AIRYS_TEST_TIMEOUT", "240"))


class SmokeTestError(Exception):
    """Raised when a running service fails a smoke check."""


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []

    def handle_starttag(self, _tag, attributes):
        attributes = dict(attributes)
        for attribute in ("src", "href"):
            asset = attributes.get(attribute)
            if asset and asset.startswith("/") and not asset.startswith("//"):
                self.assets.append(asset)


def request(url, method="GET", payload=None, timeout=REQUEST_TIMEOUT):
    data = None
    headers = {"Accept": "application/json, text/html"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            body = response.read()
            content_type = response.headers.get("Content-Type", "")
            return response.status, body, content_type
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise SmokeTestError(f"{method} {url} returned HTTP {error.code}: {detail[:500]}") from error
    except (URLError, TimeoutError, OSError) as error:
        raise SmokeTestError(f"{method} {url} failed: {error}") from error


def request_json(url, method="GET", payload=None, timeout=REQUEST_TIMEOUT):
    status, body, _ = request(url, method=method, payload=payload, timeout=timeout)
    try:
        parsed = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SmokeTestError(f"{method} {url} returned invalid JSON") from error
    if not isinstance(parsed, dict):
        raise SmokeTestError(f"{method} {url} returned an unexpected JSON response")
    return parsed


def check_frontend():
    print(f"[frontend] Checking {FRONTEND_URL}")
    status, body, content_type = request(FRONTEND_URL + "/")
    page = body.decode("utf-8", errors="replace")
    if status != 200 or "text/html" not in content_type or "<title>AIrys" not in page:
        raise SmokeTestError("Frontend did not serve the expected AIrys page")

    parser = AssetParser()
    parser.feed(page)
    if not parser.assets:
        raise SmokeTestError("Frontend page did not reference any local JS or CSS assets")
    for asset in dict.fromkeys(parser.assets):
        asset_status, _, _ = request(urljoin(FRONTEND_URL + "/", asset.lstrip("/")))
        if asset_status != 200:
            raise SmokeTestError(f"Frontend asset failed to load: {asset}")
    print(f"[frontend] PASS: page and {len(set(parser.assets))} local assets loaded")


def check_backend():
    print(f"[backend] Checking {BACKEND_URL}")
    health = request_json(BACKEND_URL + "/api/v1/chat/health")
    if health.get("status") != "healthy" or health.get("service") != "AIrys":
        raise SmokeTestError(f"Unexpected backend health response: {health}")

    settings = request_json(BACKEND_URL + "/api/v1/settings")
    if not settings.get("ollama_host") or not settings.get("ollama_model"):
        raise SmokeTestError("Backend settings do not include an Ollama host and model")
    history = request_json(BACKEND_URL + "/api/v1/chat/history")
    if not isinstance(history.get("sessions"), list):
        raise SmokeTestError("Backend chat history endpoint returned an invalid response")
    categories = request_json(BACKEND_URL + "/api/v1/memory/categories")
    if not categories.get("success"):
        raise SmokeTestError("Backend memory categories endpoint failed")
    print("[backend] PASS: health, runtime settings, history, and memory endpoints responded")
    return settings


def model_names(model):
    names = {model.get("name", ""), model.get("model", "")}
    return {name for name in names if name}


def is_chat_model(model):
    capabilities = model.get("capabilities")
    return not capabilities or any(capability in {"completion", "tools"} for capability in capabilities)


def find_model(models, requested):
    chat_models = [model for model in models if is_chat_model(model)]
    for model in chat_models:
        if requested in model_names(model):
            return model
    if ":" not in requested:
        for model in chat_models:
            if any(name.split(":", 1)[0] == requested for name in model_names(model)):
                return model
    if chat_models:
        return min(
            chat_models,
            key=lambda model: model.get("size") if isinstance(model.get("size"), int) else sys.maxsize,
        )
    return None


def ollama_tags():
    response = request_json(OLLAMA_URL + "/api/tags")
    models = response.get("models")
    if not isinstance(models, list):
        raise SmokeTestError("Ollama /api/tags returned no model list")
    return models


def pull_model(model_name):
    print(f"[ollama] No installed chat model found; downloading {model_name}")
    payload = json.dumps({"model": model_name, "stream": True}).encode("utf-8")
    req = Request(
        OLLAMA_URL + "/api/pull",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    last_status = None
    last_progress = -10
    try:
        with urlopen(req, timeout=OLLAMA_TIMEOUT) as response:
            for line in response:
                if not line.strip():
                    continue
                result = json.loads(line)
                if result.get("error"):
                    raise SmokeTestError(f"Ollama could not pull {model_name}: {result['error']}")
                status = result.get("status", "downloading")
                total = result.get("total")
                completed = result.get("completed")
                progress = int(completed * 100 / total) if total and completed is not None else None
                if status != last_status or (progress is not None and progress >= last_progress + 10):
                    suffix = f" {progress}%" if progress is not None else ""
                    print(f"[ollama] {status}{suffix}")
                    last_status = status
                    if progress is not None:
                        last_progress = progress
    except SmokeTestError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise SmokeTestError(f"Failed to download Ollama model {model_name}: {error}") from error


def ensure_local_model(requested):
    try:
        models = ollama_tags()
    except SmokeTestError as error:
        raise SmokeTestError(
            f"Cannot reach local Ollama at {OLLAMA_URL}. Start Ollama or set OLLAMA_TEST_HOST. "
            f"Original error: {error}"
        ) from error

    selected = find_model(models, requested)
    if selected is None:
        pull_model(FALLBACK_MODEL)
        models = ollama_tags()
        selected = find_model(models, FALLBACK_MODEL)
        if selected is None:
            raise SmokeTestError(f"Ollama finished pulling {FALLBACK_MODEL}, but it is not available for chat")
    selected_name = selected.get("name") or selected.get("model")
    print(f"[ollama] Using installed chat model: {selected_name}")
    return selected_name


def check_integration(backend_settings):
    print("[integration] Checking frontend proxy and live Ollama chat")
    proxy_health = request_json(FRONTEND_URL + "/api/v1/chat/health")
    if proxy_health.get("status") != "healthy":
        raise SmokeTestError("Frontend API proxy did not reach the backend")

    selected_model = ensure_local_model(backend_settings["ollama_model"])
    test_settings = dict(backend_settings)
    test_settings["ollama_model"] = selected_model
    settings_changed = selected_model != backend_settings["ollama_model"]
    settings_applied = False
    try:
        if settings_changed:
            updated = request_json(BACKEND_URL + "/api/v1/settings", method="PUT", payload=test_settings)
            settings_applied = True
            if updated.get("ollama_model") != selected_model:
                raise SmokeTestError("Could not temporarily select the installed Ollama model")

        _, body, _ = request(
            FRONTEND_URL + "/api/v1/chat/complete",
            method="POST",
            payload={
                "message": "Reply with a short greeting to confirm the assistant is working.",
                "persist_history": False,
            },
            timeout=REQUEST_TIMEOUT,
        )
        try:
            result = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SmokeTestError("Backend chat returned invalid JSON") from error
        if not isinstance(result, dict) or not result.get("response", "").strip():
            raise SmokeTestError(f"Backend chat returned no assistant response: {result}")
        print(f"[integration] PASS: Ollama chat generated a response ({selected_model})")
    finally:
        if settings_applied:
            restored = request_json(
                BACKEND_URL + "/api/v1/settings",
                method="PUT",
                payload=backend_settings,
            )
            if restored.get("ollama_model") != backend_settings["ollama_model"]:
                raise SmokeTestError("Failed to restore the backend's original model setting")
            print("[integration] Restored the backend's original model setting")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=("frontend", "backend", "integration", "all"),
        default="all",
        help="Service check to run (default: all)",
    )
    target = parser.parse_args().target
    try:
        if target in {"frontend", "all"}:
            check_frontend()
        backend_settings = None
        if target in {"backend", "integration", "all"}:
            backend_settings = check_backend()
        if target in {"integration", "all"}:
            check_integration(backend_settings)
    except SmokeTestError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {target} smoke test(s) completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
