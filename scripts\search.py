#!/usr/bin/env python3
"""88查企业查询脚本

阿里巴巴88查企业信息查询服务

用法:
    python search.py 江淮              # 查询"江淮"相关公司
    python search.py 阿里巴巴          # 查询"阿里巴巴"相关公司
    python search.py --json 江淮       # 输出完整JSON格式
"""

import sys
import json
import argparse
import requests
import socket

# API 配置
SEARCH_API_URL = "https://ainext.1688.com/1688claw/extra/enterprise/search"
DETAIL_API_URL = "https://ainext.1688.com/1688claw/extra/enterprise/companyAllData"

# 默认查询字段
DEFAULT_FETCH_FIELDS = [
    "ent_name",
    "social_credit_code",
    "license_number",
    "es_date",
    "reg_cap",
    "reg_cap_num",
    "ent_type",
    "legal_name",
    "ent_status",
    "category",
    "ability_label_outside"
]


def get_local_ip() -> str:
    """获取本机IP地址

    Returns:
        本机IP地址字符串
    """
    try:
        # 创建一个UDP socket，不实际发送数据
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def search_company(company_name: str, page_no: int = 1, page_size: int = 10) -> dict:
    """查询企业信息

    Args:
        company_name: 公司名称
        page_no: 页码，默认1
        page_size: 每页数量，默认10

    Returns:
        API 响应的字典数据
    """
    # 获取本机IP
    local_ip = get_local_ip()

    payload = {
        "companyName": company_name,
        "fetchFields": DEFAULT_FETCH_FIELDS,
        "fineRanking": True,
        "pageNo": page_no,
        "pageSize": page_size
    }

    headers = {
        "Content-Type": "application/json",
        "X-Forwarded-For": local_ip
    }

    try:
        response = requests.post(SEARCH_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)


def format_company(company: dict) -> str:
    """格式化单个公司信息为易读文本

    Args:
        company: 公司数据字典

    Returns:
        格式化的文本
    """
    ent_name = company.get("ent_name", "").replace("<em>", "**").replace("</em>", "**")
    legal_name = company.get("legal_name", "-")
    ent_status = company.get("ent_status", "-")
    reg_cap = company.get("reg_cap", "-")
    social_credit_code = company.get("social_credit_code", "-")
    es_date = company.get("es_date", "-")
    ent_type = company.get("ent_type", "-")
    address = company.get("address", "-")
    license_number = company.get("license_number", "-")
    ability_label = company.get("ability_label_outside", "-")

    lines = [
        f"## {ent_name}",
        f"**法人：** {legal_name}",
        f"**状态：** {ent_status}",
        f"**注册资本：** {reg_cap}",
        f"**统一社会信用代码：** {social_credit_code}",
        f"**成立日期：** {es_date}",
        f"**企业类型：** {ent_type}",
        f"**地址：** {address}",
        f"**许可证号：** {license_number}",
        f"**能力标签：** {ability_label}",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="88查企业信息查询")
    parser.add_argument("company_name", help="公司名称")
    parser.add_argument("--json", action="store_true", help="输出完整 JSON 格式")
    parser.add_argument("--page", type=int, default=1, help="页码（默认1）")
    parser.add_argument("--size", type=int, default=10, help="每页数量（默认10）")

    args = parser.parse_args()

    # 执行查询
    result = search_company(args.company_name, args.page, args.size)

    # 判断是否成功
    if not result.get("success"):
        print(f"查询失败: {result.get('errMsg', '未知错误')}", file=sys.stderr)
        sys.exit(1)

    # JSON 格式输出
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 文本格式输出
    total = result.get("total", 0)
    page_no = result.get("pageNo", 1)
    page_size = result.get("pageSize", 10)
    total_page = result.get("totalPage", 1)

    print(f"# 88查企业查询结果：{args.company_name}")
    print(f"总共 **{total}** 条结果，第 **{page_no}/{total_page}** 页（每页 {page_size} 条）\n")

    companies = result.get("data", [])
    for idx, company in enumerate(companies, 1):
        print(f"--- 第 {idx} 条 ---")
        print(format_company(company))
        print()


if __name__ == "__main__":
    main()
