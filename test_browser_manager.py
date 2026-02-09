from app.core.browser_manager import BrowserManager

bm = BrowserManager()

payload = {
    "name": "test_browser",
    "proxy": {},
    "fingerprint": {}
}

b = bm.create_browser(account_id="acc01", payload=payload)

assert bm.acquire("acc01") is not None

bm.mark_wait_human(b.browser_id)

assert bm.acquire("acc01") is None  # 必须成立

print("BrowserManager OK")
