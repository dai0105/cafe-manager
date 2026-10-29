from django.shortcuts import render, redirect
import random

STAFF_LIST = [

    # エース
    {
        "name": "佐藤",
        "capacity": 90,
        "daily_wage": 18000,
        "remaining_days": 6,
    },
    {
        "name": "高橋",
        "capacity": 80,
        "daily_wage": 16000,
        "remaining_days": 8,
    },

    # ベテラン
    {
        "name": "山田",
        "capacity": 70,
        "daily_wage": 13000,
        "remaining_days": 10,
    },
    {
        "name": "中村",
        "capacity": 65,
        "daily_wage": 12000,
        "remaining_days": 12,
    },

    # 中堅
    {
        "name": "鈴木",
        "capacity": 60,
        "daily_wage": 10000,
        "remaining_days": 14,
    },
    {
        "name": "伊藤",
        "capacity": 55,
        "daily_wage": 9000,
        "remaining_days": 15,
    },

    # 新人
    {
        "name": "渡辺",
        "capacity": 50,
        "daily_wage": 7000,
        "remaining_days": 18,
    },
    {
        "name": "小林",
        "capacity": 45,
        "daily_wage": 6000,
        "remaining_days": 20,
    },
]

def generate_weather():
    return random.choices(
        ["晴れ", "曇り", "雨", "台風"],
        weights=[45, 30, 20, 5],
        k=1,
    )[0]

def title_view(request):

    best_score = request.session.get(
        "best_score",
        0
    )

    context = {
        "best_score": best_score,
    }

    return render(
        request,
        "game/title.html",
        context
    )


def start_game(request):

    request.session.pop(
        "ending_reason",
        None
    )

    request.session["day"] = 30
    request.session["money"] = 300000

    # 店舗評価
    request.session["reputation"] = 50

    request.session["staff_list"] = STAFF_LIST

    # Day1の天気を確定して保存
    request.session["today_weather"] = generate_weather()

    # 前回の選択状態を消す
    request.session.pop("selected_staff", None)

    return redirect("dashboard")

def dashboard_view(request):

    day = request.session.get("day", 1)
    money = request.session.get("money", 300000)
    reputation = request.session.get("reputation", 50)
    staff_list = request.session.get(
        "staff_list",
        []
    )

    today_weather = request.session.get("today_weather")

    # セッションに天気がない場合だけ生成
    if not today_weather:
        today_weather = generate_weather()
        request.session["today_weather"] = today_weather


    context = {
        "day": day,
        "money": money,
        "reputation": reputation,
        "staff_list": staff_list,
        "today_weather": today_weather,
    }

    return render(
        request,
        "game/dashboard.html",
        context
    )

