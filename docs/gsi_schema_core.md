# Dota 2 GSI 核心 Schema（决策精简版）

> 只包含对 AI 决策有直接价值的字段，按决策场景分类

---

## 快速参考

```
map.game_state        → 游戏阶段判断
map.clock_time        → 时间节点决策
map.daytime           → 日夜策略
hero.health_percent   → 战斗/撤退
hero.mana_percent     → 技能使用
hero.alive            → 团战时机
player.gold           → 出装建议
abilities.*.cooldown  → 技能提醒
items.*.cooldown      → 物品提醒
buildings.*.health    → 推进决策
```

---

## 1. 时间与阶段判断

### map 模块

| 字段 | 类型 | 决策用途 | 值说明 |
|------|------|----------|--------|
| `map.game_state` | str | **阶段判断** | 见下表 |
| `map.game_time` | int | 游戏总时长（含准备期） | 秒 |
| `map.clock_time` | int | **游戏时钟** | 负数=准备期，0=开始 |
| `map.daytime` | bool | **日夜判断** | `true`=白天 |
| `map.radiant_score` | int | 天辉击杀 | 局势判断 |
| `map.dire_score` | int | 夜魇击杀 | 局势判断 |
| `map.paused` | bool | 暂停状态 | 暂停时不做决策 |
| `map.win_team` | str | 胜负结果 | `"none"`/`"radiant"`/`"dire"` |

### game_state 关键值

| 值 | 决策意义 |
|----|----------|
| `DOTA_GAMERULES_STATE_HERO_SELECTION` | 选人阶段，可做 BP 建议 |
| `DOTA_GAMERULES_STATE_STRATEGY_TIME` | 策略时间，可做出装路线建议 |
| `DOTA_GAMERULES_STATE_PRE_GAME` | 准备阶段，提示购买起始装 |
| `DOTA_GAMERULES_STATE_GAME_IN_PROGRESS` | **核心决策阶段** |
| `DOTA_GAMERULES_STATE_POST_GAME` | 游戏结束，停止决策 |

### 重要时间节点

| clock_time | 事件 | 决策建议 |
|------------|------|----------|
| 0:00 | 游戏开始 | 出门装提醒 |
| 每 2:00 | 符文刷新 | 控符提醒 |
| 5:00 | 白天开始 | gank 窗口 |
| 7:00 | 中立物品 T1 掉落 | 打野提醒 |
| 10:00 | 前哨激活 | 前哨提醒 |
| 17:00 | 中立物品 T2 掉落 | |
| 20:00 | 肉山首次最佳窗口 | 肉山提醒 |
| 27:00 | 中立物品 T3 掉落 | |
| 37:00 | 中立物品 T4 掉落 | |
| 60:00 | 中立物品 T5 掉落 | |

---

## 2. 战斗与生存决策

### hero 模块

| 字段 | 类型 | 决策用途 | 阈值建议 |
|------|------|----------|----------|
| `hero.health` | int | 绝对生命值 | |
| `hero.max_health` | int | 最大生命值 | |
| `hero.health_percent` | int | **生命百分比** | <30% 危险，<15% 极危 |
| `hero.mana` | int | 绝对魔法值 | |
| `hero.max_mana` | int | 最大魔法值 | |
| `hero.mana_percent` | int | **魔法百分比** | <20% 魔量不足 |
| `hero.alive` | bool | **存活状态** | `false`=已死亡 |
| `hero.respawn_seconds` | int | 复活倒计时 | 团战时机判断 |

### 控制状态（是否能行动）

| 字段 | 含义 | 决策 |
|------|------|------|
| `hero.stunned` | 被眩晕 | 无法行动 |
| `hero.silenced` | 被沉默 | 只能普攻 |
| `hero.hexed` | 被变羊 | 无法行动 |
| `hero.disarmed` | 被缴械 | 无法普攻 |
| `hero.muted` | 被禁用物品 | 物品不可用 |
| `hero.break` | 被破坏 | 被动失效 |
| `hero.magicimmune` | 魔免中 | 可进攻 |
| `hero.smoked` | 烟雾中 | gank 状态 |

