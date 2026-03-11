# Text To Dialogue V3 API Documentation

> Generate content using the Text To Dialogue V3 model

## Overview

This document describes how to use the Text To Dialogue V3 model for content generation. The process consists of two steps:
1. Create a generation task
2. Query task status and results

## Authentication

All API requests require a Bearer Token in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

Get API Key:
1. Visit [API Key Management Page](https://kie.ai/api-key) to get your API Key
2. Add to request header: `Authorization: Bearer YOUR_API_KEY`

---

## 1. Create Generation Task

### API Information
- **URL**: `POST https://api.kie.ai/api/v1/jobs/createTask`
- **Content-Type**: `application/json`

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model | string | Yes | Model name, format: `elevenlabs/text-to-dialogue-v3` |
| input | object | Yes | Input parameters object |
| callBackUrl | string | No | Callback URL for task completion notifications |

### input Object Parameters

#### stability
- **Type**: `number`
- **Required**: No
- **Description**: Determines how stable the voice is and the randomness between each generation.
- **Range**: 0 - 1 (step: 0.5)
- **Default Value**: `0.5`

#### language_code
- **Type**: `string`
- **Required**: No
- **Description**: Language selection
- **Default Value**: `"auto"`
- **Common options**: `auto`, `en` (English), `es` (Spanish), `fr` (French), `de` (German), `zh` (Mandarin Chinese), `pt` (Portuguese), `ar` (Arabic)

### Request Example

```json
{
  "model": "elevenlabs/text-to-dialogue-v3",
  "input": {
    "dialogue": [
      {"text": "Your narration text here", "voice": "Liam"}
    ],
    "stability": 0.5,
    "language_code": "en"
  }
}
```

### Response Example

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "281e5b0*********************f39b9"
  }
}
```

---

## 2. Query Task Status

### API Information
- **URL**: `GET https://api.kie.ai/api/v1/jobs/recordInfo`
- **Parameter**: `taskId` (passed via URL parameter)

### Response Example

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "281e5b0*********************f39b9",
    "model": "elevenlabs/text-to-dialogue-v3",
    "state": "success",
    "resultJson": "{\"resultUrls\": [\"https://...\"]}",
    "costTime": 5000,
    "completeTime": 1757584169490,
    "createTime": 1757584164490
  }
}
```

### Task States
| State | Description |
|-------|-------------|
| `waiting` | Task is queued |
| `success` | Task completed, results in `resultJson` |
| `fail` | Task failed, check `failCode` and `failMsg` |

### Result Format
When `state` is `success`, parse `resultJson` → `resultUrls` array contains download URLs for the generated audio.

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Request successful |
| 400 | Invalid request parameters |
| 401 | Authentication failed |
| 402 | Insufficient account balance |
| 404 | Resource not found |
| 422 | Parameter validation failed |
| 429 | Request rate limit exceeded |
| 500 | Internal server error |
