import re

p = "scripts/synthesis.py"
s = open(p, encoding="utf-8").read()

# ===== 1. _use_god_fit：移除五格五行参与 =====
old_usegod = '''    add("人格", (wg["grids"]["ren"] or {}).get("wuxing"), 3.0)
    add("总格", (wg["grids"]["zong"] or {}).get("wuxing"), 2.0)
    add("体卦", GUA_WX.get(((mh.get("cast") or {}).get("ti") or {}).get("gua", "")), 2.0)
    for ch in (wg.get("sancai") or {}).get("combo", ""):
        add("三才", ch, 1.0)
    for c in wy.get("chars") or []:
        add(f"五音·{c.get('char','')}", c.get("wuxing"), 1.0)'''
new_usegod = '''    # 五格数理五行（人格/总格/三才）另算，不参与跨体系用神契合
    # 只取梅花体卦与五音
    add("体卦", GUA_WX.get(((mh.get("cast") or {}).get("ti") or {}).get("gua", "")), 3.0)
    for c in wy.get("chars") or []:
        add(f"五音·{c.get('char','')}", c.get("wuxing"), 2.0)'''
s = s.replace(old_usegod, new_usegod)

# ===== 2. cross_analysis：五行共振改为三源（梅花、八字、五音） =====
old_vecs = '''    vecs = {"bazi": _vec_bazi(bz), "wuge": _vec_wuge(wg),
            "meihua": _vec_meihua(mh), "wuyin": _vec_wuyin(wy)}'''
new_vecs = '''    # 五行共振：五格数理五行另算，不与其他体系共振
    # 只取梅花、八字、五音三源
    vecs = {"bazi": _vec_bazi(bz),
            "meihua": _vec_meihua(mh), "wuyin": _vec_wuyin(wy)}'''
s = s.replace(old_vecs, new_vecs)

old_keys = '''    keys = ["bazi", "wuge", "meihua", "wuyin"]'''
new_keys = '''    keys = ["bazi", "meihua", "wuyin"]'''
s = s.replace(old_keys, new_keys)

old_lacking = '''    lacking_all = [w for w in WX if all(shares[k][w] < 1e-9 for k in keys)]'''
new_lacking = '''    lacking_all = [w for w in WX if all(shares[k][w] < 1e-9 for k in keys)]
    # 五格五行主导（仅供报告参考，不入共振）
    wuge_vec = _vec_wuge(wg)
    wuge_share = _share(wuge_vec)'''
s = s.replace(old_lacking, new_lacking)

# ===== 3. _cross_items：移除五格跨体系五行比较 =====

# 3a. 移除"日主与人格"规则
old_rule2 = '''    # 2 日主与人格
    ren_wx = (wg["grids"]["ren"] or {}).get("wuxing", "")
    rel = wuxing_relation(dw, ren_wx)
    if rel in ("比和", "生我"):
        add("印证", "体用同气",
            f"日主{dw}与人格{ren_wx}为「{rel}」，命局与主运同源，心性与行事一致。",
            ["八字", "五格"])
    elif rel == "克我":
        add("张力", "名克本命",
            f"人格{ren_wx}克日主{dw}，主运对本命成压制之势，宜以柔化刚。", ["八字", "五格"])
    elif rel == "我克":
        add("调和", "命制主运",
            f"日主{dw}克人格{ren_wx}，本命对主运成统摄之势，行事以我为主。", ["八字", "五格"])
    else:
        add("调和", "本命泄于名",
            f"日主{dw}生人格{ren_wx}，力气外注于主运，付出多而收成稍缓。", ["八字", "五格"])

    # 3 体卦与日主'''
new_rule2 = '''    # 2 体卦与日主（梅花与八字同一体系）'''
s = s.replace(old_rule2, new_rule2)

# 调整规则编号
s = s.replace('''    # 3 体卦与日主''', '''    # 2 体卦与日主''')
s = s.replace('''    # 4 变卦与流通''', '''    # 3 变卦与流通''')
s = s.replace('''    # 5 三才与身强弱''', '''    # 4 梅花卦局与八字五行（同体系直接比较）''')
s = s.replace('''    # 6 五音末字与总格''', '''    # 5 五音末字与总格''')
s = s.replace('''    # 7 五行共振''', '''    # 6 五行共振''')
s = s.replace('''    # 8 卦局缺用神''', '''    # 7 卦局缺用神''')
s = s.replace('''    # 9 分数共识''', '''    # 8 分数共识''')

# 3c. 替换"三才与身强弱"为梅花-八字直接比较
old_rule5 = '''    # 5 三才与身强弱
    combo = (wg.get("sancai") or {}).get("combo", "")
    help_n = sum(1 for c in combo if c == dw or SHENG.get(c) == dw)
    drain_n = sum(1 for c in combo
                  if KE.get(c) == dw or SHENG.get(dw) == c or KE.get(dw) == c)
    strong = (bz.get("strength") or {}).get("ratio", 0.5) >= 0.5
    if strong and drain_n > help_n:
        add("印证", "三才泄旺",
            f"三才{combo}，泄克日主{dw}者 {drain_n} 位；身偏旺而得制，格能任事。",
            ["五格", "八字"])
    elif (not strong) and help_n > drain_n:
        add("印证", "三才扶弱",
            f"三才{combo}，生扶日主{dw}者 {help_n} 位；身偏弱而得扶，根基有托。",
            ["五格", "八字"])
    elif strong and help_n >= drain_n:
        add("张力", "旺而再助",
            f"三才{combo}以生扶为主（{help_n} 位），日主{dw}本已偏旺，恐过刚少制。",
            ["五格", "八字"])
    else:
        add("张力", "弱而复泄",
            f"三才{combo}以泄克为主（{drain_n} 位），日主{dw}本已偏弱，宜择时蓄力。",
            ["五格", "八字"])
    # 三才缺失项单独提示（信息价值高）
    if len(combo) == 3 and dw and dw not in combo:
        pass

    # 6 五音末字与总格'''