### 买活决策

| 字段 | 类型 | 说明 |
|------|------|------|
| `hero.buyback_cost` | int | 买活费用 |
| `hero.buyback_cooldown` | int | 买活冷却（秒） |
| `player.gold` | int | 当前金币 |
| `player.gold_reliable` | int | 可靠金币（不因死亡丢失） |

**买活决策逻辑**：
```
可买活 = gold >= buyback_cost AND buyback_cooldown == 0
应买活 = 可买活 AND (高地团战 OR 关键时刻)
```

---

## 3. 技能使用决策

### abilities 模块

| 字段 | 类型 | 决策用途 |
|------|------|----------|
| `abilities.ability{N}.name` | str | 技能名（用于识别） |
| `abilities.ability{N}.level` | int | 技能等级（0=未学） |
| `abilities.ability{N}.can_cast` | bool | **当前可否释放** |
| `abilities.ability{N}.cooldown` | int | **当前冷却** |
| `abilities.ability{N}.max_cooldown` | int | 最大冷却 |
| `abilities.ability{N}.ultimate` | bool | 是否大招 |
| `abilities.ability{N}.passive` | bool | 是否被动 |

### 决策逻辑示例

```python
# 大招可用检测
def ult_ready(abilities):
    for key, skill in abilities.items():
        if skill.get('ultimate') and skill.get('level', 0) > 0:
            return skill.get('can_cast', False)
    return False

# 技能冷却提醒
def skill_coming_up(ability, threshold=3):
    """技能即将就绪提醒"""
    cd = ability.get('cooldown', 0)
    return 0 < cd <= threshold
```

---

## 4. 物品使用决策

### items 模块

**核心槽位**：`slot0` ~ `slot5`（主背包）、`teleport0`（TP）

| 字段 | 类型 | 决策用途 |
|------|------|----------|
| `items.{slot}.name` | str | 物品名（`"empty"` = 空） |
| `items.{slot}.can_cast` | bool | **当前可否使用** |
| `items.{slot}.cooldown` | int | **当前冷却** |
| `items.{slot}.charges` | int | 充能数（魔棒等） |

### 关键物品监控

| 物品 | 监控点 | 提醒场景 |
|------|--------|----------|
| `item_magic_stick/wand` | `charges > 10` | 低血时提醒使用 |
| `item_black_king_bar` | `cooldown == 0` | 团战前提醒 |
| `item_blink` | `cooldown == 0` | 先手/逃跑 |
| `item_tpscroll` | `cooldown == 0` | 支援提醒 |
| `item_refresher` | `cooldown == 0` | 大招可刷新 |
| `item_aegis` | 存在 | 肉山盾提醒 |

---

## 5. 经济决策

### player 模块

| 字段 | 类型 | 决策用途 |
|------|------|----------|
| `player.gold` | int | **当前总金币** |
| `player.gold_reliable` | int | 可靠金币 |
| `player.gold_unreliable` | int | 不可靠金币 |
| `player.gpm` | int | 每分钟金币 |
| `player.xpm` | int | 每分钟经验 |
| `player.last_hits` | int | 正补数 |

### 出装建议触发

```python
# 关键物品节点（金币达到时提醒）
ITEM_THRESHOLDS = {
    2150: "可以买跳刀",
    2700: "可以买 BKB",
    4200: "可以买羊刀",
    5050: "可以买大根",
}

def check_item_suggestion(gold):
    for threshold, msg in ITEM_THRESHOLDS.items():
        if gold >= threshold:
            return msg
```

---

## 6. 推进与防守

### buildings 模块

