# 疯狂科学家 AI 重绘素材包（给生成方用）

> 目标：把现在的“裁切图”换成 AI 重绘的**人设图 + 全身角色图 + 立绘 + 小头像**，
> 风格贴近原版角色（厚描边、手绘平涂、暗色调 + 暖色轮廓光）。
> 动画不做逐帧，而是用同一张全身图做位移/旋转/拉伸压缩。
>
> 参考图（随本文件一起给模型）：
> - `character_ref.png` —— 原版 Tinker Time 事件里的角色原图（构图/服装/配色依据）
> - `style_board.png` —— 原版 5 个角色的选择立绘（风格依据）
> - `palette.png` —— 从角色身上提取的主色

---

## 1. 需要的产出

### A. 人设图（1 张）

- 2.5K 左右横图：正面 / 3/4 侧 / 侧面三个视角 + 头部特写 + 扳手、试瓶等道具
- 用来定稿设计，也方便以后画卡图、做宣传图
- 纯白背景，不要文字标注

### A2. 全身角色图（1 张，最重要）

- 透明背景 PNG（或纯白背景，我来抠），约 **1024×1536**
- **全身**、**脚在画面底部**、**3/4 侧身朝右**（和原版角色一致）
- 姿势：站立，右手（画面右侧那只）抬起/握拳，左手拿扳手，双脚分开
- 这张图是游戏里唯一的战斗贴图，所有动作都靠它形变，所以要挑最满意的一张

### B. 动画：不做逐帧，用单张全身图做形变

待机 / 攻击 / 受击都由**同一张全身图**通过位移、旋转、拉伸压缩、闪白/闪红完成（代码里已经实现）。
所以全身图只需要一个干净的**中性站姿**：

- 双脚可见、踩在同一条水平线上
- 3/4 侧身朝右，手臂不要和身体重叠太多（方便做前倾/后仰）
- 不要动态模糊、不要动作残影

### C. 角色选择立绘（1 张）

- 头 + 肩胸，**132×195 的比例**（出 528×780 再缩）
- 和 A 同一张脸、同一光照，眼神看向画面右前方
- 透明背景

### D. 顶栏小头像（1 张）

- 头部特写（护目镜 + 半张脸），正方形，出 352×352
- 透明背景，缩到 88×88 时仍然认得出是护目镜 + 彩色头发

### E. （可选）角色选择背景 1920×1080

- 如果想让背景也换成 AI 图：暗色洞穴实验室，中间留空给立绘，不要出现人物

---

## 2. 推荐工具（按顺手程度）

| 工具 | 适合做什么 | 说明 |
|---|---|---|
| **即梦 AI（Seedream 4.0）** | A / C / D / E，以及 8 帧表 | 国内可直接用，参考图一致性好，中文提示词就行，自带抠图 |
| **可灵（Kling）图生视频** | 用 A 生成 5 秒待机/攻击视频，再抽 8 帧 | 动作连贯，但风格会轻微漂移，抽帧后我来修 |
| **LiblibAI / ComfyUI + SDXL（Illustrious 系）** | 可控性最高 | 需要 ControlNet(OpenPose) + IP-Adapter 锁角色，门槛高但最稳 |
| **Gemini 2.5 Flash Image（Nano Banana）** | A / C / D 和逐帧编辑 | 改图一致性最强，但需要能访问；输出没有透明通道，抠图我来做 |
| Midjourney v7 | 只适合出概念图 | `--cref` 角色参考 + `--sref` 风格参考，但很难出干净的 8 帧表 |

**最省事的路线（推荐）**
1. 即梦 / Nano Banana：用 `character_ref.png` + `style_board.png` 出 **A（全身基准图）**，反复抽到满意；
2. 用 A 作为参考图，逐帧改姿势出 8 张（每张都带上 A，提示词只改动作）；
3. 或者跳过 2，用可灵把 A 做成 5 秒循环视频，我抽 8 帧。

> 不建议让模型“一次画 8 帧”：跨帧一致性是当前图像模型的弱项。逐帧编辑或视频抽帧更稳。

---

## 3. 提示词

### 通用风格前缀（所有图都加）