new_rule5 = '''    # 4 梅花卦局与八字五行（同一体系直接比较）
    mh_dist = (mh.get("wangshuai") or {}).get("distribution") or {}
    bz_stat = (bz.get("wuxing_stat") or {})
    # 卦局最旺 vs 八字最旺
    mh_max_wx = max(WX, key=lambda w: float(mh_dist.get(w, 0)))
    bz_max_wx = max(WX, key=lambda w: float((bz_stat.get(w) or {}).get("total", 0)))
    if mh_max_wx == bz_max_wx:
        add("印证", "卦命同旺",
            f"卦局最旺为{mh_max_wx}（{mh_dist.get(mh_max_wx,0):.0f}%），"
            f"八字最旺亦为{bz_max_wx}（{(bz_stat.get(bz_max_wx) or {}).get('total',0):.1f}）；"
            f"卦象与命局同气，旺衰方向一致。",
            ["梅花", "八字"])
    elif wuxing_relation(bz_max_wx, mh_max_wx) in ("生我", "比和"):
        add("调和", "卦旺生局",
            f"卦局最旺{mh_max_wx}生八字最旺{bz_max_wx}，卦象对命局有扶益之象。",
            ["梅花", "八字"])
    elif wuxing_relation(bz_max_wx, mh_max_wx) == "克我":
        add("张力", "卦旺克局",
            f"卦局最旺{mh_max_wx}克八字最旺{bz_max_wx}，卦象与命局旺处相战。",
            ["梅花", "八字"])
    else:
        add("调和", "卦局异旺",
            f"卦局最旺{mh_max_wx}，八字最旺{bz_max_wx}，二者各行其道。",
            ["梅花", "八字"])
    # 用卦与日主关系
    yong = ((mh.get("cast") or {}).get("yong") or {})
    yong_wx = yong.get("wuxing", "")
    rel_yong = wuxing_relation(dw, yong_wx)
    if rel_yong in ("比和", "生我"):
        add("印证", "用卦生助",
            f"用卦{yong.get('gua','')}属{yong_wx}，与日主{dw}「{rel_yong}」；"
            f"外境对命主有扶持之象。", ["梅花", "八字"])
    elif rel_yong == "克我":
        add("张力", "用卦压制",
            f"用卦{yong.get('gua','')}属{yong_wx}，克日主{dw}；"
            f"外境对命主成消耗之势。", ["梅花", "八字"])

    # 5 五音末字与总格'''
s = s.replace(old_rule5, new_rule5)

# 调整用神契合的 dims
s = s.replace('''            ["八字", "五格", "五音"])''', '''            ["八字", "梅花", "五音"])''', 1)
s = s.replace('''            ["八字", "五格"])''', '''            ["八字", "梅花", "五音"])''', 1)

# 调整五行共振文字
old_resonance = '''    # 7 五行共振
    if res["score"] >= 84:
        add("印证", "四源同气",
            f"四体系五行分布共振 {res['score']:.0f}%，主导之行为"
            f"{'、'.join(res['consensus_wx']) or '各有所主'}，指向一致。",
            ["四源"])
    elif res["score"] >= 72:
        add("调和", "四源大体同调",
            f"共振 {res['score']:.0f}%，主导五行{'、'.join(res['consensus_wx']) or '分散'}，"
            f"方向相近而侧重不同。", ["四源"])
    else:
        add("张力", "四源各有所主",
            f"共振仅 {res['score']:.0f}%，四体系所重不同，须分别看待，不宜强合。", ["四源"])'''
new_resonance = '''    # 6 五行共振（五格另算，三源：梅花·八字·五音）
    if res["score"] >= 84:
        add("印证", "三源同气",
            f"梅花·八字·五音三体系共振 {res['score']:.0f}%，主导之行为"
            f"{'、'.join(res['consensus_wx']) or '各有所主'}，指向一致。",
            ["梅花", "八字", "五音"])
    elif res["score"] >= 72:
        add("调和", "三源大体同调",
            f"共振 {res['score']:.0f}%，主导五行{'、'.join(res['consensus_wx']) or '分散'}，"
            f"方向相近而侧重不同。", ["梅花", "八字", "五音"])
    else:
        add("张力", "三源各有所主",
            f"共振仅 {res['score']:.0f}%，三体系所重不同，须分别看待，不宜强合。",
            ["梅花", "八字", "五音"])'''
s = s.replace(old_resonance, new_resonance)

# 分数共识中的四源
old_spread = '''    elif spread >= 24:
        lo = min(parts, key=parts.get)
        hi = max(parts, key=parts.get)
        add("张力", "长短悬殊",
            f"{SOURCE_NAME[hi]} {parts[hi]:.1f} 与 {SOURCE_NAME[lo]} {parts[lo]:.1f} "
            f"相差 {spread:.1f}，一强一弱，不可只取其一。", ["四源"])'''
new_spread = '''    elif spread >= 24:
        lo = min(parts, key=parts.get)
        hi = max(parts, key=parts.get)
        add("张力", "长短悬殊",
            f"{SOURCE_NAME[hi]} {parts[hi]:.1f} 与 {SOURCE_NAME[lo]} {parts[lo]:.1f} "
            f"相差 {spread:.1f}，一强一弱，不可只取其一。",
            [SOURCE_NAME[hi], SOURCE_NAME[lo]])'''
s = s.replace(old_spread, new_spread)

open(p, "w", encoding="utf-8").write(s)
print("cross_items & cross_analysis updated")
