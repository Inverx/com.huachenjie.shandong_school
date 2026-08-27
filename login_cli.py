import argparse
import getpass
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
from client import ShanDongClient

def main():
    print("闪动校园 / 登录认证\n")
    
    parser = argparse.ArgumentParser(description="闪动校园登录 CLI")
    parser.add_argument("-p", "--phone", type=str, help="登录手机号")
    parser.add_argument("--password", type=str, help="登录密码 (建议直接回车使用隐式输入)")
    args = parser.parse_args()
    
    try:
        phone = args.phone
        if not phone:
            phone = input("登录手机号: ").strip()
        if not phone:
            print("错误: 手机号不能为空")
            return
            
        password = args.password
        if not password:
            password = getpass.getpass("登录密码: ").strip()
        if not password:
            print("错误: 密码不能为空")
            return
            
        print("正在完成安全人机验证...")
        client = ShanDongClient(use_adb=True)
        print("正在提交登录认证...")
        res = client.login(phone, password)
        
        if res.get("error") == 0:
            d = res.get("data", {})
            print("\n登录成功")
            print(f"用户 UID: {d.get('userId')}")
            print(f"学校编号: {d.get('schoolCode')}")
            print(f"Token: {d.get('token')[:25]}...")
            print(f"SaToken: {d.get('satoken')}")
        else:
            print("\n登录失败")
            print(f"错误码: {res.get('error')}")
            print(f"原因: {res.get('message')}")
            if "raw" in res:
                print("原始返回:", repr(res["raw"]))
    except (KeyboardInterrupt, EOFError):
        print("\n操作已取消")

if __name__ == "__main__":
    main()

