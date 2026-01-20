# Dota 2 GSI 完整 Schema 文档

> 基于实际采集数据分析生成，包含所有发现的字段

---

## 概览

| 模块 | 字段数 | 说明 |
|------|--------|------|
| provider | 5 | 数据源信息 |
| map | 14 | 地图/比赛状态 |
| player | 25 | 当前玩家信息 |
| hero | 39 | 控制的英雄状态 |
| abilities | 46 | 技能信息 |
| items | 66 | 物品栏 |
| buildings | 53 | 建筑物状态 |
| minimap | 1261 | 小地图单位（动态） |
| wearables | 10 | 饰品装备 |
| league | 10 | 联赛信息 |
| draft | 1 | 选人阶段 |
| events | 1 | 事件列表 |
| roshan | 1 | 肉山状态 |
| couriers | 1 | 信使状态 |
| neutralitems | 1 | 中立物品 |
| previously | 619 | 上一帧变化的字段 |
| added | 84 | 本帧新增的字段 |

---

## 1. provider - 数据源信息

提供 GSI 数据的客户端信息。

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `provider.name` | str | 游戏名称 | `"Dota 2"` |
| `provider.appid` | int | Steam AppID | `570` |
| `provider.version` | int | GSI 协议版本 | `48` |
| `provider.timestamp` | int | Unix 时间戳（秒） | `1768894970` |

---

## 2. map - 地图/比赛状态

当前比赛的全局状态。

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `map.name` | str | 地图名称 | `"start"` |
| `map.matchid` | str | 比赛 ID | `"0"` (自定义游戏) |
| `map.game_time` | int | 游戏时间（秒，含准备阶段） | `50` |
| `map.clock_time` | int | 游戏时钟（秒，0:00 开始计） | `-87` (负数=准备阶段) |
| `map.daytime` | bool | 是否白天 | `false` |
| `map.nightstalker_night` | bool | 是否暗夜魔王的黑夜 | `false` |
| `map.radiant_score` | int | 天辉击杀数 | `0` |
| `map.dire_score` | int | 夜魇击杀数 | `0` |
| `map.game_state` | str | 游戏阶段 | 见下表 |
| `map.paused` | bool | 是否暂停 | `false` |
| `map.win_team` | str | 获胜方 | `"none"` / `"radiant"` / `"dire"` |
| `map.customgamename` | str | 自定义游戏名 | `""` |
| `map.ward_purchase_cooldown` | int | 眼购买冷却（秒） | `0` |

### game_state 可能的值

| 值 | 含义 |
|----|------|
| `DOTA_GAMERULES_STATE_INIT` | 初始化 |
| `DOTA_GAMERULES_STATE_WAIT_FOR_PLAYERS_TO_LOAD` | 等待玩家加载 |
| `DOTA_GAMERULES_STATE_HERO_SELECTION` | 选择英雄 |
| `DOTA_GAMERULES_STATE_STRATEGY_TIME` | 策略时间 |
| `DOTA_GAMERULES_STATE_PRE_GAME` | 准备阶段（0:00前） |
| `DOTA_GAMERULES_STATE_GAME_IN_PROGRESS` | 游戏进行中 |
| `DOTA_GAMERULES_STATE_POST_GAME` | 游戏结束 |
| `DOTA_GAMERULES_STATE_DISCONNECT` | 断开连接 |

---

## 3. player - 当前玩家信息

控制当前客户端的玩家数据。

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `player.steamid` | str | Steam 64位 ID | `"76561198100175922"` |
| `player.accountid` | str | Steam 账户 ID | `"139910194"` |
| `player.name` | str | 玩家昵称 | `"XinG"` |
| `player.activity` | str | 当前活动 | `"playing"` / `"menu"` |
| `player.team_name` | str | 所属阵营 | `"radiant"` / `"dire"` |
| `player.player_slot` | int | 玩家槽位（0-9） | `0` |
| `player.team_slot` | int | 队内槽位（0-4） | `0` |
| **击杀/死亡** |
| `player.kills` | int | 击杀数 | `0` |
| `player.deaths` | int | 死亡数 | `0` |
| `player.assists` | int | 助攻数 | `0` |
| `player.kill_streak` | int | 连杀数 | `0` |
| `player.kill_list` | dict | 击杀详情 | `{}` |
| **经济** |
| `player.gold` | int | 当前金币 | `600` |
| `player.gold_reliable` | int | 可靠金币 | `0` |
| `player.gold_unreliable` | int | 不可靠金币 | `600` |
| `player.gold_from_hero_kills` | int | 来自英雄击杀 | `0` |
| `player.gold_from_creep_kills` | int | 来自小兵击杀 | `0` |
| `player.gold_from_income` | int | 来自被动收入 | `0` |
| `player.gold_from_shared` | int | 来自分享 | `0` |
| `player.gpm` | int | 每分钟金币 | `0` |
| `player.xpm` | int | 每分钟经验 | `0` |
| **补刀** |
| `player.last_hits` | int | 正补数 | `0` |
| `player.denies` | int | 反补数 | `0` |
| **其他** |
| `player.commands_issued` | int | 发出的命令数 | `0` |