def result_view(request):

    day = request.session.get("day", 1)

    # 総スタッフ数
    staff_count = request.session.get("staff_count", 3)
    
    # 現時点では全員出勤
    working_staff = staff_count

    # シフト編成前に決めた天気を使う
    weather = request.session.get(
        "today_weather",
        "晴れ",
    )

    reputation = request.session.get("reputation", 50)

    # 全スタッフを取得
    staff_list = request.session.get("staff_list", [])

    # 出勤選択画面で選んだスタッフ名
    selected_names = request.session.get("selected_staff", [])

    # 選択されたスタッフのデータだけ取り出す
    selected_staff = [
        staff
        for staff in staff_list
        if staff["name"] in selected_names
        and staff["remaining_days"] > 0
    ]

    # 出勤人数
    working_staff = len(selected_staff)

    # 念のため、2人未満なら選択画面へ戻す
    if working_staff < 2:
        return redirect("select_staff")

    # この日の評価変動の合計
    reputation_change = 0
    reputation_logs = []

    # 選択スタッフの対応可能人数の合計
    capacity = sum(
        staff["capacity"]
        for staff in selected_staff
    )

    average_capacity = round(
        sum(
            staff["capacity"]
            for staff in selected_staff
        ) / working_staff
    )

    # 選択スタッフの日給合計
    labor_cost = sum(
        staff["daily_wage"]
        for staff in selected_staff
    )


    if weather == "晴れ":
        base_visitors = random.randint(140, 220)

    elif weather == "曇り":
        base_visitors = random.randint(100, 160)

    elif weather == "雨":
        base_visitors = random.randint(60, 120)

    else:
        base_visitors = random.randint(10, 50)

    # 評価ボーナス
    # 店舗評価補正
    visitors = int(
        base_visitors  * (1 + reputation / 300)
    )

    bonus_visitors = visitors - base_visitors

    # 常連客イベント
    regular_customer = False
    regular_bonus = 0

    if reputation >= 90:
        regular_customer = random.random() < 0.40

    elif reputation >= 70:
        regular_customer = random.random() < 0.20

    elif reputation >= 50:
        regular_customer = random.random() < 0.10

    if regular_customer:
        regular_bonus = random.randint(20, 50)
        visitors += regular_bonus

        # 常連客による評価上昇
        reputation_change += 1
        reputation_logs.append(
            "☕ 常連客来店 +1"
        )

    # クレームイベント
    complaint = False
    complaint_rate = 0.15
    complaint_penalty = 0
    complaint_text = ""

    # 出勤スタッフ平均能力で補正
    if average_capacity >= 75:
        complaint_rate -= 0.08

    elif average_capacity >= 60:
        complaint_rate -= 0.04

    elif average_capacity <= 45:
        complaint_rate += 0.10

    elif average_capacity <= 55:
        complaint_rate += 0.05

    # 店舗評価で補正
    if reputation >= 80:
        complaint_rate -= 0.05

    elif reputation <= 40:
        complaint_rate += 0.05

    # 上限下限
    complaint_rate = max(
        0.01,
        min(complaint_rate, 0.50)
    )

    # クレーム発生判定
    complaint = random.random() < complaint_rate

    if complaint:
        complaint_penalty = random.randint(10, 30)

        visitors = max(
            visitors - complaint_penalty,
            0,
        )

        complaint_messages = [
            "コーヒーがぬるい",
            "提供が遅い",
            "店内清掃が不十分",
            "接客態度が悪い",
        ]

        complaint_text = random.choice(complaint_messages)

        # クレームによる評価低下
        reputation_change -= 2
        reputation_logs.append(
            "⚠ クレーム発生 -2"
        )

    # 高品質な接客
    if average_capacity >= 70:
        reputation_change += 2
        reputation_logs.append(
            "⭐ 高品質な接客 +2"
        )

    elif average_capacity >= 60:
        reputation_change += 1
        reputation_logs.append(
            "⭐ 良好な接客 +1"
        )

    # 出勤人数による来客上限

    # 人員制限をかける前の来客予定数
    expected_visitors = visitors

    # 対応可能人数までに制限
    visitors = min(expected_visitors, capacity)

    # 対応できなかった人数
    lost_visitors = max(expected_visitors - visitors, 0)

    # 大きな機会損失が発生した場合は評価低下
    if lost_visitors >= 60:
        reputation_change -= 2
        reputation_logs.append(
            "⚠ 大きな機会損失 -2"
        )

    elif lost_visitors >= 30:
        reputation_change -= 1
        reputation_logs.append(
            "⚠ 機会損失 -1"
        )

    # 客単価
    # 新商品イベント
    new_product = False
    new_product_name = ""
    new_product_bonus = 0

    product_events = [
        {
            "name": "期間限定ラテ",
            "bonus": 100,
        },
        {
            "name": "プレミアムケーキ",
            "bonus": 150,
        },
        {
            "name": "季節限定フラッペ",
            "bonus": 200,
        },
    ]

    if random.random() < 0.05:
        reputation_change += 1
        reputation_logs.append(
            "🧁 新商品販売開始 +1"
        )

        new_product = True

        event = random.choice(
            product_events
        )

        new_product_name = event["name"]

        new_product_bonus = event["bonus"]

    unit_price = random.randint(450, 650)
    unit_price += new_product_bonus

    # 売上
    sales = visitors * unit_price

    # 仕入れ費
    ingredient_cost = int(sales * 0.25)

    # 利益
    profit = sales - labor_cost - ingredient_cost

    # 利益による評価変動
    if profit >= 50000:
        reputation_change += 2
        reputation_logs.append(
            "💰 大幅黒字 +2"
        )

    elif profit >= 30000:
        reputation_change += 1
        reputation_logs.append(
            "💰 黒字営業 +1"
        )

    elif profit <= 0:
        reputation_change -= 2
        reputation_logs.append(
            "📉 赤字営業 -2"
        )

    elif profit <= 10000:
        reputation_change -= 1
        reputation_logs.append(
            "📉 利益低下 -1"
        )

    # 店長日報
    daily_report = ""
    if reputation_change >= 4:
        daily_report = (
            "最高の営業日でした。スタッフの活躍により、お客様から高い評価を獲得しました。"
        )

    elif reputation_change >= 2:
        daily_report = (
            "好調な営業となりました。店舗の評判も順調に上昇しています。"
        )

    elif reputation_change >= 0:
        daily_report = (
            "大きな問題もなく、安定した営業を行うことができました。"
        )

    elif reputation_change >= -2:
        daily_report = (
            "営業自体はできましたが、お客様対応に改善の余地が残りました。"
        )

    else:
        daily_report = (
            "厳しい営業日となりました。店舗運営を見直す必要がありそうです。"
        )

    if weather == "台風" and profit > 0:
        daily_report += (
            " 台風の中でも営業を続け、売上を確保しました。"
        )

    if regular_customer:
        daily_report += (
            " 常連のお客様の来店もあり、店内は賑わいました。"
        )

    if new_product:
        daily_report += (
            " 新商品の反応も良く、多くのお客様に興味を持っていただけました。"
        )


    # 評価変動を反映
    reputation += reputation_change

    # 評価を0～100に収める
    reputation = max(
        0,
        min(reputation, 100),
    )

    # セッションへ保存
    request.session["reputation"] = reputation

    money = request.session.get("money", 300000)

    money += profit

    request.session["money"] = money


    context = {
        # 既存の項目
        "day": day,
        "weather": weather,
        "money": money,
        "reputation": reputation,
        "reputation_change": reputation_change,
        "reputation_logs": reputation_logs,

        # 選択スタッフ
        "selected_staff": selected_staff,
        "working_staff": working_staff,
        "capacity": capacity,

        # 来客
        "base_visitors": base_visitors,
        "bonus_visitors": bonus_visitors,
        "expected_visitors": expected_visitors,
        "visitors": visitors,
        "lost_visitors": lost_visitors,

        # 売上と経費
        "unit_price": unit_price,
        "sales": sales,
        "labor_cost": labor_cost,
        "ingredient_cost": ingredient_cost,
        "profit": profit,

        # イベント
        "regular_customer": regular_customer,
        "regular_bonus": regular_bonus,
        "complaint": complaint,
        "complaint_penalty": complaint_penalty,
        "complaint_text": complaint_text,
        "average_capacity": average_capacity,
        "complaint_rate": round(
            complaint_rate * 100,
            1
        ),
        "new_product": new_product,
        "new_product_name": new_product_name,
        "new_product_bonus": new_product_bonus,
        "daily_report": daily_report,
    }

    return render(
        request,
        "game/result.html",
        context
    )

