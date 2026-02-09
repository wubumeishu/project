# -*- coding: utf-8 -*-
"""
Task1500 - 1500项目注册任务 (语法与逻辑修正版)
修复：
1. 修复 f-string 内部反斜杠导致的 SyntaxError
2. 确保 logger 调用正确 (logger.info 而不是 logger())
3. 确保地区选择逻辑符合“预先随机选择”的要求
"""

import time
import random
import string
import shutil
import os
import re
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 引入核心组件
import requests
from app.services.sms.sms_client import SmsClient
from app.services.browser.browser_controller import (
    create_browser_driver,
    close_browser,
    BIT_API_BASE,
)
from app.core.settings import Settings
from app.core.logger import TaskLogger

# ==========================================
# 1. 业务常量与辅助函数
# ==========================================

# 地址映射表
AREA_MAP = {
    "53": "北海道(道央)", "54": "北海道(道北)", "55": "北海道(道東)", "56": "北海道(道南)",
    "2": "青森", "3": "岩手", "4": "福島", "5": "秋田", "6": "宮城", "7": "山形", "8": "福井",
    "9": "新潟", "10": "石川", "11": "富山", "21": "東京", "15": "神奈川", "16": "埼玉",
    "17": "茨城", "18": "栃木", "19": "群馬", "20": "千葉", "12": "岐阜", "13": "長野",
    "14": "山梨", "22": "愛知", "23": "静岡", "24": "三重", "25": "大阪", "26": "兵庫",
    "27": "奈良", "28": "滋賀", "29": "和歌山", "30": "京都", "31": "岡山", "32": "広島",
    "33": "島根", "34": "鳥取", "35": "山口", "36": "愛媛", "37": "香川", "38": "高知",
    "39": "徳島", "40": "福岡", "41": "熊本", "42": "宮崎", "43": "長崎", "45": "鹿児島",
    "46": "大分", "47": "佐賀", "44": "沖縄"
}

def random_email():
    """生成随机 Gmail 邮箱"""
    prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return f"{prefix}@gmail.com"

def load_names_from_path(abs_path: Path):
    """从绝对路径加载昵称"""
    if not abs_path.exists(): return []
    try:
        content = abs_path.read_text(encoding="utf-8")
        return [line.strip() for line in content.splitlines() if line.strip()]
    except: return []

def get_random_avatar(avatar_dir: Path):
    """从头像目录获取一张图片"""
    if not avatar_dir.exists(): return None
    files = list(avatar_dir.rglob("*.jpg")) + list(avatar_dir.rglob("*.png")) + list(avatar_dir.rglob("*.jpeg"))
    if not files: return None
    return str(random.choice(files))

def get_random_dob_image(images_dir: Path):
    """从认证图目录解析生日和图片"""
    candidates = []
    pat = re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})")
    
    for sub in ["1", "2"]:
        sub_dir = images_dir / sub
        if sub_dir.exists():
            for img_file in sub_dir.glob("*"):
                m = pat.search(img_file.name)
                if m:
                    yyyy = m.group(1)
                    mm = int(m.group(2))
                    dd = int(m.group(3))
                    candidates.append((f"{yyyy}-{mm:02d}-{dd:02d}", str(img_file)))
    
    if not candidates:
        rand_dob = f"{random.randint(1990, 2003)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        return rand_dob, None
        
    return random.choice(candidates)

# ==========================================
# 2. Worker (核心业务逻辑)
# ==========================================

