import argparse
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
from client import ShanDongClient

def main():
    print("闪动校园 / 校园围栏与打卡规则\n")
    
    parser = argparse.ArgumentParser(description="闪动校园围栏与打卡规则查询")
    parser.add_argument("-s", "--school-code", type=str, help="学校编号 (默认使用当前账号绑定学校)")
    args = parser.parse_args()
    
    try:
        client = ShanDongClient(use_adb=True)
        print("正在查询校园电子围栏与打卡规则...")
        res = client.get_school_fences(args.school_code)
        
        if res.get("code") == 0:
            fences = res.get("data", [])
            if not fences:
                print("\n暂无数据")
                return
                
            print(f"\n查询结果 (共 {len(fences)} 个校区打卡围栏)")
            for i, f in enumerate(fences, 1):
                poly_cnt = len(f.get("fenceList", []))
                print(f"{i}. 围栏名称: {f.get('fenceName')} | 对应校区: {f.get('subSchoolName')} | 必经打卡点数: {f.get('requiredPointCounts')} | 边界顶点数: {poly_cnt} | 开放状态: {'开放中' if f.get('openStatus') else '未开放'}")
        else:
            print("\n查询失败")
            print(f"错误码: {res.get('code')}")
            print(f"原因: {res.get('message')}")
    except (KeyboardInterrupt, EOFError):
        print("\n操作已取消")

if __name__ == "__main__":
    main()

