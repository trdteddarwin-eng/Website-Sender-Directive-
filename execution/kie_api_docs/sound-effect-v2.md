# Sound Effect V2 API Documentation

> Generate content using the Sound Effect V2 model

## Overview

This document describes how to use the Sound Effect V2 model for content generation. The process consists of two steps:
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
| model | string | Yes | Model name, format: `elevenlabs/sound-effect-v2` |
| input | object | Yes | Input parameters object |
| callBackUrl | string | No | Callback URL for task completion notifications |

### input Object Parameters

#### text
- **Type**: `string`
- **Required**: Yes
- **Description**: The text describing the sound effect to generate
- **Max Length**: 450 characters

#### loop
- **Type**: `boolean`
- **Required**: No
- **Description**: Whether to create a sound effect that loops smoothly
- **Default Value**: `false`

#### duration_seconds
- **Type**: `number`
- **Required**: No
- **Description**: Duration in seconds (0.5-22). If None, optimal duration will be determined from prompt
- **Range**: 0.5 - 22 (step: 0.1)

#### prompt_influence
- **Type**: `number`
- **Required**: No
- **Description**: How closely to follow the prompt (0-1). Higher values mean less variation
- **Range**: 0 - 1 (step: 0.01)
- **Default Value**: `0.3`

#### output_format
- **Type**: `string`
- **Required**: No
- **Description**: Output format of the generated audio
- **Options**: `mp3_22050_32`, `mp3_44100_32`, `mp3_44100_64`, `mp3_44100_96`, `mp3_44100_128`, `mp3_44100_192`, `pcm_8000`, `pcm_16000`, `pcm_22050`, `pcm_24000`, `pcm_44100`, `pcm_48000`, `ulaw_8000`, `alaw_8000`, `opus_48000_32`, `opus_48000_64`, `opus_48000_96`, `opus_48000_128`, `opus_48000_192`
- **Default Value**: `"mp3_44100_128"`

### Request Example

```json
{
  "model": "elevenlabs/sound-effect-v2",
  "input": {
    "text": "dramatic whoosh with sparkle chime",
    "loop": false,
    "duration_seconds": 3.0,
    "prompt_influence": 0.3,
    "output_format": "mp3_44100_128"
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
    "model": "elevenlabs/sound-effect-v2",
    "state": "success",
    "resultJson": "{\"resultUrls\": [\"https://...\"]}",
    "costTime": 8000,
    "completeTime": 1757584172490,
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
