import sys
import os
import sqlite3  # 新增：用于操作数据库
import pandas as pd # 新增：用于处理数据库查询结果

# 将当前脚本所在的目录添加到系统路径中，确保能正确导入 app 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.reporter import ExcelReporter
except ImportError:
    # 如果直接导入失败，尝试添加父目录（针对某些 IDE 或运行环境）
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    try:
        from app.core.reporter import ExcelReporter
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保 'app/core/reporter.py' 文件存在且类名正确。")
        sys.exit(1)

def create_and_populate_db(db_name="demo_data.db"):
    """
    创建一个演示用的 SQLite 数据库，如果表不存在则创建，并插入模拟数据。
    这解决了'数据库里没有表和数据'的问题。
    """
    print(f"🔄 正在初始化演示数据库: {db_name}...")
    
    # 连接到 SQLite 数据库 (如果文件不存在会自动创建)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # 1. 为了演示方便，每次运行先删除旧表（生产环境请勿这样做）
    cursor.execute("DROP TABLE IF EXISTS employees")
    
    # 2. 创建员工表
    cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            department TEXT,
            status TEXT,
            salary REAL,
            hire_date TEXT
        )
    """)
    
    # 3. 准备并插入模拟数据
    mock_data = [
        (101, "张三", "研发部", "在职", 15000.0, "2020-01-15"),
        (102, "李四", "市场部", "出差", 12000.0, "2021-03-22"),
        (103, "王五", "人事部", "休假", 9000.5, "2019-07-01"),
        (104, "赵六", "财务部", "在职", 18000.0, "2018-11-11"),
        (105, "孙七", "运维部", "离职", 11000.0, "2022-05-30")
    ]
    
    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?)", mock_data)
    conn.commit()
    print(f"✅ 数据库表 'employees' 已创建，并成功插入 {len(mock_data)} 条测试数据。")
    
    # 返回连接对象以便后续查询
    return conn

def main():
    print("🚀 正在启动控制台运行程序...")

    conn = None
    try:
        # 1. 初始化数据库并填入数据
        # (这步模拟了真实环境中数据库已经就绪的状态)
        conn = create_and_populate_db()
        
        # 2. 从数据库查询数据
        print("🔍 正在执行 SQL 查询: SELECT * FROM employees...")
        query = "SELECT * FROM employees"
        
        # 使用 pandas 直接将 SQL 查询结果读取为 DataFrame
        # 这比手动处理 cursor 更加方便，且直接兼容 ExcelReporter
        df_result = pd.read_sql_query(query, conn)
        
        print(f"📄 查询结果预览:\n{df_result}")

        # 3. 初始化报告生成器
        reporter = ExcelReporter(output_dir="outputs")
        
        # 4. 生成报告 (将从数据库查出来的 DataFrame 传进去)
        filename = "数据库导出报表.xlsx"
        report_path = reporter.generate_report(df_result, filename)
        
        # 5. 输出结果
        if report_path:
            print(f"✨ 任务成功！Excel 文件已保存至: {report_path}")
        else:
            print("⚠️ 任务结束，但未能生成文件。")

    except Exception as e:
        print(f"❌ 运行时发生错误: {e}")
        # 提示用户安装依赖
        if "No module named 'openpyxl'" in str(e) or "No module named 'pandas'" in str(e):
            print("💡 提示: 请确保已安装依赖库 -> pip install pandas openpyxl")
    finally:
        # 即使出错也要关闭数据库连接
        if conn:
            conn.close()
            print("🔒 数据库连接已关闭。")

if __name__ == "__main__":
    main()