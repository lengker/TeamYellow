# A5 后端接口调用说明（当前版本）

本文只覆盖两部分：

1. 当前数据库表结构（字段、主键、外键）
2. 当前可用接口（路由、参数、返回、规则/限制）

---

## 一、数据库表结构

> 数据库使用 SQLite，已启用外键约束（`PRAGMA foreign_keys = ON`）。

### 1) `LNG_AIRPORTS`（机场）

| 字段 | 类型 | 说明 |
|---|---|---|
| airport_code | TEXT | 主键 |
| name | TEXT | 机场名 |
| country_code | TEXT | 国家码 |
| airports_latitude | REAL | 纬度 |
| airports_longitude | REAL | 经度 |

- 主键：`airport_code`
- 外键：无

### 2) `LNG_USERS`（用户）

| 字段 | 类型 | 说明 |
|---|---|---|
| user_id | INTEGER | 主键，自增 |
| username | TEXT | 唯一，非空 |
| password_hash | TEXT | 非空 |
| role | TEXT | 角色 |
| email | TEXT | 邮箱 |

- 主键：`user_id`
- 外键：无

### 3) `LNG_TRACKS`（航迹）

| 字段 | 类型 | 说明 |
|---|---|---|
| track_id | INTEGER | 主键，自增 |
| timestamp | TEXT | 非空 |
| flight_id | TEXT | 非空 |
| tracks_latitude | REAL | 非空 |
| tracks_longitude | REAL | 非空 |
| altitude | REAL | 高度 |
| speed | REAL | 速度 |
| heading | REAL | 航向 |
| departure_airport_code | TEXT | 出发机场 |
| arrival_airport_code | TEXT | 到达机场 |
| next_id | INTEGER | 指向下一段 track |
| prev_id | INTEGER | 指向上一段 track |

- 主键：`track_id`
- 外键：
  - `departure_airport_code -> LNG_AIRPORTS.airport_code`
  - `arrival_airport_code -> LNG_AIRPORTS.airport_code`
  - `next_id -> LNG_TRACKS.track_id`
  - `prev_id -> LNG_TRACKS.track_id`

### 4) `LNG_AUDIO_RECORDS`（音频）

| 字段 | 类型 | 说明 |
|---|---|---|
| audio_id | INTEGER | 主键，自增 |
| source_url | TEXT | 非空 |
| start_time_utc | TEXT | 非空 |
| end_time_utc | TEXT | 非空 |
| duration_ms | INTEGER | 非空 |
| file_name | TEXT | 非空 |
| file_path | TEXT | 非空 |
| file_size | INTEGER | 文件大小 |
| status | INTEGER | 默认 0，约束 `IN (0,1,2,3)` |
| last_access_at | TEXT | 最近访问时间（系统维护） |
| track_id | INTEGER | 非空，所属 track |
| next_id | INTEGER | 自引用下一条 |
| prev_id | INTEGER | 自引用上一条 |

- 主键：`audio_id`
- 外键：
  - `track_id -> LNG_TRACKS.track_id`
  - `next_id -> LNG_AUDIO_RECORDS.audio_id`
  - `prev_id -> LNG_AUDIO_RECORDS.audio_id`
- 检查约束：`end_time_utc >= start_time_utc`

### 5) `LNG_ANNOTATIONS`（标注）

| 字段 | 类型 | 说明 |
|---|---|---|
| annotation_id | INTEGER | 主键，自增 |
| label_type | TEXT | 标签类型 |
| author_id | INTEGER | 非空，用户 |
| audio_id | INTEGER | 非空，音频 |
| relative_start | REAL | 相对起始 |
| relative_end | REAL | 相对结束 |
| abs_start_time | TEXT | 绝对起始 |
| abs_end_time | TEXT | 绝对结束 |
| asr_content | TEXT | 识别内容 |
| vad_confidence | REAL | 置信度 |
| is_annotated | INTEGER | 默认 0，约束 `IN (0,1)` |
| annotation_text | TEXT | 标注文本 |
| annotation_time | TEXT | 标注时间 |
| storage_tag | TEXT | 存储标记 |
| next_id | INTEGER | 自引用下一条 |
| prev_id | INTEGER | 自引用上一条 |

- 主键：`annotation_id`
- 外键：
  - `author_id -> LNG_USERS.user_id`
  - `audio_id -> LNG_AUDIO_RECORDS.audio_id`
  - `next_id -> LNG_ANNOTATIONS.annotation_id`
  - `prev_id -> LNG_ANNOTATIONS.annotation_id`
- 检查约束：
  - `relative_start <= relative_end`
  - `abs_end_time >= abs_start_time`

### 6) `LNG_VSP_DATA`（VSP）

