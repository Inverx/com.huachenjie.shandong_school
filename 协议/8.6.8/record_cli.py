import argparse
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
from client import ShanDongClient

def main():
    print("闪动校园 / 跑步记录与统计\n")
    
    parser = argparse.ArgumentParser(description="闪动校园跑步记录与统计查询")
    parser.add_argument("-p", "--page", type=int, default=1, help="分页页码 (默认 1)")
    parser.add_argument("-s", "--page-size", type=int, default=10, help="每页条数 (默认 10)")
    parser.add_argument("-t", "--type", choices=["sun", "free", "summary"], default="summary", help="查询类型 (summary: 累计统计, sun: 阳光跑记录, free: 自由跑记录)")
    args = parser.parse_args()
    
    try:
        client = ShanDongClient(use_adb=True)
        if not client.transport.token:
            print("错误: 未检测到有效登录状态，请先执行 python login_cli.py 登录")
            return
            
        if args.type == "summary":
            print("正在查询累计跑步数据统计...")
            res = client.get_run_summary(sport_type=2, time_type=3)
            if res.get("code") == 0:
                d = res.get("data", {})
                print("\n查询结果")
                print(f"累计总里程: {float(d.get('totalDistance', 0))/1000:.2f} 公里 ({d.get('totalDistance')} 米)")
                print(f"累计运动耗时: {int(d.get('totalDuration', 0))//60} 分钟 ({d.get('totalDuration')} 秒)")
                print(f"累计消耗热量: {d.get('totalCalorie', 0)} 卡路里")
                print(f"打卡达标天数: {d.get('checkDays', 0)} 天")
                print(f"个人最佳配速: {d.get('bestPace', 0)} 秒/公里")
            else:
                print("\n查询失败")
                print(f"错误码: {res.get('code')}")
                print(f"原因: {res.get('message')}")
                
        elif args.type == "sun":
            print(f"正在查询阳光跑历史记录 (第 {args.page} 页)...")
            res = client.get_sun_run_records(page_num=args.page, page_size=args.page_size)
            if res.get("code") == 0:
                records = res.get("data", {}).get("list", [])
                total = res.get("data", {}).get("total", 0)
                if not records:
                    print(f"\n暂无数据 (总记录数: {total})")
                    return
                print(f"\n查询结果 (共 {total} 条记录)")
                for i, r in enumerate(records, 1):
                    print(f"{i}. {r.get('createTime', '未知时间')} | 里程: {float(r.get('distance', 0))/1000:.2f} km | 耗时: {int(r.get('duration', 0))//60}分{int(r.get('duration', 0))%60}秒 | 配速: {r.get('pace', '0')}/km | 状态: {'达标' if r.get('qualifiedFlag') else '未达标'}")
            else:
                print("\n查询失败")
                print(f"错误码: {res.get('code')}")
                print(f"原因: {res.get('message')}")
        elif args.type == "free":
            print(f"正在查询自由跑历史记录 (第 {args.page} 页)...")
            res = client.get_free_run_records(page_num=args.page, page_size=args.page_size)
            if res.get("code") == 0:
                records = res.get("data", {}).get("list", [])
                total = res.get("data", {}).get("total", 0)
                if not records:
                    print(f"\n暂无数据 (总记录数: {total})")
                    return
                print(f"\n查询结果 (共 {total} 条记录)")
                for i, r in enumerate(records, 1):
                    print(f"{i}. {r.get('createTime', '未知时间')} | 里程: {float(r.get('distance', 0))/1000:.2f} km | 耗时: {int(r.get('duration', 0))//60}分{int(r.get('duration', 0))%60}秒 | 步数: {r.get('totalStep', 0)}")
            else:
                print("\n查询失败")
                print(f"错误码: {res.get('code')}")
                print(f"原因: {res.get('message')}")
    except (KeyboardInterrupt, EOFError):
        print("\n操作已取消")

if __name__ == "__main__":
    main()