def next_day(request):
    day = request.session.get("day", 1)
    day += 1

    request.session["day"] = day

    if day > 30:
        return redirect("ending")

    # 新しい日の天気を確定
    request.session["today_weather"] = generate_weather()

    # 前日の選択スタッフを解除
    request.session.pop("selected_staff", None)

    return redirect("dashboard")

def ending_view(request):

    money = request.session.get(
        "money",
        300000
    )

    reputation = request.session.get(
        "reputation",
        50
    )

    day = request.session.get(
        "day",
        1
    )

    ending_reason = request.session.get(
        "ending_reason",
        ""
    )

    # ゲームオーバー
    if ending_reason:

        context = {
            "day": day,
            "money": money,
            "reputation": reputation,
            "ending_reason": ending_reason,
        }

        return render(
            request,
            "game/ending.html",
            context
        )

    # 通常エンド
    # 総合スコア
    score = (
        reputation * 100
        + money // 1000
    )

    # これまでの最高スコア
    best_score = request.session.get(
        "best_score",
        0
    )

    # BEST更新判定
    is_new_record = False

    if score > best_score:

        best_score = score

        request.session["best_score"] = best_score

        is_new_record = True

    if score >= 10000:
        rank = "S"
        title = "伝説の店長"
        message = (
            "あなたの店は街一番の人気店になりました。"
        )

    elif score >= 8000:
        rank = "A"
        title = "カリスマ店長"
        message = (
            "多くの常連客に愛される人気店です。"
        )

    elif score >= 6000:
        rank = "B"
        title = "人気店店長"
        message = (
            "安定した経営を続けました。"
        )

    elif score >= 4000:
        rank = "C"
        title = "地域密着店長"
        message = (
            "地域に根付いたお店を作りました。"
        )

    else:
        rank = "D"
        title = "駆け出し店長"
        message = (
            "まだまだ成長の余地があります。"
        )

    context = {
        "money": money,
        "reputation": reputation,
        "score": score,
        "rank": rank,
        "title": title,
        "message": message,
        "best_score": best_score,
        "is_new_record": is_new_record,
    }

    return render(
        request,
        "game/ending.html",
        context
    )

