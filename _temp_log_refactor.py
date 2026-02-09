# 临时脚本：日志标准化重构
import re

# 读取文件
with open('app/services/tasks/task_1500.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 定义替换规则
replacements = [
    # logger.info 调用
    (r'logger\.info\(f"\[{idx}\] 🚀 线程启动"\)', 
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "start", "msg": "线程启动"})'),
    
    (r'logger\.info\(f"\[{idx}\] 📱 获取号码: {phone}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "sms_get_phone", "msg": f"获取号码: {phone}"})'),
    
    (r'logger\.info\(f"\[{idx}\] 资料: {nick} \| {dob} \| 图片类型: {img_type_log}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "prepare_data", "msg": f"资料: {nick} | {dob} | 图片类型: {img_type_log}"})'),
    
    (r'logger\.info\(f"\[{idx}\] 🌏 浏览器启动 \(ID: {bid}\)"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "browser_start", "msg": f"浏览器启动 (ID: {bid})"})'),
    
    (r'logger\.info\(f"\[{idx}\] 窗口序号: {seq}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "browser_start", "msg": f"窗口序号: {seq}"})'),
    
    (r'logger\.info\(f"\[{idx}\] 打开首页: {url_top}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "page_1", "msg": f"打开首页: {url_top}"})'),
    
    (r'logger\.info\(f"\[{idx}\] 点击"無料ではじめる""\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "page_1", "msg": "点击注册按钮"})'),
    
    (r'logger\.info\(f"\[{idx}\] 选择一级地域: {result\[\'region\'\]}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "page_2", "msg": f"选择地域: {result[\'region\']}"})'),
    
    (r'logger\.info\(f"\[{idx}\] 第三页提交完成"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "page_3", "msg": "第三页提交完成"})'),
    
    (r'logger\.info\(f"\[{idx}\] 第三页填写跳过或失败: {e}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "warning", "action": "page_3", "msg": f"第三页填写跳过或失败: {e}"})'),
    
    (r'logger\.info\(f"\[{idx}\] 上传头像: {avatar_path}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "page_4_upload", "msg": f"上传头像: {os.path.basename(avatar_path)}"})'),
    
    (r'logger\.info\(f"\[{idx}\] 头像页提交按钮未激活"\)',
     r'logger({"task": "1500", "worker": idx, "level": "warning", "action": "page_4_upload", "msg": "头像页提交按钮未激活"})'),
    
    (r'logger\.info\(f"\[{idx}\] 头像上传异常: {e}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "warning", "action": "page_4_upload", "msg": f"头像上传异常: {e}"})'),
    
    (r'logger\.info\(f"\[{idx}\] 按钮仍禁用，尝试点击 Body 触发校验"\)',
     r'logger({"task": "1500", "worker": idx, "level": "warning", "action": "page_6", "msg": "按钮仍禁用，尝试点击 Body 触发校验"})'),
    
    (r'logger\.info\(f"\[{idx}\] 提交手机号密码"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "page_6", "msg": "提交手机号密码"})'),
    
    (r'logger\.info\(f"\[{idx}\] ⏳ 等待验证码\.\.\."\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "page_7_sms", "msg": "等待验证码..."})'),
    
    (r'logger\.info\(f"\[{idx}\] 提交验证码"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "page_7_sms", "msg": "提交验证码"})'),
    
    (r'logger\.info\(f"\[{idx}\] 注册流程走完，准备认证上传\.\.\."\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "page_8", "msg": "注册流程走完，准备认证上传..."})'),
    
    (r'logger\.info\(f"\[{idx}\] 上传认证图: {temp_path}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "page_11_verify", "msg": f"上传认证图: {os.path.basename(verify_img_path)}"})'),
    
    (r'logger\.info\(f"\[{idx}\] 任务结束，自动关闭窗口\.\.\."\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "cleanup", "msg": "任务结束，自动关闭窗口..."})'),
    
    (r'logger\.info\(f"\[{idx}\] 任务结束，保留窗口 \(auto_close=False\)"\)',
     r'logger({"task": "1500", "worker": idx, "level": "info", "action": "cleanup", "msg": "任务结束，保留窗口 (auto_close=False)"})'),
    
    # logger.error 调用
    (r'logger\.error\(f"\[{idx}\] ❌ 取号失败"\)',
     r'logger({"task": "1500", "worker": idx, "level": "error", "action": "sms_get_phone", "msg": "取号失败"})'),
    
    (r'logger\.error\(f"\[{idx}\] 填验证码步骤异常: {e}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "error", "action": "page_7_sms", "msg": f"填验证码步骤异常: {e}"})'),
    
    (r'logger\.error\(f"\[{idx}\] 认证图上传失败: {e}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "error", "action": "page_11_verify", "msg": f"认证图上传失败: {e}"})'),
    
    (r'logger\.error\(f"\[{idx}\] ❌ 异常: {error_msg}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "error", "action": "exception", "msg": error_msg})'),
    
    # logger.success 调用
    (r'logger\.success\(f"\[{idx}\] 获取到验证码: {code}"\)',
     r'logger({"task": "1500", "worker": idx, "level": "success", "action": "page_7_sms", "msg": f"获取到验证码: {code}"})'),
    
    (r'logger\.success\(f"\[{idx}\] 认证上传完成"\)',
     r'logger({"task": "1500", "worker": idx, "level": "success", "action": "page_11_verify", "msg": "认证上传完成"})'),
    
    (r'logger\.success\(f"\[{idx}\] 🎉 全部流程结束!"\)',
     r'logger({"task": "1500", "worker": idx, "level": "success", "action": "complete", "msg": "全部流程结束"})'),
]

# 执行替换
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# 写回文件
with open('app/services/tasks/task_1500.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ 日志标准化完成')
