#!/usr/bin/env python3
"""88查企业详细信息查询脚本

基于统一社会信用代码查询企业详细数据，支持多维度查询。

用法:
    python detail.py 91340121149265963G                    # 查询所有常用维度
    python detail.py 91340121149265963G --dims gszl,gdxx  # 查询指定维度
    python detail.py 91340121149265963G --json            # JSON格式输出
"""

import sys
import json
import argparse
import requests
import socket

# API 配置
API_URL = "https://ainext.1688.com/1688claw/extra/enterprise/companyAllData"

# 常用维度（按需查询，避免数据量过大）
DEFAULT_DIMENSIONS = [
    "gszl",  # 工商资料
    "gdxx",  # 股东信息
    "qybj",  # 企业背景
    "ryzz",  # 荣誉资质
    "zlxx",  # 专利信息
    "dcdy",  # 动产抵押
    "xzcf",  # 行政处罚
    "jyyc",  # 经营异常
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


# 维度名称映射（维度代码 -> 中文名）
DIMENSION_NAMES = {
    "all": "所有维度",
    "gszl": "工商资料",
    "gdxx": "股东信息",
    "qybj": "企业背景",
    "sbif": "商标",
    "ryzz": "荣誉资质",
    "zlxx": "专利信息",
    "zzuq": "著作权",
    "nbif": "年报",
    "dcdy": "动产抵押",
    "gqcz": "股权出质",
    "xzcf": "行政处罚",
    "pjjl": "评级记录",
    "cjqs": "催缴/欠税",
    "jyyc": "经营异常",
    "zdwf": "重大税收违法",
    "zycy": "主要成员",
    "sjkzr": "企业实际控制人",
    "dwtz": "对外投资",
    "fzjg": "分支机构",
    "ktgg": "开庭公告",
    "ssgg": "涉诉公告",
    "cpws": "裁判文书",
    "bzxr": "被执行人",
    "sxzxr": "失信被执行人",
    "zbaj": "终本案件",
    "xzgxf": "限制高消费",
    "sfxz": "司法协助",
    "gsbg": "工商变更",
    "wzba": "网站备案",
    "jzfx": "竞争分析",
    "glfx": "关联风险",
    "glfrd": "关联方认定",
    "xzxk": "行政许可",
    "fxdt": "风险动态",
    "ppcp": "品牌产品",
    "fxsm": "风险扫描",
    "swfzc": "税务非正常",
    "ztbif": "招投标",
    "gqct": "股权穿透图",
    "qygx": "企业关系",
    "zmbq": "芝麻企业信用标签"
}


def get_dimension_name(dimension_code: str) -> str:
    """获取维度的中文名称

    Args:
        dimension_code: 维度代码

    Returns:
        中文名称
    """
    return DIMENSION_NAMES.get(dimension_code, dimension_code)


def query_company_detail(social_credit_code: str, fetch_list: list) -> dict:
    """查询企业详细信息

    Args:
        social_credit_code: 统一社会信用代码
        fetch_list: 要查询的维度列表

    Returns:
        API 响应的字典数据
    """
    # 获取本机IP
    local_ip = get_local_ip()

    payload = {
        "keyType": "socialCreditCode",
        "key": social_credit_code,
        "fetchList": fetch_list
    }

    headers = {
        "Content-Type": "application/json",
        "X-Forwarded-For": local_ip
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)


def format_dimension(dimension_code: str, data: any) -> str:
    """格式化单个维度的数据

    Args:
        dimension_code: 维度代码
        data: 维度数据

    Returns:
        格式化的文本
    """
    if data is None or data == []:
        return f"## {get_dimension_name(dimension_code)}\n暂无数据\n"

    if isinstance(data, (list, dict)):
        return f"## {get_dimension_name(dimension_code)}\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```\n"

    return f"## {get_dimension_name(dimension_code)}\n{data}\n"


def main():
    parser = argparse.ArgumentParser(description="88查企业详细信息查询")
    parser.add_argument("social_credit_code", help="统一社会信用代码")
    parser.add_argument("--dims", type=str,
                       help=f"查询维度，逗号分隔（如：gszl,gdxx），默认：{','.join(DEFAULT_DIMENSIONS)}")
    parser.add_argument("--json", action="store_true", help="输出完整 JSON 格式")

    args = parser.parse_args()

    # 确定查询维度
    if args.dims:
        fetch_list = [d.strip() for d in args.dims.split(",") if d.strip()]
    else:
        fetch_list = DEFAULT_DIMENSIONS

    # 验证维度代码
    invalid_dims = [d for d in fetch_list if d not in DIMENSION_NAMES]
    if invalid_dims:
        print(f"错误：无效的维度代码: {', '.join(invalid_dims)}", file=sys.stderr)
        print(f"有效的维度代码：{', '.join(DIMENSION_NAMES.keys())}", file=sys.stderr)
        sys.exit(1)

    # 执行查询
    result = query_company_detail(args.social_credit_code, fetch_list)

    # 判断是否成功
    if not result.get("success") or result.get("code") != "200":
        error_msg = result.get("errMsg", "未知错误")
        print(f"查询失败: {error_msg}", file=sys.stderr)
        sys.exit(1)

    # JSON 格式输出
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 文本格式输出
    print(f"# 88查企业详细信息")
    print(f"**统一社会信用代码：** {args.social_credit_code}")
    print(f"**查询维度：** {', '.join(get_dimension_name(d) for d in fetch_list)}\n")

    data = result.get("data", {})

    # 按请求顺序输出各个维度
    for dim in fetch_list:
        dimension_data = data.get(get_dimension_name(dim), None)
        if dimension_data is not None or dim in fetch_list:
            print(format_dimension(dim, dimension_data))

    # 查询可能返回了额外的维度
    extra_dims = []
    for key in data.keys():
        # 检查是否是请求的维度之一
        if key not in [get_dimension_name(d) for d in fetch_list]:
            extra_dims.append(key)

    if extra_dims:
        print("\n--- 其他返回维度 ---")
        for dim_name in extra_dims:
            print(f"\n## {dim_name}")
            print(f"```json\n{json.dumps(data[dim_name], ensure_ascii=False, indent=2)}\n```")


if __name__ == "__main__":
    main()
