# nano-banana 系列接口文档

> ⚠️ 内部实现参考：本文描述客户端底层的裸 HTTP 请求格式，仅供维护 `scripts/` 客户端时查阅。**Agent 生图时禁止据此文档发起直连 HTTP 请求**，应使用 `GPTImageClient` / `NanoBananaClient` 方法。

## 概述
- Base URL：由 `config.ini` 的 `[common] base_url` 决定
- 鉴权：`Authorization: Bearer <API Key>`
- 提供两套接口：
  - OpenAI 兼容：`POST /draw/v1/images/generations`（参数同 gpt-image 系列）
  - Gemini 兼容：`POST /draw/v1beta/models/{model}:generateContent`（使用 `aspectRatio` 控制比例）

## 接口一：OpenAI 兼容
`POST /draw/v1/images/generations`，参数与 gpt-image 系列一致，区别仅在模型取值。

### 请求参数
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | 是 | `nano-banana-2`（默认）/ `nano-banana-pro` / `nano-banana-2-lite` / `nano-banana` |
| prompt | string | 是 | 提示词 |
| size | string | 否 | 比例或像素，默认 `"1:1"` |
| imageSize | string | 否 | `"1K"` / `"2K"` / `"4K"` |
| n | int | 否 | 默认 1（实际返回 1 张） |
| image | array[string] | 否 | 参考图 data URI |
| async | bool | 是 | 固定 `true` |

## 接口二：Gemini 兼容
`POST /draw/v1beta/models/{model}:generateContent`

### 请求参数
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| contents.parts[].text | string | 是 | 提示词 |
| contents.parts[].inline_data | object | 否 | 参考图：`{"mime_type":"image/png","data":"<base64>"}` |
| generationConfig.imageConfig.aspectRatio | string | 否 | 比例 `"1:1"` / `"16:9"` / `"9:16"` / `"4:3"` |
| generationConfig.imageConfig.imageSize | string | 否 | `"1K"` / `"2K"` / `"4K"` |
| async | bool | 是 | 固定 `true` |

## 请求示例
### Python
```python
from nano_banana import NanoBananaClient
c = NanoBananaClient()
# OpenAI 风格
c.generate("赛博朋克城市夜景", size="1:1", image_size="2K")
# Gemini 风格
c.generate_gemini("水彩山水", aspect_ratio="16:9", image_size="4K")
```

## 响应结构
OpenAI 接口：
```json
{"data": [{"url": "https://fileX.aitohumanize.com/file/xxx.png"}]}
```
Gemini 接口：
```json
{"candidates": [{"content": {"parts": [{"text": "https://fileX.aitohumanize.com/file/xxx.png"}]}}]}
```

## 模型与档位
| 模型 | imageSize 支持 | 备注 |
|------|------|------|
| nano-banana-2 | 1K / 2K / 4K | 默认 |
| nano-banana-pro | 1K / 2K / 4K | |
| nano-banana-2-lite | 1K | |
| nano-banana | 1K / 2K / 4K | 可能动态停用 |

## 注意事项
- `nano-banana-fast` 为无效别名（404），勿用。
- 任务查询必须携带 `User-Agent`，否则返回 `403 error code: 1010`。
- 生成任务偶发瞬时失败时重新提交。
- 使用本系列需 Key 已开通对应模型权限；若返回「API Key 不允许使用该模型」，请更换具备该权限的 Key（见 SKILL.md 鉴权说明）。