---

## 4. hero - 英雄状态

当前控制的英雄详细信息。

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| **基础信息** |
| `hero.id` | int | 英雄 ID | `17` (风暴之灵) |
| `hero.name` | str | 英雄内部名 | `"npc_dota_hero_storm_spirit"` |
| `hero.level` | int | 等级 | `1` |
| `hero.xp` | int | 当前经验 | `0` |
| `hero.facet` | int | 命石槽位 | `2` |
| **位置** |
| `hero.xpos` | int | X 坐标 | `-6700` |
| `hero.ypos` | int | Y 坐标 | `-6700` |
| **生命/魔法** |
| `hero.health` | int | 当前生命值 | `582` |
| `hero.max_health` | int | 最大生命值 | `582` |
| `hero.health_percent` | int | 生命百分比 | `100` |
| `hero.mana` | int | 当前魔法值 | `351` |
| `hero.max_mana` | int | 最大魔法值 | `351` |
| `hero.mana_percent` | int | 魔法百分比 | `100` |
| **状态** |
| `hero.alive` | bool | 是否存活 | `true` |
| `hero.respawn_seconds` | int | 复活倒计时（秒） | `0` |
| `hero.buyback_cost` | int | 买活费用 | `246` |
| `hero.buyback_cooldown` | int | 买活冷却（秒） | `0` |
| **控制效果** |
| `hero.silenced` | bool | 被沉默 | `false` |
| `hero.stunned` | bool | 被眩晕 | `false` |
| `hero.disarmed` | bool | 被缴械 | `false` |
| `hero.magicimmune` | bool | 魔法免疫 | `false` |
| `hero.hexed` | bool | 被变羊 | `false` |
| `hero.muted` | bool | 被禁用物品 | `false` |
| `hero.break` | bool | 被破坏（禁用被动） | `false` |
| `hero.smoked` | bool | 烟雾状态 | `false` |
| `hero.has_debuff` | bool | 有负面效果 | `false` |
| **装备** |
| `hero.aghanims_scepter` | bool | 有阿哈利姆神杖 | `false` |
| `hero.aghanims_shard` | bool | 有阿哈利姆魔晶 | `false` |
| **天赋** |
| `hero.talent_1` ~ `hero.talent_8` | bool | 天赋是否学习 | `false` |
| `hero.attributes_level` | int | 属性加点等级 | `0` |
| **永久增益** |
| `hero.permanent_buffs` | dict | 永久 buff（如肉山盾） | `{}` |

---

## 5. abilities - 技能信息

英雄的技能状态，以 `ability0` ~ `abilityN` 形式存储。

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `abilities.ability{N}.name` | str | 技能内部名 | `"storm_spirit_static_remnant"` |
| `abilities.ability{N}.level` | int | 技能等级 | `0` |
| `abilities.ability{N}.can_cast` | bool | 当前是否可释放 | `false` |
| `abilities.ability{N}.passive` | bool | 是否被动技能 | `false` |
| `abilities.ability{N}.ability_active` | bool | 技能是否激活 | `true` |
| `abilities.ability{N}.cooldown` | int | 当前冷却（秒） | `0` |
| `abilities.ability{N}.max_cooldown` | int | 最大冷却（秒） | `0` |
| `abilities.ability{N}.ultimate` | bool | 是否大招 | `false` |

### 技能槽位说明
- `ability0` ~ `ability3`: 主要技能（Q/W/E/R）
- `ability4`+: 额外技能（天赋、命石技能等）

---

## 6. items - 物品栏

物品信息，包括主背包、背包、TP、中立物品等槽位。

### 槽位类型

| 槽位 | 说明 |
|------|------|
| `slot0` ~ `slot5` | 主物品栏（6格） |
| `slot6` ~ `slot8` | 背包（3格） |
| `stash0` ~ `stash5` | 储藏处（6格） |
| `teleport0` | TP 卷轴槽 |
| `neutral0`, `neutral1` | 中立物品槽 |
| `preserved_neutral6` ~ `preserved_neutral10` | 保存的中立物品 |

### 物品字段

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `items.{slot}.name` | str | 物品内部名 | `"item_tpscroll"` / `"empty"` |
| `items.{slot}.purchaser` | int | 购买者槽位 | `0` |
| `items.{slot}.item_level` | int | 物品等级 | `1` |
| `items.{slot}.can_cast` | bool | 是否可使用 | `false` |
| `items.{slot}.cooldown` | int | 当前冷却（秒） | `100` |
| `items.{slot}.max_cooldown` | int | 最大冷却（秒） | `101` |
| `items.{slot}.passive` | bool | 是否被动物品 | `false` |
| `items.{slot}.charges` | int | 当前充能数 | `1` |
| `items.{slot}.item_charges` | int | 物品充能数 | `1` |

---

## 7. buildings - 建筑物状态

