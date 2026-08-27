import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
from client import ShanDongClient
import crypto

def main():
    print("闪动校园 / 用户信息与状态\n")
    
    try:
        client = ShanDongClient(use_adb=True)
        if not client.transport.token:
            print("错误: 未检测到有效登录状态，请先执行 python login_cli.py 登录")
            return
            
        print("正在查询用户基础信息...")
        u_info = client.get_user_info()
        print("正在查询所属学校信息...")
        s_info = client.get_school_details()
        print("正在查询诚信学分积分...")
        c_info = client.get_credit_notes()
        
        if u_info.get("code") == 0:
            ud = u_info.get("data", {})
            sd = s_info.get("data", {})
            cd = c_info.get("data", {})
            
            # Decrypt sensitive fields
            raw_name = ud.get('userName', '')
            dec_name = crypto.decrypt_field(raw_name) if raw_name else '未知'
            
            raw_phone = ud.get('phone', '')
            dec_phone = crypto.decrypt_field(raw_phone) if raw_phone else '未知'
            
            raw_sno = ud.get('studentNumber', '')
            dec_sno = crypto.decrypt_field(raw_sno) if raw_sno else '已隐藏'
            
            print("\n查询结果")
            print(f"用户姓名: {dec_name}")
            print(f"用户手机: {dec_phone}")
            print(f"所属学校: {sd.get('name', '未知')} ({sd.get('shortName', '')})")
            print(f"学生学号: {dec_sno}")
            print(f"诚信积分: {cd.get('amount', 0)} 分")
        else:
            print("\n查询失败")
            print(f"错误码: {u_info.get('code')}")
            print(f"原因: {u_info.get('message')}")
    except (KeyboardInterrupt, EOFError):
        print("\n操作已取消")

if __name__ == "__main__":
    main()