| 字段 | 类型 | 说明 |
|---|---|---|
| vsp_id | INTEGER | 主键，自增 |
| airport_code | TEXT | 非空，所属机场 |
| region | TEXT | 区域 |
| runway | TEXT | 跑道 |
| taxiway | TEXT | 滑行道 |
| vor_id | TEXT | VOR |
| waypoint | TEXT | 航路点 |
| approach_type | TEXT | 进近类型 |
| gate | TEXT | 机位 |
| holding_point | TEXT | 等待点 |
| sector_name | TEXT | 扇区 |

- 主键：`vsp_id`
- 外键：`airport_code -> LNG_AIRPORTS.airport_code`

### 7) `LNG_STORAGE_LOG`（存储日志）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键，自增 |
| action_type | TEXT | 非空，`CLEANUP/ARCHIVE` |
| source_url | TEXT | 非空 |
| released_space | INTEGER | 非空 |
| op_time | TEXT | 非空 |

- 主键：`id`
- 外键：无

---

## 二、接口总体概述

当前接口分为 5 组：

1. **健康检查**
   - `GET /health`：服务存活检查
2. **通用表 CRUD（正式）**
   - 前缀：`/tables`
   - 面向所有逻辑表（`airports/users/tracks/audio_records/annotations/vsp_data/storage_log`）
3. **通用查询**
   - 前缀：`/query`
   - `POST /query/arbitrary`：按外键图做跨表任意字段查询
4. **开发态管理接口**
   - 前缀：`/dev`
   - 包含重置/建表/删表/DB UI 行级 CRUD（仅开发环境）
5. **tracks 扩展接口（新增）**
   - 正式版：`/tables/tracks/ext/*`
   - 开发态版：`/dev/db-ui/rows/tracks/ext/*`

---

## 三、接口详细说明

## 3.1 健康检查

### `GET /health`

- 入参：无
- 返回：`{"ok": true}`
- 规则：仅用于连通性检查

---

## 3.2 通用表 CRUD（`/tables`）

> `table_key` 可选：`airports`、`users`、`tracks`、`audio_records`、`annotations`、`vsp_data`、`storage_log`

### `POST /tables/{table_key}`

- 入参：JSON 对象，字段名为该表可写字段
- 返回：`{"id": 主键值}`
  - `airports` 返回主键字符串（`airport_code`）
  - 其他表返回整型自增 id
- 规则/限制：
  - 字段需满足表约束（非空、唯一、外键、check）
  - 非法字段会被忽略；若最终无可写字段，返回 400

### `GET /tables/{table_key}/{item_id}`

- 入参：路径主键（`airports` 用字符串，其他用整数）
- 返回：该行完整字段对象
- 规则/限制：
  - 不存在返回 404
  - `audio_records` 查询会自动更新 `last_access_at`

### `GET /tables/{table_key}?limit=100&offset=0`

- 入参：
  - `limit`：1~1000，默认 100
  - `offset`：>=0，默认 0
- 返回：数组 `[{...}]`
- 规则/限制：
  - `audio_records` 列表查询会自动更新返回行的 `last_access_at`

### `PUT /tables/{table_key}/{item_id}`

- 入参：JSON 对象（要更新的字段）
- 返回：`{"updated": true}`
- 规则/限制：
  - `airports` 的主键 `airport_code` 不通过该接口修改
  - 字段无变化或主键不存在会返回 404（`Item not found or no fields changed`）
  - 外键/约束冲突返回 400

### `DELETE /tables/{table_key}/{item_id}`

- 入参：路径主键
- 返回：`{"deleted": true}`
- 规则/限制：
  - 仅删除当前表该记录
  - 不存在返回 404

---

## 3.3 通用查询（`/query`）

### `POST /query/arbitrary`

- 入参：
```json
{
  "reference": {"任意字段": "值", "...": "..."},
  "select": ["字段1", "字段2"]
}
```
- 返回：`[{"字段1": "...", "字段2": "..."}, ...]`
- 规则/限制：
  - `reference` 至少 1 项，`select` 至少 1 项
  - 支持跨表：`reference` 字段与 `select` 字段都可分布在不同表
  - 字段名不存在会 400（`Unknown field`）
  - 若字段名在多表重复，系统按外键图选择可达且距离最短路径；不可判定时会 400（`ambiguous across tables`）
  - 去重返回（相同 select 结果只保留一条）

---

## 3.4 开发态管理接口（`/dev`）

> 仅在开发环境可用，生产环境会返回 403（`Development endpoints are disabled.`）

### 表级管理

- `POST /dev/reset/{table_key}`
  - 返回：`{"reset":"tracks","recreated_order":[...]}`
  - 作用：级联清空该表及下游依赖表，再按依赖顺序重建

- `POST /dev/reset-all`
  - 返回：`{"reset_all": true, "recreated_order":[...]}`
  - 作用：清空并重建所有表

- `GET /dev/db-ui/snapshot?limit=100`
  - 返回：`{"tables":[{"key","sql_name","exists","columns","rows"}, ...]}`
  - 作用：DB 管理页面快照

- `POST /dev/db-ui/drop/{table_key}`
  - 返回：`{"dropped":"tracks","dropped_order":[...]}`
  - 作用：按依赖级联 DROP 表

