"""初始 admin 用户种子脚本"""

import sys
from pathlib import Path

# 注入路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from console.server.db import SessionLocal, init_db
from console.server.models.user import User, RoleBinding
from console.server.services.auth_service import hash_password


def seed():
    init_db()
    db = SessionLocal()

    # 检查是否已有admin
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        print("admin 用户已存在，跳过")
        db.close()
        return

    admin = User(
        username="admin",
        password_hash=hash_password("admin123"),
        display_name="系统管理员",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    db.add(RoleBinding(user_id=admin.id, role="admin"))
    db.commit()

    print(f"admin 用户已创建 (密码: admin123, 角色: admin)")

    # 创建示例角色用户
    demo_users = [
        ("product_user", "产品经理", ["product"]),
        ("architect_user", "架构师", ["architect"]),
        ("design_user", "设计师", ["design"]),
        ("qa_user", "测试工程师", ["qa"]),
        ("dev_user", "全栈开发", ["frontend", "backend"]),
    ]

    for username, display_name, roles in demo_users:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            continue
        user = User(
            username=username,
            password_hash=hash_password("123456"),
            display_name=display_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        for role in roles:
            db.add(RoleBinding(user_id=user.id, role=role))
        db.commit()
        print(f"{username} 用户已创建 (密码: 123456, 角色: {roles})")

    db.close()
    print("种子数据初始化完成")


if __name__ == "__main__":
    seed()
