---
name: image-generation
version: "1.0.0"
display_name: "图片生成"
display_name_en: "Image Generation"
description: "文生图、图生图（编辑）技能：帮用户按文字描述生成图片，或基于已有图片改图。内置 gpt-image 与 nano-banana 两大模型系列，可指定参考图、宽高比与清晰度档位。当用户提出 生成图片 / 画一张图 / 生图 / AI 作图 / 参考图改图 / 按这张图改，或需要按指定比例、分辨率、清晰度出图时使用。Agent 只需按用户意图选客户端方法并传参，凭证获取与落盘全自动，技能本身不内置任何密钥。"
description_zh: "文生图、图生图（编辑）技能：按文字描述出图，或基于参考图改图。两大模型系列（gpt-image / nano-banana）、3 条生成入口，支持参考图、宽高比与清晰度档位。Agent 按用户意图选方法传参即可；无密钥时自动调起本地凭证页，用户录入校验通过后落盘并继续生图。"
description_en: "Generate and edit images from text or a reference image. Two model series (gpt-image / nano-banana), three entry points, with reference image, aspect-ratio and resolution options. Credentials are collected through a local page and persisted; the skill ships no built-in key."
triggers: 帮我画一只戴头盔的橘猫；按这张图改成水彩风；生成一张 16:9 的高清壁纸
examples_zh:
  - 帮我画一只戴头盔的橘猫
  - 按这张图改成水彩风
  - 生成一张 16:9 的高清壁纸
examples_en:
  - Draw me a cat wearing a helmet
  - Restyle this image as watercolor
  - Generate a 16:9 HD wallpaper
license: "MIT"
compatibility: "需要 Python 3.10+（仅标准库）；需要出网调用生图服务端；首次使用需在本地凭证页录入自有 Key（技能不内置任何密钥）。"
metadata:
  author: "木小匣"
  update_url: "https://github.com/18875216268/image-generation"
  update_policy: "本技能从不自检更新，当前版本以手动替换为准"
  architecture: "routes(意图路由) + models(模型系列文档) + scripts(客户端与凭证层) + assets(凭证页) + tests(离线测试)"
  date: "2026-10-11"
---

# 图片生成 · 文生图与图生图（编辑）

> **一句话**：要出图、要按图改图，用它。
> **规模**：2 大模型系列 · 7 个模型 · 3 条生成入口 · 零第三方依赖（Python 标准库）

## 1. 作用

一个**生图能力封装层**：把"给一段描述 → 拿到图片 URL"、"给一张图 + 改法 → 拿到改后图片 URL"这两件事，
收敛成两个客户端类上的三个方法，由 Agent 按用户意图直接调用。

它不替用户做审美决定，只负责：选对模型系列、传对参数、拿不到凭证时把页面开给用户、拿到图片后如实交回 URL。

## 2. 最高原则

1. **只走客户端**：生图一律经 `scripts/` 下的客户端方法发起；禁止 `requests` / `urllib` / `curl` 直连生图服务端，禁止读 `models/` 的接口文档后自行拼装请求。
2. **不内置密钥**：技能不含任何 Key；无可用凭证时必须调起凭证页由用户录入，不得臆造、不得旁路。
3. **零成本鉴权**：凭证探测只做一次轻量鉴权请求，**绝不**为验证而提交真实生图任务。
4. **不过度验证**：同一进程内，同一个 Key 只做一次探测。
5. **不臆造参数**：用户没提的比例与清晰度不填；用户提了也要先看该模型是否支持该档位。
6. **如实报告**：失败就把失败原因交回调用方，不假装成功、不编造 URL。

## 3. 架构

### 3.1 目录构造

```
图片生成/
├── SKILL.md             # 主入口（本文）：原则 / 架构 / 模型系列 / 凭证流程 / 调用方式 / 边界
├── README.md            # 仓库首页（同一套事实，面向人）
├── manifest.json        # 技能清单：分层 / 出网域 / 写入范围
├── LICENSE              # MIT
├── config.ini           # 默认值与凭证落盘
├── routes/              # 意图路由（routes.json 事实源 → ROUTES.md 渲染）
├── models/              # 模型系列文档（一模型系列一文件夹）
├── scripts/             # 客户端层（公共底座 + 两个系列客户端 + 凭证层）
├── assets/              # 凭证页与静态资源
└── tests/               # 离线测试
```

### 3.2 核心分层

