import argparse
import getpass
import json
import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cur_dir)

from client import ShanDongClient


def main():
    print("闪动校园 / 登录")
    print()

    parser = argparse.ArgumentParser(description="登录闪动校园账号")
    parser.add_argument("-u", "--username", "--phone", dest="phone", help="登录手机号")
    parser.add_argument("-p", "--password", help="登录密码 (建议直接回车使用隐式输入)")
    parser.add_argument("--transport", default="direct", choices=["direct", "adb", "proxy"], help="传输模式 (默认 direct)")
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--adb-path", help="自定义 adb 可执行文件路径")
    args = parser.parse_args()

    phone = args.phone
    if not phone:
        try:
            phone = input("登录手机号: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            print("操作已取消")
            return

    if not phone:
        print("错误: 手机号不能为空")
        return

    password = args.password
    if not password:
        try:
            password = getpass.getpass("登录密码: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            print("操作已取消")
            return

    if not password:
        print("错误: 密码不能为空")
        return

    client = ShanDongClient(
        transport_mode=args.transport,
        proxy=args.proxy,
        adb_path=args.adb_path
    )

    print("正在完成安全人机验证...")
    print("正在提交登录认证...")
    res = client.login(phone, password)

    if res.get("code") == 0:
        d = res.get("data", {})
        print()
        print("登录成功")
        print(f"用户 UID: {d.get('userId', '-')}")
        print(f"学校编号: {d.get('schoolCode', '-')}")
        token_str = str(d.get("token", "-"))
        masked_token = f"{token_str[:16]}..." if len(token_str) > 20 else token_str
        print(f"Token: {masked_token}")
        print(f"SaToken: {d.get('satoken', '-')}")
        print()
    else:
        print()
        print("登录失败")
        print(f"错误码: {res.get('code')}")
        print(f"原因: {res.get('message')}")
        if "raw" in res:
            print(f"响应: {json.dumps(res['raw'], ensure_ascii=False)}")
        print()


if __name__ == "__main__":
    main()
