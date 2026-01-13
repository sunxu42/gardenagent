"""
Tool system for loading and managing skill files.
Provides functions to load skill headers, content, and scan skills directory.
"""
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import yaml
import re


def load_skill_header(skill_path: str) -> Dict[str, str]:
    """
    加载SKILL文件的头部信息（YAML front matter）。
    
    Args:
        skill_path: SKILL.md文件的路径
        
    Returns:
        包含头部信息的字典，如果文件不存在或没有头部信息则返回空字典
        
    Example:
        >>> header = load_skill_header("skills/grassland_manage/SKILL.md")
        >>> print(header)
        {'name': 'pdf', 'description': '...', 'license': '...'}
    """
    skill_file = Path(skill_path)
    
    if not skill_file.exists():
        return {}
    
    try:
        content = skill_file.read_text(encoding='utf-8')
        
        # 检查是否有YAML front matter（以---开头和结尾）
        if not content.startswith('---'):
            return {}
        
        # 找到第二个---的位置
        lines = content.split('\n')
        if len(lines) < 2 or lines[0].strip() != '---':
            return {}
        
        # 查找第二个---的位置
        end_index = None
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                end_index = i
                break
        
        if end_index is None:
            return {}
        
        # 提取YAML内容
        yaml_content = '\n'.join(lines[1:end_index])
        
        # 解析YAML
        header = yaml.safe_load(yaml_content)
        return header if header else {}
        
    except Exception as e:
        # 如果解析失败，返回空字典
        return {}


def load_skill_content(skill_path: str) -> str:
    """
    加载SKILL文件中除头部信息以外的其他内容。
    
    Args:
        skill_path: SKILL.md文件的路径
        
    Returns:
        去除YAML front matter后的Markdown内容字符串
        
    Example:
        >>> content = load_skill_content("skills/grassland_management/SKILL.md")
        >>> print(content[:100])
        # PDF Processing Guide
        ...
    """
    skill_file = Path(skill_path)
    
    if not skill_file.exists():
        return ""
    
    try:
        content = skill_file.read_text(encoding='utf-8')
        
        # 检查是否有YAML front matter
        if not content.startswith('---'):
            return content
        
        # 找到第二个---的位置
        lines = content.split('\n')
        if len(lines) < 2 or lines[0].strip() != '---':
            return content
        
        # 查找第二个---的位置
        end_index = None
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                end_index = i
                break
        
        if end_index is None:
            return content
        
        # 提取---之后的内容（跳过第二个---行）
        content_lines = lines[end_index + 1:]
        
        # 如果第一个非空行是空行，跳过它
        result = '\n'.join(content_lines)
        if result.startswith('\n'):
            result = result.lstrip('\n')
        
        return result
        
    except Exception as e:
        # 如果读取失败，返回空字符串
        return ""


def scan_skills_headers(skills_dir: str) -> Dict[str, Dict[str, str]]:
    """
    扫描skills文件夹下所有SKILL文件的头部信息。
    
    Args:
        skills_dir: skills文件夹的路径
        
    Returns:
        字典，键为技能名称（从header中的name字段获取，如果没有则使用文件夹名），
        值为该技能的头部信息字典
        
    Example:
        >>> headers = scan_skills_headers("garden_agent/skills")
        >>> print(headers)
        {'pdf': {'name': 'pdf', 'description': '...', 'license': '...'}}
    """
    skills_path = Path(skills_dir)
    
    if not skills_path.exists() or not skills_path.is_dir():
        return {}
    
    result = {}
    
    # 递归查找所有SKILL.md文件
    skill_files = list(skills_path.rglob('SKILL.md'))
    
    for skill_file in skill_files:
        header = load_skill_header(str(skill_file))
        
        if header:
            # 使用header中的name字段作为键，如果没有name则使用文件夹名
            skill_name = header.get('name')
            if not skill_name:
                # 使用包含SKILL.md的文件夹名作为技能名
                skill_name = skill_file.parent.name
            
            result[skill_name] = header
    
    return result


def validate_skill_header(header: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    验证SKILL文件头部信息是否符合格式要求。
    
    验证规则：
    - name: 必需，小写，允许连字符，最多64字符
    - description: 必需，最多1024字符
    
    Args:
        header: SKILL文件的头部信息字典
        
    Returns:
        元组 (is_valid, errors):
        - is_valid: 布尔值，表示是否通过验证
        - errors: 错误信息列表，如果通过验证则为空列表
        
    Example:
        >>> header = {'name': 'pdf-tool', 'description': 'PDF processing tool.'}
        >>> is_valid, errors = validate_skill_header(header)
        >>> print(is_valid, errors)
        True []
        
        >>> header = {'name': 'Invalid Name', 'description': 'Some description'}
        >>> is_valid, errors = validate_skill_header(header)
        >>> print(is_valid, errors)
        False ['name must be lowercase and can only contain lowercase letters, numbers, and hyphens']
    """
    errors = []
    
    # 验证name字段
    if 'name' not in header:
        errors.append("name field is required")
    else:
        name = header['name']
        
        # 检查是否为字符串
        if not isinstance(name, str):
            errors.append("name must be a string")
        else:
            # 检查长度
            if len(name) > 64:
                errors.append(f"name must be at most 64 characters (got {len(name)})")
            
            # 检查格式：小写，允许连字符，允许数字
            # 允许的模式：小写字母、数字、连字符
            if not re.match(r'^[a-z0-9-]+$', name):
                errors.append("name must be lowercase and can only contain lowercase letters, numbers, and hyphens")
            
            # 检查不能以连字符开头或结尾
            if name.startswith('-') or name.endswith('-'):
                errors.append("name cannot start or end with a hyphen")
    
    # 验证description字段
    if 'description' not in header:
        errors.append("description field is required")
    else:
        description = header['description']
        
        # 检查是否为字符串
        if not isinstance(description, str):
            errors.append("description must be a string")
        else:
            # 检查长度
            if len(description) > 1024:
                errors.append(f"description must be at most 1024 characters (got {len(description)})")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_skill_file(skill_path: str) -> Tuple[bool, List[str]]:
    """
    验证SKILL文件是否符合格式要求。
    
    首先加载头部信息，然后验证头部格式。
    
    Args:
        skill_path: SKILL.md文件的路径
        
    Returns:
        元组 (is_valid, errors):
        - is_valid: 布尔值，表示是否通过验证
        - errors: 错误信息列表，如果通过验证则为空列表
        
    Example:
        >>> is_valid, errors = validate_skill_file("skills/grassland_manage/SKILL.md")
        >>> if not is_valid:
        ...     print("Validation errors:", errors)
    """
    header = load_skill_header(skill_path)
    
    if not header:
        return False, ["Failed to load skill header or header is empty"]
    
    return validate_skill_header(header)


# 示例用法（用于测试）
if __name__ == "__main__":
    # 测试加载单个文件的头部
    skill_path = "skills/grassland-management/SKILL.md"
    # validate skill file
    is_valid, errors = validate_skill_file(skill_path)
    print(f"is_valid: {is_valid}, errors: {errors}")

    header = load_skill_header(skill_path)
    print("Header:", header)
    
    # 测试加载内容
    content = load_skill_content(skill_path)
    print("\nContent preview (first 200 chars):")
    print(content[:200])
    
    # 测试扫描所有技能
    skills_dir = "skills"
    all_headers = scan_skills_headers(skills_dir)
    print("\nAll skill headers:")
    for name, header in all_headers.items():
        print(f"{name}: {header}")