- `POST /dev/db-ui/ensure/{table_key}`
  - 返回：`{"ensure":"tracks","created_or_skipped":[{"key","action"}, ...]}`
  - 作用：补齐该表及祖先依赖表

### 行级 CRUD（开发态）

- `POST /dev/db-ui/rows/create/{table_key}`
  - 入参：`{"values": {...}}` 或直接 `{...}`
  - 返回：`{"id": ...}`

- `POST /dev/db-ui/rows/delete/{table_key}`
  - 入参：`{"id": 主键}`
  - 返回：`{"deleted": true, "id": 主键}`
  - 规则：包含级联删除逻辑（例如删 track 会删关联 audio，再删 annotation）

- `POST /dev/db-ui/rows/search/{table_key}`
  - 入参：`{"filters": {...}, "limit": 100}` 或直接把过滤字段放顶层
  - 返回：`{"rows":[...]}`
  - 规则：搜索时会忽略主键字段过滤；`audio_records` 搜索会刷新 `last_access_at`

- `POST /dev/db-ui/rows/update/{table_key}`
  - 入参：`{"id": 主键, "new_id": 可选, "values": {...}}`
  - 返回：`{"updated": true, "id": 主键}`
  - 规则：
    - `airports` 支持 `new_id` 改主键（并联动更新 tracks/vsp_data 外键）
    - 其他表不支持 `new_id`

---

## 3.5 tracks 扩展接口（正式版）

## 3.5.1 `POST /tables/tracks/ext/create`

- 入参：
  - 单条：`{...}`
  - 多条：`[{...}, {...}]`
- 单条字段要求：
  - 必填：`timestamp, flight_id, tracks_latitude, tracks_longitude, altitude, speed, heading, airport_code`
  - 其中 `airport_code` 必须是数组，长度 >= 2，例如 `["VHHH","VVTS","ZBAA"]`
- 返回：
  - 单段：`{"id": 12, "track_id": 12}`
  - 多段链：`{"id": 12, "track_id": [12,13,...]}`
  - 多条请求：返回数组
- 规则/限制：
  - 不允许直接传 `departure_airport_code/arrival_airport_code/next_id/prev_id`
  - `airport_code` 会自动拆成相邻段并构造 `prev_id/next_id`

## 3.5.2 `POST /tables/tracks/ext/delete`

- 入参：`{"id": track_id}`
- 返回：`{"deleted": true, "ids":[链路所有track_id], "count": 数量}`
- 规则/限制：
  - 传任意链上节点，会向前/向后找到整链后全部删除
  - 复用开发态级联删除逻辑，关联 audio/annotation 也会处理

## 3.5.3 `POST /tables/tracks/ext/update/{item_id}`

- 入参：
```json
{
  "values": {
    "speed": 900,
    "departure_airport_code": "VHHH"
  }
}
```
（也支持直接把更新字段放在顶层）
- 返回：`{"updated": true, "id": item_id, "chain_ids":[...]}`
- 规则/限制：
  - 禁止更新 `next_id`、`prev_id`
  - 普通字段（除机场码外）会同步更新整条链
  - 若更新 `departure_airport_code` 且存在 `prev_id`，会同步把上一段 `arrival_airport_code` 改为同值
  - 若更新 `arrival_airport_code` 且存在 `next_id`，会同步把下一段 `departure_airport_code` 改为同值

## 3.5.4 `POST /tables/tracks/ext/search`

- 入参：`{"filters": {...}, "limit": 100}`（也支持直接把过滤字段放顶层）
- 返回：
  - 无结果：`[]`
  - 单链：`{...}`
  - 多链：`[{...}, {...}]`
- 聚合返回结构：
  - `track_id`: 数组（链上每段主键）
  - `airport_code`: 数组（从链头 departure 到链尾 arrival）
  - 其余字段：`timestamp, flight_id, tracks_latitude, tracks_longitude, altitude, speed, heading`
- 规则/限制：
  - 过滤逻辑复用行级搜索（主键过滤不生效）

---

## 3.6 tracks 扩展接口（开发态版）

与正式版规则一致，仅路由前缀不同，且受开发环境开关限制。

- `POST /dev/db-ui/rows/tracks/ext/create`
- `POST /dev/db-ui/rows/tracks/ext/delete`
- `POST /dev/db-ui/rows/tracks/ext/update`
- `POST /dev/db-ui/rows/tracks/ext/search`

其中：

- `ext/update` 开发态版把 `id` 放在 body：`{"id": 12, "values": {...}}`
- 其余入参/出参与正式版一致

---

## 四、联调建议（简版）

- 先确保父表数据存在（例如 `tracks` 依赖 `airports`，`audio_records` 依赖 `tracks`）
- 若返回 400，优先检查：字段名、外键存在性、时间/区间 check 约束
- 若要快速验证结构，先调 `GET /dev/db-ui/snapshot`
- 生产环境不要依赖 `/dev/*` 接口