def worker(idx: int, *, use_proxy: bool, auto_close: bool, 
           names: list, avatar_dir: Path, images_dir: Path, 
           logger: TaskLogger) -> dict:
    
    # 1. 独立实例化 SmsClient
    sms_client = SmsClient(item_id=2612) 
    
    driver = None 
    bid = None
    pkey = None
    
    result = {
        "idx": idx, 
        "status": "failed", 
        "phone": "", 
        "password": "", 
        "nick": "", 
        "dob": "", 
        "region": "",
        "error": ""
    }

    # 构造标准日志字典辅助函数
    def log_dict(level, action, msg):
        return {
            "task": "1500", "worker": idx, "level": level, "action": action, "msg": msg
        }

    logger.info(log_dict("info", "start", "🚀 线程启动"))

    try:
        # --- Step 1: 准备数据 ---
        
        # 1.1 取号
        pkey, phone = sms_client.get_phone()
        if not phone:
            result["error"] = "取号失败(无号码)"
            logger.error(log_dict("error", "get_phone", "❌ 取号失败"))
            return result
        
        phone = phone.zfill(11)
        result["phone"] = phone
        logger.info(log_dict("info", "get_phone", f"📱 获取号码: {phone}"))

        # 1.2 生成资料
        pwd = ''.join(random.choices(string.ascii_lowercase, k=3)) + ''.join(random.choices(string.digits, k=3))
        result["password"] = pwd
        
        nick = random.choice(names) if names else f"user_{random.randint(10000, 99999)}"
        result["nick"] = nick
        
        email = random_email()
        avatar_path = get_random_avatar(avatar_dir)
        dob, verify_img_path = get_random_dob_image(images_dir)
        
        result["dob"] = dob 
        dy, dm, dd = dob.split("-")
        
        img_type_log = "未知"
        if verify_img_path:
            norm_path = verify_img_path.replace("\\", "/")
            if "/1/" in norm_path: img_type_log = "1(健康保险证)"
            elif "/2/" in norm_path: img_type_log = "2(驾驶证)"
        
        logger.info(log_dict("info", "gen_data", f"资料: {nick} | {dob} | 图片类型: {img_type_log}"))

        # --- Step 2: 启动浏览器 ---
        
        page_obj, bid = create_browser_driver(use_proxy=use_proxy)
        if not page_obj:
            raise RuntimeError("浏览器创建失败")
            
        logger.info(log_dict("info", "browser_start", f"🌏 浏览器启动 (ID: {bid})"))

        # 2.1 获取真实窗口序号
        try:
            detail_resp = requests.post(f"{BIT_API_BASE}/browser/detail", json={"id": bid}, timeout=5)
            d_json = detail_resp.json()
            if d_json.get("success") and "data" in d_json:
                seq = d_json["data"].get("seq")
                result["idx"] = seq 
                logger.info(log_dict("info", "window_seq", f"窗口序号: {seq}"))
                
                try: requests.post(f"{BIT_API_BASE}/windowbounds/flexable", json={"seqlist": [seq]}, timeout=2)
                except: pass
        except Exception as e:
            logger.warning(log_dict("warning", "window_seq", f"获取窗口序号失败: {e}"))

        # 2.2 新建业务标签页
        context = page_obj.context
        driver = context.new_page() 
        
        # --- Step 3: 业务流程 ---
        driver.set_default_navigation_timeout(60000)
        
        # 3.1 打开首页
        url_top = "https://www.194964.com/top.php"
        logger.info(log_dict("info", "open_url", f"打开首页: {url_top}"))
        driver.goto(url_top, wait_until="domcontentloaded", timeout=60000)
        time.sleep(2)
        
        # 3.2 点击注册入口
        try:
            start_btn = driver.locator("a.btn-top.btn-regis-phone").first
            start_btn.wait_for(state="visible", timeout=10000)
            start_btn.click()
            logger.info(log_dict("info", "click_start", "点击“無料ではじめる”"))
        except Exception:
            driver.goto("https://www.194964.com/entry.php")
        time.sleep(2)
        
        # 3.3 填写基本信息
        try:
            nickname_input = driver.locator('#input_nickname').first
            nickname_input.wait_for(state="visible", timeout=10000)
            nickname_input.fill(nick)
        except Exception as e:
            raise RuntimeError(f"填写昵称失败: {e}")

        # 3.4 性别
        try:
            driver.locator('label[for="female"]').click()
        except: pass 

        # 3.5 选择地域 (预加载逻辑)
        try:
            # 随机选择一个地区代码
            area_code = random.choice(list(AREA_MAP.keys()))
            result["region"] = AREA_MAP[area_code]
            
            # 使用该代码进行选择
            area_select = driver.locator('#input_area').first
            area_select.select_option(area_code)
            
            # 记录日志 (修正语法错误的地方)
            logger.info(log_dict("info", "select_area", f"选择一级地域: {result['region']}"))
        except Exception as e:
            raise RuntimeError(f"选择地域失败: {e}")

        # 3.6 选择城市
        try:
            time.sleep(1) 
            city_select = driver.locator('#input_city').first
            city_select.wait_for(state="visible", timeout=10000)
            city_opts = city_select.locator("option")
            cnt = city_opts.count()
            if cnt > 1:
                rand_idx = random.randint(1, cnt - 1)
                val = city_opts.nth(rand_idx).get_attribute("value")
                city_select.select_option(val)
                logger.info(log_dict("info", "select_city", f"选择二级城市: {val}"))
        except: pass

        # 3.7 设置出生日期
        target_date = f"{int(dy):04d}-{int(dm):02d}" 
        driver.evaluate("""(val) => {
            let input = document.getElementById('input_date');
            let view = document.getElementById('selectdate');
            if (input) input.value = val;
            if (view) {
                view.value = val;
                view.dispatchEvent(new Event('input', { bubbles: true }));
                view.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""", target_date)
        
        next_btn = driver.locator("#submitBtn").first
        next_btn.click()
        time.sleep(2)

        # --- 第三页面会员信息 ---
        try:
            driver.locator("#dateHope").select_option(str(random.choice([1, 2, 3, 99])))
            driver.locator("#meetHope").select_option(str(random.choice([1, 2, 3])))
            
            next_btn = driver.locator("#submitBtnStep02w").first
            next_btn.click()
            logger.info(log_dict("info", "step3_submit", "第三页提交完成"))
        except Exception as e:
            logger.info(log_dict("info", "step3_skip", f"第三页填写跳过或失败: {e}"))

        # --- 第四页 上传头像 ---
        time.sleep(2)
        if avatar_path:
            try:
                driver.locator('span.popup-photo').first.click()
                driver.locator('input#imageUpload').first.set_input_files(avatar_path)
                logger.info(log_dict("info", "upload_avatar", f"上传头像: {avatar_path}"))
                time.sleep(5) 
                
                btn = driver.locator('#submitBtnStep03').first
                if btn.is_enabled():
                    btn.click()
                else:
                    logger.warning(log_dict("warning", "upload_avatar", "头像页提交按钮未激活"))
            except Exception as e:
                logger.warning(log_dict("warning", "upload_avatar", f"头像上传异常: {e}"))

        # --- 第五页 填写邮箱 ---
        time.sleep(2)
        try:
            driver.locator('input#input_email').first.fill(email)
            driver.locator('input#checkboxOptIn').first.check()
            btn = driver.locator('#submitBtnStep04').first
            if btn.is_enabled():
                btn.click()
        except: pass

        # --- 第六页 手机号密码 (加强版) ---
        time.sleep(2)
        try:
            tel_input = driver.locator('input#input_tel').first
            tel_input.wait_for(state="visible", timeout=10000)
            
            tel_input.click()
            tel_input.fill("")
            tel_input.type(phone, delay=50) 
            tel_input.press("Tab") 
            time.sleep(1)
            
            pass_input = driver.locator('input#input_password_tel').first
            pass_input.fill(pwd)
            pass_input.press("Tab") 
            time.sleep(1)
            
            btn = driver.locator('#submitBtnStep05').first
            if btn.is_disabled():
                logger.info(log_dict("info", "step6_retry", "按钮仍禁用，尝试点击 Body"))
                driver.locator("body").click()
                time.sleep(1)
            
            btn.click()
            logger.info(log_dict("info", "step6_submit", "提交手机号密码"))
            time.sleep(2)
            
        except Exception as e:
            raise RuntimeError(f"第六页(手机号)失败: {e}")

        # --- 第七页 验证码 ---
        logger.info(log_dict("info", "sms_wait", "⏳ 等待验证码..."))
        code = None
        wait_start = time.time()
        while time.time() - wait_start < 120:
            code = sms_client.get_code(pkey)
            if code: break
            time.sleep(5)
            
        if not code:
            raise RuntimeError("获取验证码超时")
            
        logger.success(log_dict("success", "sms_get", f"获取到验证码: {code}"))
        
        try:
            code_input = driver.locator('#input_code_tel').first
            code_input.fill(code)
            driver.locator("body").click()
            time.sleep(1)
            
            next_btn = driver.locator('#submitBtnStep06').first
            next_btn.click()
            logger.info(log_dict("info", "sms_submit", "提交验证码"))
            time.sleep(2)
        except Exception as e:
            logger.error(log_dict("error", "sms_submit", f"填验证码步骤异常: {e}"))
            raise e
        
        # --- 第八页 跳过点赞 ---
        try:
            close_btn = driver.locator("img.delButton").first
            if close_btn.is_visible(timeout=5000):
                close_btn.click()
        except: pass

        # --- 准备上传认证图 ---
        logger.info(log_dict("info", "cert_prepare", "注册流程走完，等待 5 秒准备认证..."))
        time.sleep(5) 

        # --- 第十一页 上传认证图 ---
        if verify_img_path:
            try:
                cert_url = "https://sp.194964.com/nochild/certificate/show_certificate_picture.html"
                driver.goto(cert_url, wait_until="commit")
                
                uploader = driver.locator("input#uploader").first
                uploader.wait_for(state="attached", timeout=10000)
                
                ext = os.path.splitext(verify_img_path)[1]
                temp_name = "".join(random.choices(string.ascii_lowercase, k=6)) + ext
                temp_dir = Path(Settings.get("paths.root_dir", ".")) / "temp_uploads"
                temp_dir.mkdir(exist_ok=True)
                temp_path = temp_dir / temp_name
                
                shutil.copy(verify_img_path, temp_path)
                
                uploader.set_input_files(str(temp_path))
                logger.info(log_dict("info", "cert_upload", f"上传认证图: {temp_path}"))
                time.sleep(2)
                
                submit_span = driver.locator("span.exec-upload.nenrei_pic2").first
                submit_span.scroll_into_view_if_needed()
                time.sleep(1)
                submit_span.click()
                time.sleep(2)
                
                try: os.remove(temp_path)
                except: pass
                
                driver.locator("div.menuLink >> a").first.click()
                logger.success(log_dict("success", "cert_finish", "认证上传完成"))
                
            except Exception as e:
                logger.error(log_dict("error", "cert_upload", f"认证图上传失败: {e}"))

        # --- 最终判定成功 ---
        result["status"] = "success"
        sms_client.api_return(pkey, 0)
        logger.success(log_dict("success", "task_finish", "🎉 全部流程结束!"))

    except Exception as e:
        error_msg = str(e)
        logger.error(log_dict("error", "task_crash", f"❌ 异常: {error_msg}"))
        result["error"] = error_msg
        if pkey:
            try:
                sms_client.release_phone(pkey)
            except: pass
    finally:
        # 关闭策略
        if bid and auto_close:
            logger.info(log_dict("info", "close", "自动关闭窗口..."))
            try:
                close_browser(bid)
            except: pass
        else:
            logger.info(log_dict("info", "close", "任务结束，保留窗口 (auto_close=False)"))

    return result