| 建筑 | 路径 | 满血 | 决策 |
|------|------|------|------|
| 一塔 | `buildings.{team}.dota_*_tower1_*` | 1800 | 对线阶段重点 |
| 二塔 | `buildings.{team}.dota_*_tower2_*` | 2500 | 中期推进 |
| 三塔 | `buildings.{team}.dota_*_tower3_*` | 2500 | 高地防守 |
| 高地塔 | `buildings.{team}.dota_*_tower4_*` | 2600 | 关键防线 |
| 兵营 | `buildings.{team}.*_rax_*` | 2200/1300 | 超级兵触发 |
| 基地 | `buildings.{team}.dota_*_fort` | 4500 | 胜负关键 |

### 推进建议逻辑

```python
def should_push(our_buildings, enemy_buildings, our_team):
    """判断是否应该推进"""
    enemy_team = "dire" if our_team == "radiant" else "radiant"

    # 检查敌方外塔血量
    for lane in ["top", "mid", "bot"]:
        tower = f"dota_{'badguys' if enemy_team == 'dire' else 'goodguys'}_tower1_{lane}"
        if tower in enemy_buildings:
            hp = enemy_buildings[tower].get('health', 0)
            max_hp = enemy_buildings[tower].get('max_health', 1800)
            if hp < max_hp * 0.5:
                return f"推进 {lane} 路，敌方一塔血量 {hp}/{max_hp}"
    return None
```

---

## 7. 位置与视野

### minimap 模块（简化使用）

| 字段 | 决策用途 |
|------|----------|
| `minimap.o{N}.xpos/ypos` | 单位坐标 |
| `minimap.o{N}.team` | 阵营（2=天辉, 3=夜魇） |
| `minimap.o{N}.unitname` | 单位名（识别英雄/建筑） |

### 位置决策示例

```python
def count_visible_enemies(minimap, my_team):
    """统计视野内敌方英雄数量"""
    enemy_team = 3 if my_team == 2 else 2
    count = 0
    for key, unit in minimap.items():
        if unit.get('team') == enemy_team:
            if 'hero' in unit.get('unitname', ''):
                count += 1
    return count

def missing_enemy_alert(visible_enemies, total_enemies=5):
    """敌人缺失警报"""
    missing = total_enemies - visible_enemies
    if missing >= 3:
        return "警告：3人以上缺失，小心 gank！"
```

---

## 8. 综合决策模板

```python
class DecisionEngine:
    def analyze(self, gsi_data):
        suggestions = []

        hero = gsi_data.get('hero', {})
        player = gsi_data.get('player', {})
        map_info = gsi_data.get('map', {})

        # 1. 生存检查
        if hero.get('health_percent', 100) < 30:
            if hero.get('stunned') or hero.get('silenced'):
                suggestions.append("⚠️ 危险！血量低且被控")
            else:
                suggestions.append("⚠️ 血量过低，考虑撤退")

        # 2. 大招检查
        abilities = gsi_data.get('abilities', {})
        for key, skill in abilities.items():
            if skill.get('ultimate') and skill.get('can_cast'):
                suggestions.append(f"💥 大招可用")
                break

        # 3. 买活检查
        if not hero.get('alive', True):
            cost = hero.get('buyback_cost', 999999)
            cd = hero.get('buyback_cooldown', 999)
            gold = player.get('gold', 0)
            if gold >= cost and cd == 0:
                suggestions.append("💰 可以买活")

        # 4. 时间节点
        clock = map_info.get('clock_time', 0)
        if clock > 0 and clock % 120 < 10:  # 符文刷新
            suggestions.append("🔮 符文即将/刚刚刷新")

        return suggestions
```

---

## 附录：常用英雄名映射

| hero.name | 中文名 |
|-----------|--------|
| `npc_dota_hero_storm_spirit` | 风暴之灵 |
| `npc_dota_hero_antimage` | 敌法师 |
| `npc_dota_hero_phantom_assassin` | 幻影刺客 |
| `npc_dota_hero_invoker` | 祈求者 |
| `npc_dota_hero_pudge` | 帕吉 |

（完整映射需参考 Dota 2 数据文件或 OpenDota API）
