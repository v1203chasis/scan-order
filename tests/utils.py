"""测试工具函数"""
import os
import yaml


def load_yaml(file_path):
    """加载 YAML 文件"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, file_path)
    with open(full_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)