# ==========================================
# 3. 任务入口类
# ==========================================

class Task1500:
    def __init__(self, *, count: int, threads: int = 1, use_proxy: bool = False, auto_close: bool = True, 
                 result_callback=None):
        self.count = count
        self.threads = threads
        self.use_proxy = use_proxy
        self.auto_close = auto_close
        self.result_callback = result_callback
        
        self.logger = TaskLogger("task_1500")
        
        self.names_path = Path(Settings.get("paths.names"))
        self.avatar_dir = Path(Settings.get("paths.avatars"))
        self.images_dir = Path(Settings.get("paths.images"))
        
        self.names_cache = load_names_from_path(self.names_path)
        
        img_count_1 = len(list((self.images_dir / "1").glob("*"))) if (self.images_dir / "1").exists() else 0
        img_count_2 = len(list((self.images_dir / "2").glob("*"))) if (self.images_dir / "2").exists() else 0
        total_img = img_count_1 + img_count_2
        
        # 初始化日志
        self.logger.info({
            "task": "1500", "worker": 0, "level": "info", "action": "init",
            "msg": f"资源统计: 昵称({len(self.names_cache)}) 认证图({total_img})"
        })

    def run(self) -> list:
        self.logger.info({
            "task": "1500", "worker": 0, "level": "info", "action": "run",
            "msg": f"开始执行: 数量={self.count}, 线程={self.threads}"
        })
        results = []
        
        with ThreadPoolExecutor(max_workers=self.threads) as pool:
            futures = []
            for i in range(self.count):
                future = pool.submit(
                    worker, idx=i + 1, use_proxy=self.use_proxy, auto_close=self.auto_close,
                    names=self.names_cache, avatar_dir=self.avatar_dir, images_dir=self.images_dir, 
                    logger=self.logger
                )
                futures.append(future)
                if i < self.count - 1: time.sleep(3)
            
            for future in as_completed(futures):
                try:
                    res = future.result()
                    results.append(res)
                    if self.result_callback:
                        self.result_callback(res)
                except Exception as e:
                    self.logger.error({
                        "task": "1500", "worker": 0, "level": "error", "action": "crash",
                        "msg": f"线程崩溃: {e}"
                    })
                    
        return results