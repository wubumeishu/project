# app/services/sms/sms_client.py
import requests
import time
from typing import Optional, Tuple
from app.core.settings import Settings

class SmsClient:
    """
    火狐狸短信接码客户端 (Firefox.fun 正式版)
    - 接口地址: http://www.firefox.fun/yhapi.ashx
    - 架构设计: Token 进配置 (Settings)，Item ID 进业务 (Task)
    """
    
    # ✅ 修正为文档中的正确地址 (HTTP)
    BASE_URL = "http://www.firefox.fun/yhapi.ashx"

    def __init__(self, item_id: int):
        self.item_id = item_id
        # Token 统一从 Settings 读取
        self.token = Settings.firefox_sms_token()

        if not self.token:
            raise ValueError("❌ 火狐狸 token 未配置，请在 settings/settings.json 中填写 firefox_sms.token")

    def _call_api(self, params: dict) -> tuple:
        """
        内部通用请求方法
        解析规则：1|成功|数据... 或 0|失败原因
        """
        # 自动注入 token
        params["token"] = self.token
        
        try:
            # ✅ 使用 params 传参，Requests 会自动拼接成 url?act=xx&token=xx
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            text = response.text.strip()
            
            # 按 | 分割
            parts = text.split("|")
            
            # 判断状态码 '1' 为成功
            if parts[0] == "1":
                # 返回 (True, 去掉状态码后的数据列表)
                return True, parts[1:]
            else:
                # 返回 (False, 数据列表)
                return False, parts[1:]
                
        except Exception as e:
            print(f"[SMS] 接口请求异常: {e}")
            return False, []

    def get_balance(self) -> float:
        """查询余额"""
        # 文档接口: act=myInfo
        ok, parts = self._call_api({"act": "myInfo"})
        
        if ok and len(parts) >= 1:
            try:
                return float(parts[0])
            except:
                pass
        return 0.0

    def get_phone(self) -> Tuple[str, str]:
        """
        获取手机号
        文档接口: act=getPhone&iid=项目ID
        返回: (pkey, phone)
        """
        ok, parts = self._call_api({
            "act": "getPhone",
            "iid": self.item_id
        })
        
        # 根据之前的经验，成功返回通常包含: pkey, ..., 手机号
        # parts[0] 是 pkey
        # parts[5] 或 parts[6] 是手机号 (取决于接口版本，这里做个兼容)
        if ok and len(parts) >= 6:
            pkey = parts[0]
            # 尝试获取手机号，通常在后面
            phone = parts[6] if len(parts) > 6 else parts[5]
            return pkey, phone
            
        return "", ""

    def get_code(self, pkey: str) -> Optional[str]:
        """
        获取验证码 (单次查询)
        文档接口: act=getPhoneCode&pkey=...
        """
        ok, parts = self._call_api({
            "act": "getPhoneCode",
            "pkey": pkey
        })
        
        # 成功返回: 1|验证码|短信内容
        # 这里 parts[0] 就是验证码
        if ok and len(parts) >= 1:
            code = parts[0]
            # 简单的校验，确保是数字
            if code.isdigit():
                return code
        return None

    def release_phone(self, pkey: str) -> bool:
        """释放手机号"""
        # 文档接口: act=setRel&pkey=...
        ok, _ = self._call_api({
            "act": "setRel",
            "pkey": pkey
        })
        return ok

    def api_return(self, pkey: str, remark: int = 0) -> bool:
        """回传结果 (加黑/释放)"""
        # 文档接口: act=apiReturn&pkey=...
        ok, _ = self._call_api({
            "act": "apiReturn",
            "pkey": pkey,
            "remark": remark
        })
        return ok

# ===================================================================
# 模块级兼容层 (保留以兼容旧代码，但建议新代码直接用类)
# ===================================================================
# 默认 2612 项目
_default_client = SmsClient(item_id=2612)

def get_balance(token: str = None) -> float:
    return _default_client.get_balance()

def get_phone(token: str = None) -> Tuple[str, str]:
    return _default_client.get_phone()

def get_code(token: str = None, pkey: str = None) -> Optional[str]:
    return _default_client.get_code(pkey)

def release_phone(token: str = None, pkey: str = None) -> bool:
    return _default_client.release_phone(pkey)