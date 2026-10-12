# 意图路由（由 routes/routes.json 渲染）

> 本文件与 `routes.json` 同源：`routes.json` 是**唯一事实源**，改动后需同步本表（同步性由 `tests/test_routes_sync.py` 校验）。
> 这里只讲「什么意图 → 用哪个客户端的哪个方法、传什么参数」；模型清单、清晰度档位与接口契约见 `models/<系列>.md`。

## 默认取值

| 项 | 默认值 | 来源 |
| --- | --- | --- |
| 客户端 | `gpt_image.GPTImageClient` | `routes.json` defaults |
| 方法 | `generate` | `routes.json` defaults |
| 模型 | `gpt-image-2` | `config.ini [gpt_image] default_model` |
| 比例 | `1:1` | `config.ini` default_size |
| 数量 | `1` | `config.ini` n |
| 清晰度 | 不设 | 由用户描述推断，不臆造 |
| Gemini 比例 | 不设 | 由用户描述推断，不臆造 |

## 路由表

| 意图 | 触发条件 | 客户端 / 方法 | 关键参数 | 说明 |
| --- | --- | --- | --- | --- |
| `text_to_image` | 用户只给文字描述，未给参考图 | `gpt_image.GPTImageClient.generate` | prompt(必填) / size / image_size | 文生图：默认走 gpt-image 系列 |
| `image_to_image` | 用户提供图片并要求照图修改 / 参考这张图 | `gpt_image.GPTImageClient.generate` | prompt(必填) / image(必填) | 图生图（编辑）：仅多传 image，其余同文生图 |
| `nano_openai_style` | 明确要使用 nano-banana 系列，且沿用 OpenAI 风格参数 | `nano_banana.NanoBananaClient.generate` | prompt / size / image_size / image | nano-banana 的 OpenAI 兼容入口（与 gpt-image 同路径，仅模型取值不同） |
| `nano_gemini_style` | 使用 nano-banana 系列且以宽高比（aspect_ratio）表达构图 | `nano_banana.NanoBananaClient.generate_gemini` | prompt(必填) / aspect_ratio / image_size | Gemini 兼容入口：比例走 aspectRatio |
| `no_credential` | 无可用 Key，或 Key 校验不通过 | `credential.ensure_valid_key`（自动调起） | credential_timeout（默认 900 秒） | 凭证层：启本地服务 + 凭证页录入 → 校验通过落盘 config.ini → 继续生图 |

## 红线

- 生图只能经 scripts/ 下的客户端方法发起，禁止用 requests / urllib / curl 直连生图服务端
- 禁止阅读 models/ 下的接口文档后自行拼装 URL / Header / JSON 请求体
- 禁止自行实现「提交 → 轮询 → 完成判定」流程（客户端已封装）
- 禁止手动构造 Authorization 鉴权请求；Key 由 ensure_valid_key 自动探测与补全
- 技能不内置任何密钥；无 Key 时必须走凭证页由用户录入
- 用户未提及的比例与清晰度不得臆造；清晰度须该模型支持该档位
- 鉴权探测为零成本，不触发真实生图