```
Slay the Spire 2 official character art style, hand-painted 2D game illustration,
thick dark ink outlines, painterly flat shading with soft gradients, muted earthy palette,
warm rim light from the upper right, slightly grotesque stylized proportions,
clean readable silhouette, high contrast, no text, no watermark, no border,
full body, feet visible, three-quarter view facing right, plain white background
```

中文版：
```
《杀戮尖塔2》官方角色原画风格，手绘2D插画，粗黑描边，平涂+柔和渐变，
低饱和土色调，右上暖色轮廓光，略微怪诞的卡通比例，剪影清晰，高对比，
不要文字/水印/边框，全身，脚在画面内，3/4侧身朝右，纯白背景
```

### A. 全身基准图

```
<风格前缀>
A female lizard-like mad scientist (kobold), orange-brown scaled skin, strong muscular arms,
wild curly hair made of overlapping gear-shaped petals (teal, magenta, yellow, blue),
large brass goggles with glowing yellow lenses pushed up on her forehead, wide toothy grin,
white lab coat over a grey shirt, leather belt with pouches and a wrench,
oversized scavenger backpack with rubber hoses and a glowing green potion flask,
standing in a relaxed combat stance, right arm raised, left hand holding a wrench,
full body, feet on the ground, facing right
```

### B. 8 帧动作表（4×2）

```
<风格前缀>
Character animation sprite sheet, 4 columns x 2 rows, 8 frames, exactly the same character
in every frame, same camera angle, same scale, same lighting, feet on the same baseline,
full body in every cell, evenly spaced grid, plain white background, no text, no frame borders.
Row 1 (idle): frame1 standing exhale, frame2 standing inhale (chest slightly up),
frame3 back to frame1, frame4 attack windup leaning back with arm pulled back.
Row 2 (attack + hurt): frame5 lunge forward striking with the wrench,
frame6 recovering to mid stance, frame7 hurt flinch leaning back,
frame8 recovering to standing.
```

如果模型画不好整张表，就逐帧出（每帧都附上 A 作为参考图），提示词只替换动作那句：

- `idle frame: standing, exhaling, shoulders slightly down`
- `idle frame: standing, inhaling, chest slightly lifted`
- `attack windup: leaning back, wrench arm pulled back`
- `attack strike: lunging forward, body tilted forward, wrench swinging`
- `attack recover: back to mid stance, slightly forward`
- `hurt: flinching backwards, head tilted back, eyes squeezed`
- `hurt recover: returning to standing`

### C. 角色选择立绘

```
<风格前缀>
Head and shoulders bust portrait of the same lizard mad scientist,
large brass goggles with glowing yellow lenses, colorful gear-petal hair,
white lab coat collar, wide toothy grin, looking to the right,
dark cave background removed, transparent background
```

### D. 顶栏小头像

```
<风格前缀>
Square head icon of the same lizard mad scientist, close-up of the face and goggles,
colorful gear-petal hair, glowing yellow goggle lenses, high contrast, readable at 88x88,
transparent background
```

### 负面提示词

```
different character, changed outfit, extra arms, extra fingers, deformed hands,
cropped feet, inconsistent scale, different camera angle, multiple characters,
text, watermark, signature, frame borders, grid lines, drop shadow,
3D render, photorealistic, blurry, low contrast, oversaturated
```

### 参数建议

- 参考图权重：角色参考 0.7~0.85，风格参考 0.5~0.7
- 画面比例：A 用 2:3，C 用 2:3，D 用 1:1，B 用 4:3
- 一次多抽几张，挑“脚完整、手没崩、护目镜对”的那张

---

## 4. 交付给我时的格式

- 原图不要压缩，PNG
- 8 帧表：统一格子，别加格线/序号（要加就加在最外侧空白处）
- 命名：`base.png`、`sheet.png`（或 `frame01.png`…`frame08.png`）、`portrait.png`、`icon.png`、`bg.png`
- 放在 `D:\DSH_work\StS2_MadScientist\art\incoming\` 即可

我拿到后会做：抠图/去白边、脚底基线对齐、逐帧统一尺寸与调色、补描边、
打包进 pck、把 8 帧接进现在的动画系统（待机循环 + 攻击/受击各播一次），
以及修掉角色选择背景黑屏的问题。