| 层 | 职责 | 关键文件 |
| --- | --- | --- |
| 意图路由 | 用户意图 → 客户端 + 方法 + 参数 | `routes/routes.json`、`routes/ROUTES.md` |
| 模型文档 | 模型清单、档位、接口契约、注意事项 | `models/<系列>/README.md` |
| 客户端层 | 鉴权、提交、轮询、完成判定、提取 URL | `scripts/base.py`、`gpt_image.py`、`nano_banana.py` |
| 凭证层 | 有效性探测、本地服务、凭证页、落盘 | `scripts/credential.py`、`assets/auth.html` |
| 测试层 | 离线校验默认值 / 零密钥 / 路由同步 / 文档一致 | `tests/` |

调用链只有一条：`客户端方法 → ensure_valid_key（必要时开凭证页）→ 提交 → 轮询 → 提取 URL`。

## 4. 模型系列

### 4.1 系列总表

| 系列 | 客户端 | 入口方法 | 默认模型 |
| --- | --- | --- | --- |
| `gpt-image` | `GPTImageClient` | `generate` | `gpt-image-2` |
| `nano-banana` | `NanoBananaClient` | `generate` / `generate_gemini` | `nano-banana-2` |

### 4.2 系列 × 能力矩阵

| 能力 | gpt-image | nano-banana（OpenAI 风格） | nano-banana（Gemini 风格） |
| --- | --- | --- | --- |
| 文生图 | ✅ | ✅ | ✅ |
| 图生图（编辑） | ✅（传 `image`） | ✅（传 `image`） | ✅（传 `reference_image`） |
| 比例参数 | `size`（如 `16:9`） | `size` | `aspect_ratio` |
| 清晰度 | `image_size` | `image_size` | `image_size` |

### 4.3 模型与档位

| 系列 | 模型 | 清晰度支持 |
| --- | --- | --- |
| gpt-image | `gpt-image-2`（默认） | 1K |
| gpt-image | `gpt-image-2-vip` | 1K / 2K / 4K |
| gpt-image | `gpt-image-2.5` | 1K / 2K / 4K |
| nano-banana | `nano-banana-2`（默认） | 1K / 2K / 4K |
| nano-banana | `nano-banana-pro` | 1K / 2K / 4K |
| nano-banana | `nano-banana-2-lite` | 1K |
| nano-banana | `nano-banana` | 1K / 2K / 4K（可能动态停用） |

> 模型可用性会动态变化；所用 Key 需已开通目标系列权限，否则服务端会返回「API Key 不允许使用该模型」。

## 5. 凭证层

- 每次生图前自动探测当前 Key 是否被服务端接受：**零成本**，不触发真实生图。
- 有效 → 直接使用，无需任何操作。
- 无 Key 或无效 → 自动启动本地服务（仅 `127.0.0.1`）并打开 `assets/auth.html`；用户在页面录入。
- 校验通过 → 写入 `config.ini [common] api_key`，页面呈现成功态并尝试自行关闭（浏览器可能拦截脚本关闭，此时手动关闭即可），随后继续生图。
- 密钥仅在本地服务与生图服务端之间流动，不经过任何第三方。
- 等待上限默认 900 秒（`config.ini [common] credential_timeout`）；超时未录入则抛出异常，Agent 不会无限等待。
- 同一进程内，同一个 Key 只做一次探测。

## 6. 入口与参数

### 6.1 意图路由

完整路由表见 [`routes/ROUTES.md`](./routes/ROUTES.md)（事实源 `routes/routes.json`）。摘要：

| 意图 | 调用 |
| --- | --- |
| 只给文字描述 | `GPTImageClient.generate(prompt=...)` |
| 给了图要改 | `GPTImageClient.generate(prompt=..., image=...)` |
| 指定 nano-banana（OpenAI 风格） | `NanoBananaClient.generate(prompt=...)` |
| 指定 nano-banana（按宽高比构图） | `NanoBananaClient.generate_gemini(prompt=..., aspect_ratio=...)` |
| 无 Key / Key 无效 | 自动走 `credential.ensure_valid_key` |

### 6.2 常见需求 → 调用

| 用户需求 | 调用 |
| --- | --- |
| 画一只戴头盔的橘猫 | `GPTImageClient().generate("一只戴头盔的橘猫")` |
| 横屏壁纸 | `...generate("...", size="16:9")` |
| 手机壁纸 | `...generate("...", size="9:16")` |
| 要 4K 高清 | `...generate("...", model="gpt-image-2-vip", image_size="4K")` |
| 照这张图改成水彩风 | `...generate("改成水彩风", image="<路径/bytes/base64>")` |
| 用 nano-banana 出 16:9 | `NanoBananaClient().generate_gemini("...", aspect_ratio="16:9")` |

