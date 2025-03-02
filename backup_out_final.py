import os
import zipfile
import re
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def get_executable_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_folder_month(folder_name):
    match = re.search(r'[A-Za-z0-9]{20}_(\d{6})', folder_name)
    if match:
        date_str = match.group(1)
        return datetime.strptime(date_str, "%Y%m").strftime("%Y-%m")
    return None

def compress_folder(folder, zip_file, base_path):
    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, base_path)
            zip_file.write(file_path, arcname)


def incremental_backup(source_dir, backup_dir, start_backup_time):
    source_path = Path(source_dir)
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    start_backup_timestamp = datetime.strptime(start_backup_time, "%Y-%m-%d %H:%M:%S").timestamp()

    folders_by_month = defaultdict(list)
    skipped_items = []

    for item in source_path.iterdir():
        if item.is_dir() and item.stat().st_mtime > start_backup_timestamp:
            folder_month = get_folder_month(item.name)
            if folder_month:
                folders_by_month[folder_month].append(item)
            else:
                skipped_items.append(item.name)
        elif not item.is_dir():
            skipped_items.append(item.name)

    for month, folders in folders_by_month.items():
        zip_filename = f"backup_{month}.zip"
        zip_path = backup_path / zip_filename

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for folder in folders:
                compress_folder(folder, zip_file, source_path)

        print(f"已创建备份: {zip_filename}")

    print(f"增量备份完成。共处理 {sum(len(folders) for folders in folders_by_month.values())} 个文件夹，分为 {len(folders_by_month)} 个月份组。")
    
    skipped_file = backup_path / f"skipped_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(skipped_file, "w", encoding='utf-8') as f:
        f.write("以下项目被跳过：\n")
        for item in skipped_items:
            f.write(f"  - {item}\n")

    print(f"跳过的项目已记录到文件: {skipped_file}")

def read_config():
    executable_dir = get_executable_dir()
    config_path = os.path.join(executable_dir, "backup_config.txt")
    
    print(f"尝试读取配置文件: {config_path}")
    
    if not os.path.exists(config_path):
        print("配置文件不存在,正在创建...")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("源文件夹路径=C:\\path\\to\\source\n")
            f.write("备份文件夹路径=C:\\path\\to\\backup\n")
            f.write("备份起始时间=2000-01-01 00:00:00\n")
        print(f"配置文件已创建：{config_path}")
        print("请编辑配置文件并重新运行程序。")
        return None, None, None

    encodings = ['utf-8', 'gbk', 'latin-1']
    for encoding in encodings:
        try:
            with open(config_path, "r", encoding=encoding) as f:
                lines = f.readlines()
                print(f"成功使用 {encoding} 编码读取配置文件")
                break
        except UnicodeDecodeError:
            print(f"使用 {encoding} 编码读取失败")
            continue
    else:
        print(f"无法读取配置文件，请检查文件编码。路径：{config_path}")
        return None, None, None

    config = {}
    for line in lines:
        try:
            key, value = line.strip().split("=")
            config[key.strip()] = value.strip()
        except ValueError:
            print(f"无法解析配置行: {line.strip()}")

    source_dir = config.get("源文件夹路径")
    backup_dir = config.get("备份文件夹路径")
    start_time = config.get("备份起始时间")

    print(f"读取到的配置: 源文件夹={source_dir}, 备份文件夹={backup_dir}, 起始时间={start_time}")

    if not all([source_dir, backup_dir, start_time]):
        print("配置文件中缺少必要的信息")
        return None, None, None

    return source_dir, backup_dir, start_time

if __name__ == "__main__":
    source_dir, backup_dir, start_backup_time = read_config()
    if source_dir and backup_dir and start_backup_time:
        incremental_backup(source_dir, backup_dir, start_backup_time)
    else:
        print("配置读取失败，请检查配置文件。")
    input("按回车键退出...")
