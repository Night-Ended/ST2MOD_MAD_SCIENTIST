# Seedream 4.0 生图工具

`tools/seedream.py` —— 火山方舟（Ark）Seedream 4.0 的命令行封装，纯标准库 + Pillow，不依赖第三方包。
文生图、图生图、多参考图、一次出 8 张相关图、批量任务都支持，别的项目也能直接用。

- 接口：`POST https://ark.cn-beijing.volces.com/api/v3/images/generations`
- 默认模型：`doubao-seedream-4-0-250828`
- 参考：[Ark 图片生成 API](https://ark.volcengine.com/region:cn-beijing/docs/image-generation-api)

## 1. 先配置 API Key（需要你操作）

1. 打开火山引擎控制台 → 方舟（Ark）→ API Key 管理，创建一个 Key；
   如果 Seedream 4.0 没开通，在“模型广场”开通，或创建一个推理接入点（接入点的 id 是 `ep-...`）。
2. 在终端运行（输入不回显，Key 存在 `%USERPROFILE%\.dsh\secrets\ark_api_key`，不在仓库里）：

```powershell
python D:\DSH_work\StS2_MadScientist\tools\seedream.py --set-key
```

也可以用环境变量 `ARK_API_KEY`，或者 `--key-file` 指定文件。

## 2. 基本用法

```powershell
# 文生图
python tools/seedream.py "一只穿白大褂的蜥蜴科学家，全身，白色背景" --size 2K

# 图生图 / 多参考图（本地图片自动转 data URI 并压缩到长边 1536）
python tools/seedream.py "保持角色设计，改成待机姿势" `
  --ref art/incoming/base/base.png --ref docs/ai_ref/character_ref.png --size 2K

# 一次出 4 张相关图（Seedream 4.0 的 sequential 生成）
python tools/seedream.py "同一角色的 4 个表情" -n 4 --size 2K
```

输出：`<out>/<name>.png` + 同名 `.json`（prompt、参考图、耗时、用量）。默认 `--out seedream_out`。

## 3. 批量

```powershell
python tools/seedream.py --batch art/prompts/01_base.json --out art/incoming/base --dry-run   # 先看请求
python tools/seedream.py --batch art/prompts/01_base.json --out art/incoming/base
```

批量文件格式（路径相对 JSON 所在目录解析）：

```json
{
  "defaults": {"model": "doubao-seedream-4-0-250828", "size": "2K", "refs": ["../ref.png"]},
  "jobs": [
    {"name": "base", "prompt": "...", "size": "2K", "n": 1},
    {"name": "alt",  "prompt": "...", "refs": ["other.png"]}
  ]
}
```

本项目的两个批量：

| 文件 | 内容 | 输出 |
|---|---|---|
| `art/prompts/01_base.json` | 全身基准图、立绘、头像、选择背景 | `art/incoming/base/` |
| `art/prompts/02_frames.json` | 8 帧（待机 3 / 攻击 3 / 受击 2），参考 `../incoming/base/base.png` | `art/incoming/frames/` |

先跑 01，挑一张满意的存成 `art/incoming/base/base.png`，再跑 02。

## 4. 参数备忘

- `--size`：`1K` / `2K` / `4K`，或 `1920x1080` 这种显式尺寸（宽高必须是 16 的倍数，
  显式模式总像素 1280×720 ~ 4096×4096）。Seedream 4.0 支持 1K/2K/4K。
- `--n`：1-15，>1 时自动加 `sequential_image_generation=auto`。
- 参考图最多 14 张；参考图 + 生成图总数不超过 15。
- `--watermark` 默认关闭（正式素材不加水印）。
- 返回的 URL 只有 24 小时有效，工具默认用 `b64_json` 直接落盘，不存 URL。
- 4.0 不支持 `output_format` 参数，输出是 JPEG，工具会转成 PNG。

## 5. 常见错误

| 报错 | 原因 |
|---|---|
| `HTTP 401 ... API key format is incorrect` | Key 错了或没生效，重新 `--set-key` |
| `HTTP 403 ...` | 模型没开通 / 没权限，去控制台开通 Seedream 4.0 |
| `HTTP 400 ... InvalidParameter` | 尺寸不合法（宽高不是 16 的倍数、总像素越界）或参数组合不支持 |
| `HTTP 429` | 限流，工具会自动重试 2 次，仍失败就等一会 |
| 生成很慢 | 2K 一般十几秒；超时可调 `--timeout 300` |

## 6. 安全

- Key 存在用户目录，不进仓库；`--dry-run` 不会发送请求，也不会读取 Key。
- 不要把 Key 写进 prompt、日志或聊天记录。
