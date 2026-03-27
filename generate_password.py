#!/usr/bin/env python3
"""
生成密码哈希工具
"""

import hashlib
import secrets

def generate_password_hash(password: str) -> str:
    """
    生成密码哈希（与AuthManager兼容）
    
    Args:
        password: 密码
        
    Returns:
        str: 哈希值（格式：salt:hash）
    """
    if not password:
        raise ValueError("密码不能为空")
    
    # 生成随机salt
    salt = secrets.token_hex(16)
    
    # 使用PBKDF2生成哈希
    hash_value = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # 迭代次数
    )
    
    # 存储格式：salt:hash
    return f"{salt}:{hash_value.hex()}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = "admin123"
    
    hash_value = generate_password_hash(password)
    print(f"密码: {password}")
    print(f"哈希: {hash_value}")
