import argparse
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
from client import ShanDongClient

def main():
    print("闪动校园 / AI 运动项目与打卡\n")
    
    parser = argparse.ArgumentParser(description="闪动校园 AI 运动项目查询")
    parser.add_argument("-t", "--type", choices=["categories", "records"], default="categories", help="查询类型 (categories: 项目分类, records: 历史打卡记录)")
    parser.add_argument("-p", "--page", type=int, default=1, help="记录页码 (默认 1)")
    args = parser.parse_args()
    
    try:
        client = ShanDongClient(use_adb=True)
        if not client.transport.token:
            print("错误: 未检测到有效登录状态，请先执行 python login_cli.py 登录")
            return
            
        if args.type == "categories":
            print("正在查询 AI 运动项目与动作分类...")
            res = client.get_ai_categories()
            if res.get("code") == 0 and "data" in res:
                print("\n查询结果")
                for cat_key, items in res["data"].items():
                    if isinstance(items, list):
                        names = [it.get("sportName") for it in items if isinstance(it, dict) and it.get("sportName")]
                        if names:
                            print(f"类别 [{cat_key}]: {', '.join(names)}")
            else:
                print("\n查询失败")
                print(f"错误码: {res.get('code')}")
                print(f"原因: {res.get('message')}")
        else:
            print(f"正在查询 AI 运动打卡历史记录 (第 {args.page} 页)...")
            res = client.get_ai_records(page_num=args.page, page_size=10)
            if res.get("code") == 0:
                recs = res.get("data", {}).get("list", [])
                total = res.get("data", {}).get("total", 0)
                if not recs:
                    print(f"\n暂无数据 (总记录数: {total})")
                    return
                print(f"\n查询结果 (共 {total} 条记录)")
                for i, r in enumerate(recs, 1):
                    print(f"{i}. {r.get('createTime', '未知')} | 项目: {r.get('sportName')} | 完成次数: {r.get('count', 0)} 次 | 耗时: {r.get('duration', 0)} 秒 | 状态: {'成功' if r.get('status')==1 else '未达标'}")
            else:
                print("\n查询失败")
                print(f"错误码: {res.get('code')}")
                print(f"原因: {res.get('message')}")
    except (KeyboardInterrupt, EOFError):
        print("\n操作已取消")

if __name__ == "__main__":
    main()

