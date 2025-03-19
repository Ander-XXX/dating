import re
import json
from typing import Dict, List, Union

def parse_candidate(raw: str) -> Dict[str, Union[str, list, dict]]:
    """解析单个候选人原始数据"""
    # 字段编号到标准字段名的映射
    field_map = {
        "1": "wechat",
        "2": "gender",
        "3": "age",
        "4": "hometown",
        "5": "employment_status",
        "6": "height",
        "7": "weight",
        "8": "education",
        "9": "constellation",
        "10": "industry",
        "11": "income",
        "12": "working_hours",
        "13": "mbti",
        "14": "self_appearance",
        "15": "require_appearance",
        "16": "height_requirements",
        "17": "weight_requirements",
        "18": "age_preference",
        "19": "hometown_requirements",
        "20": "ideal_type",
        "21": "hobbies",
        "22": "self_evaluation"
    }

    candidate = {"basic": {}, "requirements": {}, "additional": {}}
    
    # 预处理特殊符号
    raw = raw.replace("：", ":").replace("〖", "[").replace("〗", "]")
    
    # 使用正则提取所有字段
    pattern = r"(\d+)、([^:]+):([^\d]+?(?=\d+、|$))"
    matches = re.findall(pattern, raw)
    
    for num, field_name, value in matches:
        field_key = field_map.get(num)
        if not field_key:
            continue
            
        value = value.strip()
        
        # 特殊字段处理
        if field_key == "height_requirements":
            if "身高需求" in field_name:
                candidate['requirements']['height_range'] = re.findall(r"\[([\d,]+)\]", value)
            else:
                candidate['requirements']['height_preference'] = value.split("┋")
        elif field_key == "age_preference":
            if "岁数需求" in field_name:
                candidate['requirements']['age_range'] = re.findall(r"\[([\d.,]+)\]", value)
            else:
                candidate['requirements']['age_preference'] = value.split("┋")
        elif field_key in ["ideal_type", "hobbies", "self_evaluation"]:
            candidate['additional'][field_key] = [v.strip() for v in re.split(r",|，", value)]
        else:
            candidate['basic'][field_key] = value
            
    return candidate

# 原始数据
raw_candidates = [...]  # 此处填入用户提供的原始数据列表

# 转换为结构化数据
structured = [parse_candidate(c) for c in raw_candidates if c.strip()]

# 保存为JSON文件
with open("candidates.json", "w", encoding="utf-8") as f:
    json.dump(structured, f, ensure_ascii=False, indent=2)

print(f"成功转换{len(structured)}位候选人数据")