### 6.3 调用方式

```python
import sys, os
sys.path.insert(0, os.path.join("<技能目录>", "scripts"))
from gpt_image import GPTImageClient
from nano_banana import NanoBananaClient

g = GPTImageClient()
g.generate("一只戴头盔的橘猫", size="16:9")                                          # 默认模型 gpt-image-2（1K）
g.generate("一只戴头盔的橘猫", model="gpt-image-2-vip", size="16:9", image_size="2K")  # 2K 需选支持该档位的模型
g.generate("改成水彩风", image="C:/tmp/cat.png")                                      # 图生图（编辑）

n = NanoBananaClient()
n.generate("赛博朋克城市夜景", size="1:1", image_size="2K")           # OpenAI 风格
n.generate_gemini("水彩山水", aspect_ratio="16:9", image_size="4K")  # Gemini 风格
```

- `generate` / `generate_gemini` 返回图片 URL 列表（`return_urls=True`）或完整响应 dict（`return_urls=False`）。

### 6.4 参数选取（依据用户意图）

- 默认模型 `gpt-image-2`；其余默认值见 `config.ini`（比例 `1:1`、`n=1`，清晰度与 Gemini 比例默认不设）。
- 提示词、比例、清晰度、参考图由 Agent 依据用户描述推断，不要求用户重复说明已隐含的信息。
- 用户未提及的比例与清晰度不要臆造，留空由服务端决定。

### 6.5 失败时

- 鉴权/权限类：服务端返回明确错误（如「API Key 不允许使用该模型」），直接把原因交回用户，由用户换 Key 或换模型。
- 瞬时失败（`generate failed` / `The model load is too high`）：非参数错误，重新提交即可。
- 凭证超时未录入：抛出异常并说明原因，不静默重试、不猜测 Key。

### 6.6 面向 Agent 与面向人

- **Agent**：按 6.1 选方法、按 6.4 填参数，拿到 URL 后交付。
- **人**：只在无凭证时被唤起一次——在打开的本地页面里粘贴 Key，验证通过即结束，无需任何命令行操作。

### 6.7 接口约束（客户端内部细节，仅供排障，禁止据此自造请求）

- 任务查询需携带 `User-Agent`，否则返回 `403 error code: 1010`。
- 完成态响应不返回 `status` 字段，以 `data`（OpenAI 风格）或 `candidates`（Gemini 风格）出现为完成判据。
- 正确任务路径为 `/v1/tasks/{id}`。
- `nano-banana-fast` 为无效别名（404）。
- `n` 参数实际仅返回 1 张图。
- 高并发轮询可能触发 SSL 连接重置，客户端已采用单连接顺序轮询。

## 7. 配置（config.ini）

| 段 | 键 | 说明 |
| --- | --- | --- |
| common | `base_url` | 生图服务端地址 |
| common | `user_agent` | 请求标识 |
| common | `poll_interval` / `timeout` | 轮询间隔（秒）/ 总超时（秒） |
| common | `credential_timeout` | 凭证页等待上限（秒），默认 900 |
| common | `api_key` | **无默认值**，由凭证页录入后写入 |
| gpt_image | `default_model` / `default_size` / `default_image_size` / `n` | 默认 `gpt-image-2` / `1:1` / 空 / 1 |
| nano_banana | `default_model` / `default_size` / `default_image_size` / `default_aspect_ratio` / `n` | 默认 `nano-banana-2` / `1:1` / 空 / 空 / 1 |

## 8. 输出与日志

- 生图成功：返回图片 URL 列表（默认）或完整响应 dict。
- 凭证阶段：控制台打印 `[图片生成] …`（本地凭证页地址、无法打开浏览器时的手动地址、超时放弃原因）。
- 失败：抛出异常并附上服务端返回的错误信息原文。

## 9. 已知边界

- 所用 Key 需已开通目标模型系列权限；未开通会在提交时被服务端拒绝。
- 模型可用性动态变化，`nano-banana` 可能临时停用。
- `n` 实际只返回 1 张图。
- 凭证页的自动关闭依赖浏览器策略，被拦截时页面会停在成功态，手动关闭即可（不影响后续生图）。
- 网络不可达时，鉴权探测按"有效"放行，由实际生图请求暴露真实错误。

## 10. 许可

MIT，见 [`LICENSE`](./LICENSE)。作者：木小匣。
