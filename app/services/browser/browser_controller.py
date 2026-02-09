# app/services/browser/browser_controller.py
import requests
from playwright.sync_api import sync_playwright

# 比特浏览器本地 API 地址
BIT_API_BASE = "http://127.0.0.1:54345"

# ======================
# 1. 内部工具：获取动态代理
# ======================
def _get_dynamic_proxy() -> dict | None:
    """
    获取 socks5 动态代理
    假设接口返回格式为纯文本: IP:PORT:USER:PASS
    """
    try:
        # 你的代理接口
        url = "http://47.120.56.17:3000/get_ip"
        r = requests.get(url, timeout=10)
        text = r.text.strip()
        
        # 打印原始返回，方便调试
        print(f"[Debug] 代理接口返回原始数据: {text}")

        # 解析 IP:PORT:USER:PASS
        parts = text.split(":")
        if len(parts) == 4:
            return {
                "ip": parts[0],
                "port": parts[1],
                "user": parts[2],
                "pass": parts[3]
            }
        else:
            print(f"[Error] 代理格式解析失败，切分后长度为: {len(parts)}")
            return None
            
    except Exception as e:
        print(f"[Error] 获取代理网络异常: {e}")
        return None

# ======================
# 2. 核心功能：创建并连接
# ======================
def create_browser_driver(use_proxy: bool = True):
    """
    创建比特浏览器实例并返回 Playwright page
    :return: (page, bid)
    """

    # --- Step 1: 准备配置 (代理 + 指纹) ---
    proxy_cfg = {}
    
    if use_proxy:
        print("[Info] 正在获取动态代理...")
        proxy_info = _get_dynamic_proxy()
        
        if not proxy_info:
            # 如果代理获取失败，直接报错停止，不再尝试重试或报警
            raise RuntimeError("❌ 无法获取动态代理，已终止任务。")
            
        # 构造代理配置
        proxy_cfg = {
            "proxyMethod": 2,          # 自定义代理
            "proxyType": "socks5",     # 类型
            "host": proxy_info["ip"],
            "port": int(proxy_info["port"]), # 确保是整数
            "proxyUserName": proxy_info["user"],
            "proxyPassword": proxy_info["pass"]
        }
        print(f"[Debug] 即将设置代理: {proxy_info['ip']}:{proxy_info['port']}")
    
    # 构造 payload
    payload = {
        "name": "android_worker", 
        "browserFingerPrint": {
            "coreVersion": "134",     
            "ostype": "Android",      
            "os": "Linux armv81",     
            "openWidth": 450,         
            "openHeight": 800,        
            "resolutionType": "1",
            "resolution": "360x780",
            "devicePixelRatio": 2
        },
        **proxy_cfg
    }

    # --- Step 2: 调用 /browser/update 创建/更新窗口 ---
    try:
        resp = requests.post(
            f"{BIT_API_BASE}/browser/update",
            json=payload,
            timeout=30
        ).json()
    except Exception as e:
        raise RuntimeError(f"连接比特浏览器失败: {e}")

    if not resp.get("success"):
        raise RuntimeError(f"浏览器创建失败(Update): {resp}")

    bid = resp["data"]["id"]

    # --- Step 3: 调用 /browser/open 打开窗口 ---
    try:
        open_resp = requests.post(
            f"{BIT_API_BASE}/browser/open",
            json={"id": bid},
            timeout=60
        ).json()
    except Exception as e:
        raise RuntimeError(f"请求打开浏览器超时或失败: {e}")

    if not open_resp.get("success"):
        raise RuntimeError(f"浏览器启动失败(Open): {open_resp}")

    ws = open_resp["data"]["ws"]

    # --- Step 4: Playwright 连接 ---
    playwright = sync_playwright().start()
    browser = playwright.chromium.connect_over_cdp(ws)

    context = browser.contexts[0]
    if context.pages:
        page = context.pages[0]
    else:
        page = context.new_page()

    return page, bid

# ======================
# 3. 关闭浏览器
# ======================
def close_browser(bid: str):
    try:
        requests.post(
            f"{BIT_API_BASE}/browser/close",
            json={"id": bid},
            timeout=10
        )
    except Exception as e:
        pass