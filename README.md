# 图片生成

> **要出图、要按图改图，用它。**
> 2 大模型系列 · 7 个模型 · 3 条生成入口 · 零第三方依赖（Python 标准库）

按文字描述生成图片，或基于已有图片改图；支持指定参考图、宽高比与清晰度档位。
凭证由用户在本地页面录入，技能本身**不内置任何密钥**。

```python
import sys, os
sys.path.insert(0, os.path.join("<技能目录>", "scripts"))
from gpt_image import GPTImageClient

GPTImageClient().generate("雪原上的橘色列车，水彩风格", size="16:9")
# -> ['https://.../xxx.png']
```

**本文档 = 仓库首页**（给 GitHub 读者）。[`SKILL.md`](./SKILL.md) 是同一套结构与事实的 agent / WorkBuddy 版。

**目录**：[1 作用](#1-作用) · [2 最高原则](#2-最高原则) · [3 架构](#3-架构) · [4 模型系列](#4-模型系列) · [5 凭证层](#5-凭证层) · [6 入口与参数](#6-入口与参数) · [7 配置](#7-配置) · [8 输出与日志](#8-输出与日志) · [9 已知边界](#9-已知边界) · [10 许可](#10-许可)

| 项目 | 内容 |
| --- | --- |
| 标识名 | `image-generation`（kebab-case，用于导入与发布） |
| 名称 | 图片生成 |
| 版本 | 1.0.2 |
| 日期 | 2026-10-12 |
| 作者 | 木小匣 |
| 许可 | MIT |
| 更新地址 | https://github.com/18875216268/image-generation |
| 依赖 | Python 3.10+（仅标准库） |

---

## 1. 作用

把"给一段描述 → 拿到图片"、"给一张图 + 改法 → 拿到改后图片"这两件事，收敛成两个客户端类上的三个方法。

它不替你做审美决定，只负责：选对模型系列、传对参数、没凭证时把页面开给你、拿到图片后如实交回 URL。

## 2. 最高原则

1. **只走客户端**：一律经 `scripts/` 下的客户端方法发起，不直连生图服务端。
2. **不内置密钥**：无凭证时调起本地凭证页由你录入，不臆造、不旁路。
3. **零成本鉴权**：凭证探测只做一次轻量鉴权请求，绝不为验证而提交真实生图任务。
4. **不过度验证**：同一进程内，同一个 Key 只探测一次。
5. **不臆造参数**：你没提的比例与清晰度不填；提了也要看模型是否支持该档位。
6. **如实报告**：失败就说明原因，不假装成功、不编造 URL。

## 3. 架构

### 3.1 目录构造

```
图片生成/
├── SKILL.md             # 主入口（agent / WorkBuddy 版）
├── README.md            # 本文档（仓库首页）
├── manifest.json        # 技能清单：分层 / 出网域 / 写入范围
├── LICENSE              # MIT
├── config.ini           # 默认值与凭证落盘
├── routes/              # 意图路由（routes.json 事实源 → ROUTES.md 渲染）
├── models/              # 模型系列文档（一模型系列一文档，适配两级目录约束）
├── scripts/             # 客户端层（公共底座 + 两个系列客户端 + 凭证层）
├── assets/              # 凭证页与静态资源
└── tests/               # 离线测试
```

### 3.2 核心分层

| 层 | 职责 | 关键文件 |
| --- | --- | --- |
| 意图路由 | 意图 → 客户端 + 方法 + 参数 | `routes/routes.json`、`routes/ROUTES.md` |
| 模型文档 | 模型清单、档位、接口契约、注意事项 | `models/<系列>.md` |
| 客户端层 | 鉴权、提交、轮询、完成判定、提取 URL | `scripts/base.py`、`gpt_image.py`、`nano_banana.py` |
| 凭证层 | 有效性探测、本地服务、凭证页、落盘 | `scripts/credential.py`、`assets/auth.html` |
| 测试层 | 离线校验默认值 / 零密钥 / 路由同步 / 文档一致 | `tests/` |

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

> 模型可用性会动态变化；你的 Key 需已开通目标系列权限，否则服务端会返回「API Key 不允许使用该模型」。

## 5. 凭证层

- 每次生图前自动探测当前 Key 是否被服务端接受：**零成本**，不触发真实生图。
- 有效 → 直接使用。
- 无 Key 或无效 → 自动启动本地服务（仅 `127.0.0.1`）并打开凭证页，你在页面里粘贴 Key。
- 校验通过 → 写入 `config.ini`，页面显示成功并尝试自行关闭（被浏览器拦截时手动关闭即可），随后继续生图。
- 密钥只在你的机器与生图服务端之间流动，不经过任何第三方。
- 等待上限默认 900 秒；超时未录入会抛异常，不会无限等待。

## 6. 入口与参数

### 6.1 意图路由

完整路由表见 [`routes/ROUTES.md`](./routes/ROUTES.md)。摘要：

| 意图 | 调用 |
| --- | --- |
| 只给文字描述 | `GPTImageClient.generate(prompt=...)` |
| 给了图要改 | `GPTImageClient.generate(prompt=..., image=...)` |
| 指定 nano-banana（OpenAI 风格） | `NanoBananaClient.generate(prompt=...)` |
| 指定 nano-banana（按宽高比构图） | `NanoBananaClient.generate_gemini(prompt=..., aspect_ratio=...)` |
| 无 Key / Key 无效 | 自动调起凭证页 |

### 6.2 常见需求 → 调用

| 需求 | 调用 |
| --- | --- |
| 画一只戴头盔的橘猫 | `GPTImageClient().generate("一只戴头盔的橘猫")` |
| 横屏壁纸 | `...generate("...", size="16:9")` |
| 手机壁纸 | `...generate("...", size="9:16")` |
| 要 4K 高清 | `...generate("...", model="gpt-image-2-vip", image_size="4K")` |
| 照这张图改成水彩风 | `...generate("改成水彩风", image="C:/tmp/cat.png")` |
| 用 nano-banana 出 16:9 | `NanoBananaClient().generate_gemini("...", aspect_ratio="16:9")` |

### 6.3 调用方式

```python
import sys, os
sys.path.insert(0, os.path.join("<技能目录>", "scripts"))
from gpt_image import GPTImageClient
from nano_banana import NanoBananaClient

g = GPTImageClient()
g.generate("一只戴头盔的橘猫", size="16:9")
g.generate("改成水彩风", image="C:/tmp/cat.png")     # 图生图（编辑）

n = NanoBananaClient()
n.generate("赛博朋克城市夜景", size="1:1", image_size="2K")
n.generate_gemini("水彩山水", aspect_ratio="16:9", image_size="4K")
```

### 6.4 参数选取

比例、清晰度、参考图都按你的描述推断：说"横屏壁纸"就 `16:9`，说"手机壁纸"就 `9:16`，说"照这张图改"就传 `image`。
你没提的比例与清晰度不会乱填。

### 6.5 失败时

- 权限类：服务端会明确返回「API Key 不允许使用该模型」——换 Key 或换模型即可。
- 瞬时失败（`generate failed` / `The model load is too high`）：重新提交即可，不是参数错误。
- 凭证超时未录入：抛异常说明原因，不静默重试、不猜测 Key。

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

- 成功：返回图片 URL 列表（默认）或完整响应 dict。
- 凭证阶段：控制台打印 `[图片生成] …`（凭证页地址 / 手动访问地址 / 超时原因）。
- 失败：抛异常并附上服务端返回的原始错误信息。

## 9. 已知边界

- Key 需已开通目标模型系列权限，未开通会在提交时被拒绝。
- 模型可用性动态变化，`nano-banana` 可能临时停用。
- `n` 实际只返回 1 张图。
- 凭证页自动关闭依赖浏览器策略，被拦截时停在成功态，手动关闭即可（不影响后续生图）。

## 10. 许可

MIT，见 [`LICENSE`](./LICENSE)。作者：木小匣。