双方阵营的塔、兵营、基地血量。

### 建筑结构

```
buildings
├── radiant (天辉)
│   ├── dota_goodguys_tower1_top/mid/bot     (一塔)
│   ├── dota_goodguys_tower2_top/mid/bot     (二塔)
│   ├── dota_goodguys_tower3_top/mid/bot     (三塔)
│   ├── dota_goodguys_tower4_top/bot         (高地塔)
│   ├── good_rax_melee_top/mid/bot           (近战兵营)
│   ├── good_rax_range_top/mid/bot           (远程兵营)
│   └── dota_goodguys_fort                   (基地)
└── dire (夜魇)
    └── (结构相同，前缀为 badguys)
```

### 建筑字段

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `buildings.{team}.{building}.health` | int | 当前血量 | `1800` |
| `buildings.{team}.{building}.max_health` | int | 最大血量 | `1800` |

### 建筑生命值参考

| 建筑类型 | 满血值 |
|----------|--------|
| 一塔 | 1800 |
| 二塔、三塔 | 2500 |
| 高地塔 | 2600 |
| 近战兵营 | 2200 |
| 远程兵营 | 1300 |
| 基地 | 4500 |

---

## 8. minimap - 小地图单位

视野内所有单位的位置信息，以 `o0`, `o1`, ... 形式存储。

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `minimap.o{N}.xpos` | int | X 坐标 | `-4672` |
| `minimap.o{N}.ypos` | int | Y 坐标 | `-4552` |
| `minimap.o{N}.image` | str | 小地图图标类型 | 见下表 |
| `minimap.o{N}.team` | int | 阵营 | `2`=天辉, `3`=夜魇, `4`=中立, `5`=其他 |
| `minimap.o{N}.yaw` | int | 朝向角度 | `135` |
| `minimap.o{N}.unitname` | str | 单位内部名 | `"npc_dota_goodguys_melee_rax_mid"` |
| `minimap.o{N}.visionrange` | int | 视野范围 | `600` |

### image 图标类型

| 值 | 含义 |
|----|------|
| `minimap_hero` | 英雄 |
| `minimap_creep` | 小兵 |
| `minimap_ancient` | 基地 |
| `minimap_tower` | 防御塔 |
| `minimap_racks45` / `minimap_racks90` | 兵营 |
| `minimap_ward_obs` | 侦查守卫 |
| `minimap_ward_sent` | 岗哨守卫 |
| `minimap_watcher` | 观察者/灯笼 |
| `minimap_miscbuilding` | 其他建筑 |
| `minimap_plaincircle` | 普通圆圈 |

### team 阵营值

| 值 | 含义 |
|----|------|
| `2` | 天辉 (Radiant) |
| `3` | 夜魇 (Dire) |
| `4` | 中立 |
| `5` | 其他/无阵营 |

---

## 9. wearables - 饰品装备

英雄穿戴的饰品 ID。

| 字段 | 类型 | 说明 |
|------|------|------|
| `wearables.wearable{N}` | int | 饰品 ID |

---

## 10. league - 联赛信息

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `league.league_id` | int | 联赛 ID | `0` |
| `league.match_id` | str | 比赛 ID | `"0"` |
| `league.name` | str | 联赛名称 | |
| `league.tier` | str | 联赛等级 | |
| `league.region` | int | 地区 | |
| `league.url` | str | 联赛链接 | |
| `league.description` | str | 描述 | |
| `league.notes` | str | 备注 | |
| `league.start_timestamp` | int | 开始时间 | |
| `league.end_timestamp` | int | 结束时间 | |

---

## 11. 增量字段

GSI 提供增量数据以减少传输量。

### previously - 上一帧的值

当某字段**发生变化**时，`previously` 中会包含该字段的**旧值**。

```json
"previously": {
  "map": {
    "clock_time": -36,
    "game_state": "DOTA_GAMERULES_STATE_HERO_SELECTION"
  },
  "hero": {
    "id": 0
  }
}
```

### added - 本帧新增的字段

当某字段**首次出现**时，`added` 中会标记为 `true`。

```json
"added": {
  "hero": {
    "facet": true,
    "name": true
  }
}
```

---

## 12. 其他模块（通常为空）

| 模块 | 说明 | 触发条件 |
|------|------|----------|
| `events` | 事件列表（击杀、购买等） | 特定事件发生时 |
| `roshan` | 肉山状态 | 需要订阅 |
| `couriers` | 信使状态 | 有信使时 |
| `neutralitems` | 中立物品掉落 | 掉落时 |
| `draft` | BP 选人信息 | 选人阶段 |

---

## 坐标系说明

Dota 2 地图坐标：
- 原点 `(0, 0)` 大约在地图中心
- X 轴：正方向向右（夜魇方向）
- Y 轴：正方向向上（夜魇方向）
- 天辉基地约 `(-7000, -7000)`
- 夜魇基地约 `(7000, 7000)`
- 地图范围约 `-8000` 到 `8000`