def select_staff_view(request):
    staff_list = request.session.get(
        "staff_list",
        [],
    )

    available_staff = [
        staff
        for staff in staff_list
        if staff["remaining_days"] > 0
    ]

    if len(available_staff) < 2:

        request.session["ending_reason"] = (
            "スタッフ不足で営業継続不能"
        )

        return redirect("ending")

    today_weather = request.session.get(
        "today_weather",
        "晴れ",
    )

    if request.method == "POST":
        selected_names = request.POST.getlist(
            "staff"
        )

        # 選択人数を確認
        if len(selected_names) < 2:
            return render(
                request,
                "game/select_staff.html",
                {
                    "staff_list": staff_list,
                    "today_weather": today_weather,
                    "error": "2人以上選択してください",
                }
            )

        if len(selected_names) > 4:
            return render(
                request,
                "game/select_staff.html",
                {
                    "staff_list": staff_list,
                    "today_weather": today_weather,
                    "error": "4人以下にしてください",
                }
            )

        # 選ばれたスタッフを取得
        selected_staff = [
            staff
            for staff in staff_list
            if staff["name"] in selected_names
        ]

        # 不正な名前が送信されていないか確認
        if len(selected_staff) != len(selected_names):
            return render(
                request,
                "game/select_staff.html",
                {
                    "staff_list": staff_list,
                    "today_weather": today_weather,
                    "error": "スタッフの選択内容が不正です",
                }
            )

        # 出勤回数が残っているか確認
        unavailable_staff = [
            staff["name"]
            for staff in selected_staff
            if staff["remaining_days"] <= 0
        ]

        if unavailable_staff:
            return render(
                request,
                "game/select_staff.html",
                {
                    "staff_list": staff_list,
                    "today_weather": today_weather,
                    "error": (
                        "出勤可能回数が残っていないスタッフが"
                        "選択されています"
                    ),
                }
            )

        # 選択スタッフの残り出勤回数を1減らす
        for staff in staff_list:
            if staff["name"] in selected_names:
                staff["remaining_days"] -= 1

        # 更新したスタッフ一覧をセッションに保存
        request.session["staff_list"] = staff_list

        # 今日の出勤スタッフを保存
        request.session["selected_staff"] = selected_names

        return redirect("result")

    return render(
        request,
        "game/select_staff.html",
        {
            "staff_list": staff_list,
            "today_weather": today_weather,
        },
    )