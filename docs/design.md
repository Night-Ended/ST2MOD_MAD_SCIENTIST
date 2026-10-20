# 疯狂科学家 —— 设计笔记与扩展指南

> 状态：v0.1.0 只有角色框架。卡牌 / 遗物设计由你提供后按本文的约定逐个实现。

## 1. 角色定位（提案，待确认）

原型是原版第三层事件 **Tinker Time** 里那位在尸体海里捡零件的疯狂科学家：
背着一整个实验室的破烂，护目镜发光，随身带着不知名的绿色试剂。
她不是战士，而是**把卡牌、药水和自己当成实验材料**的工程师。

建议的机制主轴（等你拍板）：

| 关键词 | 含义 | 玩法方向 |
|---|---|---|
| 实验 / Experiment | 给一张卡挂上持续效果，回合结束结算 | 养大哥、延迟收益 |
| 试剂 / Reagent | 消耗型资源（类似能量但用于强化） | 资源管理 |
| 过载 / Overload | 本回合额外能量，回合结束受反噬 | 爆发换血量 |

数值基准：70 血、3 能量、5 张打击 + 5 张防御（正式初始牌组待设计）。
初始遗物暂用「燃烧之血」占位。

## 2. 资源规格（照这个尺寸做图）

| 用途 | 路径 | 尺寸 |
|---|---|---|
| 战斗形象（静态） | `images/character/combat.png` | 426×560（透明底） |
| 角色选择立绘 | `images/charui/char_select_mad_scientist.png` | 132×195（透明底） |
| 未解锁剪影 | `images/charui/char_select_mad_scientist_locked.png` | 132×195（黑色剪影） |
| 顶栏头像 | `images/charui/character_icon_mad_scientist.png` | 88×88 |
| 头像描边 | `images/charui/character_icon_mad_scientist_outline.png` | 88×88（白色剪影） |
| 地图标记 | `images/charui/map_marker_mad_scientist.png` | 49×64 |
| 卡面小图 | `images/card_portraits/<卡id>.png` | 250×190 |
| 卡面大图 | `images/card_portraits/big/<卡id>.png` | 1000×760（全画 606×852） |
| 能力图标 | `images/powers/<能力id>.png` | 64×64 左右（模板里是 94×94） |
| 遗物图标 | `images/relics/<遗物id>.png` | 94×94 |
| 遗物大图 | `images/relics/big/<遗物id>.png` | 256×256 左右 |
| 药水 | `images/potions/<药水id>.png` | 256×256 |

`<卡id>` 等 = 类名去掉 Mod 前缀后的小写，例如类 `ReagentFlask` → `reagent_flask.png`。

## 3. 新增一张卡

1. 在 `MadScientistCode/Cards/` 新建 `ReagentFlask.cs`，继承 `MadScientistCard`：

```csharp
using MadScientist.MadScientistCode.Cards;
using MegaCrit.Sts2.Core.Entities.Cards;
using MegaCrit.Sts2.Core.GameActions.Multiplayer;

public class ReagentFlask : MadScientistCard
{
    public ReagentFlask() : base(1, CardType.Skill, CardRarity.Common, TargetType.Self) { }

    protected override async Task OnPlay(PlayerChoiceContext choiceContext, CardPlay cardPlay)
    {
        // 具体效果：参考原版卡（Decompile 工具：D:\DSH_work\tools\ilspy\ilspycmd.exe）
    }

    protected override void OnUpgrade()
    {
        // 升级效果
    }
}
```

2. 在 `MadScientist/localization/{eng,zhs}/cards.json` 加两条 key（前缀是 `MADSCIENTIST-`）：

```json
"MADSCIENTIST-REAGENT_FLASK.title": "Reagent Flask",
"MADSCIENTIST-REAGENT_FLASK.description": "Gain [blue]3[/blue] Block."
```

3. 放卡图 `images/card_portraits/reagent_flask.png` 和 `big/reagent_flask.png`。
4. `dotnet build -c Release`（会自动重打 pck、复制到游戏）。

> 卡牌会自动进 `MadScientistCardPool`（基类上的 `[Pool]` 特性负责）。

## 4. 新增遗物 / 能力 / 药水

同样的套路：继承 `MadScientistRelic` / `MadScientistPower` / `MadScientistPotion`，
key 放对应 json（`relics.json` / `powers.json`），图片按上表命名。

- 遗物：`relics.json` 需要 `title` / `description` / `flavor`。
- 能力：`powers.json` 需要 `title` / `description` / `smartDescription`。
- 药水：`potions.json` 需要 `title` / `description`。

## 5. 已知限制 / 后续

| 项 | 现状 | 要做的事 |
|---|---|---|
| 战斗形象 | 一张静态 PNG（`NodeFactory.CreateFromResource`） | 想要待机/攻击动作：用 Spine 做骨骼，或手写 `.tscn` + AnimationPlayer |
| 休息处 / 商人立绘 | 沿用铁甲战士的 | 需要一个 `.tscn`，当前打包器不支持，需引入 MegaDot |
| 能量计数器 | 沿用铁甲战士的 | 同上（或写代码用 `CustomEnergyCounter`） |
| 角色选择背景 | 铁甲战士的熔炉背景 | 需要 `char_select_bg_mad_scientist.tscn`，需 MegaDot |
| 初始牌组/遗物 | 打击、防御、燃烧之血 | 等设计 |
| 卡池 | 空（打完一局不会掉本家卡） | 等卡牌设计 |

> 如果之后要补 `.tscn`：从 https://megadot.megacrit.com/ 下 4.5.1-m.4 Windows csharp 编辑器（约 577 MB），
> 把 `Directory.Build.props` 里的 `<GodotPath>` 指过去，然后把 csproj 里的 PckPacker 换成
> `dotnet publish` 走 Godot 导出即可。

## 6. 调试小抄

- 游戏日志：`%APPDATA%\SlayTheSpire2\logs\godot.log`；每次启动都会写一行 `[MadScientist] [Diag] OK ...`。
- 反编译查 API：`D:\DSH_work\tools\ilspy\ilspycmd.exe -t 完整类名 "D:\steam\steamapps\common\Slay the Spire 2\data_sts2_windows_x86_64\sts2.dll"`。
- 原版 pck 解包工具：`D:\DSH_work\sts2_tools\`（`pcklist.py` 列目录、`extract.py` 按路径关键字导出）。
- BaseLib 源码：`D:\DSH_work\ref\baselib_src\`（已反编译，查 `CustomCharacterModel` 等）。
