# gpt-image 系列接口文档

> ⚠️ 内部实现参考：本文描述客户端底层的裸 HTTP 请求格式，仅供维护 `scripts/` 客户端时查阅。**Agent 生图时禁止据此文档发起直连 HTTP 请求**，应使用 `GPTImageClient` / `NanoBananaClient` 方法。

## 概述
- Base URL：由 `config.ini` 的 `[common] base_url` 决定
- 鉴权：`Authorization: Bearer <API Key>`
- 接口：`POST /draw/v1/images/generations`（OpenAI 兼容）
- 异步流程：提交请求获得 `task_id` → 轮询 `GET /v1/tasks/{task_id}` → 响应出现 `data` 即完成。

## 请求参数
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | 是 | `gpt-image-2`（默认）/ `gpt-image-2-vip` / `gpt-image-2.5` |
| prompt | string | 是 | 提示词 |
| size | string | 否 | 比例或像素，如 `"1:1"` / `"16:9"` / `"1024x1024"`，默认 `"1:1"` |
| imageSize | string | 否 | 清晰度档位 `"1K"` / `"2K"` / `"4K"` |
| n | int | 否 | 生成数量，默认 1（实际返回 1 张） |
| image | array[string] | 否 | 参考图，元素为 `data:image/png;base64,...` |
| async | bool | 是 | 固定 `true` |

## 参考图
`image` 为 base64 data URI 数组。客户端 `generate(image=...)` 接受本地路径 / bytes / 纯 base64，自动转换为 data URI。

## 请求示例
### Python
```python
from gpt_image import GPTImageClient
c = GPTImageClient()
url = c.generate("一只戴头盔的橘猫", size="1:1", image_size="1K")
```

## 响应结构
提交成功：
```json
{"task_id": "task_xxx"}
```
轮询完成：
```json
{"created": 1234567890, "data": [{"url": "https://fileX.aitohumanize.com/file/xxx.png"}]}
```

## 模型与档位
| 模型 | imageSize 支持 |
|------|------|
| gpt-image-2 | 1K |
| gpt-image-2-vip | 1K / 2K / 4K |
| gpt-image-2.5 | 1K / 2K / 4K |

## 注意事项
- 任务查询必须携带 `User-Agent`，否则返回 `403 error code: 1010`。
- `n` 实际仅返回 1 张图。
- 生成任务偶发瞬时失败时重新提交。
