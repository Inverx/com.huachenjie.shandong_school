import argparse
import json
import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cur_dir)

import crypto
from client import ShanDongClient


def main():
    print("闪动校园 / 用户信息")
    print()

    parser = argparse.ArgumentParser(description="查询用户信息与学校资料")
    parser.add_argument("-t", "--token", help="登录 Token")
    parser.add_argument("--satoken", help="SaToken")
    parser.add_argument("-u", "--uid", help="用户 UID")
    parser.add_argument("--transport", default="direct", choices=["direct", "adb", "proxy"], help="传输模式")
    parser.add_argument("--proxy", help="代理地址")
    args = parser.parse_args()

    client = ShanDongClient(
        token=args.token,
        satoken=args.satoken,
        user_id=args.uid,
        transport_mode=args.transport,
        proxy=args.proxy
    )

    if not client.transport.token:
        try:
            tok = input("登录 Token: ").strip()
            if tok:
                client.transport.token = tok
        except (KeyboardInterrupt, EOFError):
            print()
            print("操作已取消")
            return

    if not client.transport.token:
        print("错误: 未检测到有效登录状态，请先执行 python login_cli.py 登录")
        return

    print("正在查询用户信息...")
    u_info = client.get_user_info()
    s_info = client.get_school_details()
    c_info = client.get_credit_notes()

    if u_info.get("code") == 0:
        ud = u_info.get("data", {})
        sd = s_info.get("data", {})
        cd = c_info.get("data", {})

        raw_name = ud.get("userName", "")
        dec_name = crypto.decrypt_field(raw_name) if raw_name else "-"

        raw_phone = ud.get("phone", "")
        dec_phone = crypto.decrypt_field(raw_phone) if raw_phone else "-"

        raw_sno = ud.get("studentNumber", "")
        dec_sno = crypto.decrypt_field(raw_sno) if raw_sno else "-"

        print()
        print("查询结果")
        print(f"姓名: {dec_name}")
        print(f"手机号: {dec_phone}")
        print(f"学号: {dec_sno}")
        print(f"学校: {sd.get('name', '-')}")
        print(f"学院: {ud.get('departmentName', '-')}")
        print(f"班级: {ud.get('className', '-')}")
        print(f"UID: {ud.get('userId', client.user_id or '-')}")
        print(f"诚信学分: {cd.get('amount', 0)} 分")
        print()
    else:
        print()
        print("查询失败")
        print(json.dumps(u_info, ensure_ascii=False, indent=2))
        print()


if __name__ == "__main__":
    main()
