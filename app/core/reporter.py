# 文件路径: app/core/reporter.py
# 文件名: reporter.py
# 作用: 定义 ExcelReporter 类，用于生成 Excel 报表

import pandas as pd
import os
from datetime import datetime

class ExcelReporter:
    def __init__(self, output_dir="reports"):
        """
        初始化报告生成器，设置默认输出目录。
        """
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_report(self, data, filename=None):
        """
        根据字典列表或 DataFrame 生成 Excel 报告。
        """
        # 检查数据是否为空
        if not data:
            print("⚠️ 警告: 没有提供数据，跳过报告生成。")
            return None

        # 如果未提供文件名，则生成带时间戳的默认文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.xlsx"

        # 确保文件名以 .xlsx 结尾
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'

        filepath = os.path.join(self.output_dir, filename)

        # 如果需要，将字典列表转换为 DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("数据必须是字典列表或 pandas DataFrame")

        try:
            # 保存为 Excel (需要安装 openpyxl)
            df.to_excel(filepath, index=False)
            print(f"✅ 报告生成成功: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ 生成报告时出错: {e}")
            return None