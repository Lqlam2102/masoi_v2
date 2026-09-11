# Spec: Ma Sói Web Multiplayer

**Ngày:** 2026-09-11
**Trạng thái:** đã chốt (brainstorming 2026-09-10)

## 1. Mục tiêu

Web app cho phép một nhóm bạn chơi Ma Sói online. Server tự động làm quản trò:
mở/đóng từng pha, thu hành động, xử lý toàn bộ luật, công bố kết quả. Người chơi
tranh luận bằng voice ngoài (Discord/Zoom) — app **không** làm voice và **không**
làm chat text.

## 2. Quyết định đã chốt

| Hạng mục | Quyết định |
|---|---|
| Thể loại | Ma Sói / social deduction |
| Hình thức | Web multiplayer online, phòng theo mã |
| Tranh luận | Voice ngoài app |
| Bộ vai | Bộ đầy đủ kiểu VN (11 vai, mục 4) |
| Quản trò | Server tự động hoàn toàn |
| Stack | Python 3.11+, FastAPI, WebSocket, frontend HTML/CSS/JS thuần (không build step) |
| Engine đêm | Pipeline thu *intent* + giải quyết theo *priority* cố định |
| Lưu trữ | In-memory, một process. Không DB ở v1 |

## 3. Global Constraints

- Python **>= 3.11** (dùng `X | Y` type syntax, `StrEnum`-style `str, Enum`).
- Dependency chỉ gồm: `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `pytest`,
  `pytest-asyncio`, `httpx` (test client). Không thêm gì khác ở v1.
- Frontend: **không** framework, **không** build step, **không** CDN ngoài.
  Chỉ `static/*.html|css|js` phục vụ qua `StaticFiles`.
- Toàn bộ text hiển thị cho người chơi bằng **tiếng Việt**.
- ID vai dùng snake_case tiếng Anh (`white_wolf`), tên hiển thị tiếng Việt (`Sói Trắng`).
- Logic luật phải là **hàm thuần** (không async, không I/O, không random ngoài
  `setup.py`) để unit-test được — đây là yêu cầu cứng, không phải khuyến nghị.
- Mọi ngẫu nhiên đi qua một `random.Random` được inject, để test seed được.

## 4. Bộ vai (11 vai)

### Phe Dân (`village`)

| ID | Tên | Hành động đêm | Luật |
|---|---|---|---|
| `villager` | Dân Thường | không | — |
| `seer` | Tiên Tri | mỗi đêm | Soi 1 người, biết người đó có thuộc phe Sói không |
| `guard` | Bảo Vệ | mỗi đêm | Bảo vệ 1 người khỏi đòn Sói. **Không** được bảo vệ cùng một người 2 đêm liên tiếp. Được tự bảo vệ |
| `witch` | Phù Thủy | mỗi đêm | 1 bình cứu + 1 bình độc, mỗi bình dùng 1 lần cả ván. Được biết ai bị Sói cắn đêm đó trước khi quyết định. Độc **không** bị chặn bởi Bảo Vệ/bình cứu |
| `hunter` | Thợ Săn | khi chết | Chết bằng bất kỳ cách nào (cắn, độc, treo cổ, chết theo người yêu) đều được bắn 1 người. Phát bắn **không** bị chặn |
| `cupid` | Cupid | đêm 1 | Ghép 2 người bất kỳ (có thể gồm chính mình) thành cặp đôi. Một người chết → người kia chết theo |
| `elder` | Già Làng | không | Chịu được **1** đòn Sói (đòn thứ hai mới chết). Độc, treo cổ, phát bắn Thợ Săn giết ngay |
| `fool` | Thằng Ngố | không | Nếu bị **treo cổ** thì thắng một mình, ván kết thúc ngay |

### Phe Sói (`wolf`)

| ID | Tên | Hành động đêm | Luật |
|---|---|---|---|
| `wolf` | Sói | mỗi đêm | Bầy sói bỏ phiếu chọn 1 người để cắn |
| `wolf_seer` | Sói Tiên Tri | mỗi đêm | Vẫn bỏ phiếu cắn cùng bầy; thêm: soi 1 người, biết **vai chính xác** |
| `white_wolf` | Sói Trắng | đêm chẵn | Vẫn bỏ phiếu cắn cùng bầy; các đêm chẵn được giết thêm 1 **Sói** khác. Thắng một mình nếu là người sống sót duy nhất |

**Thằng Ngố / Cupid / Sói Trắng đều có điều kiện thắng riêng** — xem mục 8.

## 5. Kiến trúc engine đêm (phương án A)

Hai thứ tự **tách rời nhau**, mỗi vai khai báo cả hai:

1. **`phase_order`** — thứ tự server mở sub-pha ban đêm (thứ tự người chơi thấy).
2. **`resolve_priority`** — thứ tự áp dụng effect khi giải quyết cuối đêm.

Ban đêm server **chỉ thu intent**, không thay đổi state. Hết sub-pha cuối, chạy
pipeline một lần.

### Thứ tự sub-pha ban đêm (`phase_order`)

```
cupid (chỉ đêm 1) → seer → wolf_seer → guard → wolf (bầy) → white_wolf (đêm chẵn) → witch
```

Phù Thủy đi cuối vì cần biết ai bị cắn. Thông tin "ai bị cắn" lấy trực tiếp từ
intent của bầy sói (chưa qua Bảo Vệ) — đúng luật VN: Phù Thủy thấy nạn nhân kể
cả khi Bảo Vệ đã đỡ.

### Thứ tự giải quyết (`resolve_priority`)

| Priority | Vai | Effect sinh ra |
|---|---|---|
| 10 | `cupid` | `Pair(a, b)` |
| 20 | `seer` | `Reveal` |
| 25 | `wolf_seer` | `Reveal` |
| 30 | `guard` | `Protect(target)` |
| 40 | `wolf` (bầy) | `Kill(target, WOLF)` |
| 45 | `white_wolf` | `Kill(target, WHITE_WOLF)` |
| 50 | `witch` | `Heal(target)` và/hoặc `Kill(target, WITCH)` |

Sau khi thu hết effect:

- **Bước tính sát thương** (`resolve_damage`): với mỗi `Kill`,
  - nguồn `WOLF`/`WHITE_WOLF` bị hủy nếu target có `Protect` **hoặc** `Heal`;
  - nếu không bị hủy mà target còn `armor > 0` (Già Làng) → trừ 1 giáp, không chết;
  - nguồn `WITCH`, `HUNTER`, `LOVER`, `LYNCH` → **không thể chặn**.
- **Bước chết lan** (`apply_deaths`): mỗi người chết kéo theo
  - người yêu (nếu có) → `Kill(lover, LOVER)`, đệ quy;
  - nếu người chết là Thợ Săn → đẩy vào hàng đợi `pending_hunters`, server mở
    sub-pha `hunter_shot` để họ chọn mục tiêu, rồi chạy lại chết lan.

### Effect log

Mỗi bước ghi một dòng tiếng Việt vào `state.log`
(ví dụ `"Đêm 2: Sói cắn Lâm — Bảo Vệ đỡ, không chết"`). Khi có tranh cãi "sao tôi
chết" thì mở log. Log **đầy đủ** chỉ hiện khi ván kết thúc; trong ván chỉ phát
những dòng công khai.

## 6. Vòng chơi

```
LOBBY → NIGHT (các sub-pha) → NIGHT_RESULT → DAY_DISCUSS → DAY_VOTE
      → DAY_RESULT → [HUNTER_SHOT nếu có] → NIGHT → …
```

- Mỗi sub-pha có deadline. Đủ intent của tất cả người còn sống thuộc pha đó, hoặc
  hết giờ → tự chuyển pha. Ai không kịp = không hành động.
- Thời lượng mặc định: sub-pha đêm 30s, `DAY_DISCUSS` 180s, `DAY_VOTE` 60s,
  `HUNTER_SHOT` 30s. Host chỉnh được khi tạo phòng.
- Bỏ phiếu (cả bầy sói lẫn treo cổ): **đa số tương đối**. Hòa hoặc không ai vote
  → **không ai chết**, ghi log.
- Người chết lộ vai (`reveal_role_on_death = True`).
- Kiểm tra thắng/thua sau mỗi lần `NIGHT_RESULT` và `DAY_RESULT`.

## 7. Chia vai theo số người (5–18)

`setup.py` giữ bảng `DEFAULT_SETUPS`; host có thể bật/tắt từng vai trước khi bắt đầu.

| Số người | Bộ vai |
|---|---|
| 5 | wolf, seer, guard, witch, villager |
| 6 | wolf ×2, seer, guard, witch, villager |
| 7 | wolf ×2, seer, guard, witch, hunter, villager |
| 8 | wolf ×2, seer, guard, witch, hunter, villager ×2 |
| 9 | wolf ×2, wolf_seer, seer, guard, witch, hunter, villager ×2 |
| 10 | 9 + cupid |
| 11 | 10 + elder |
| 12 | 11 + white_wolf |
| 13 | 12 + fool |
| 14 | 13 + villager |
| 15 | 14 + wolf |
| 16 | 15 + villager |
| 17 | 16 + villager |
| 18 | 17 + wolf |

## 8. Điều kiện thắng (kiểm tra theo đúng thứ tự này)

1. Thằng Ngố bị treo cổ → **`fool`** thắng, kết thúc ngay.
2. Chỉ còn đúng 2 người sống và họ là cặp đôi **khác phe** → **`lovers`** thắng.
3. Sói Trắng là người sống duy nhất → **`white_wolf`** thắng.
4. Không còn ai thuộc phe Sói → **`village`** thắng.
5. Số người phe Sói ≥ số người còn lại → **`wolf`** thắng.
6. Ngược lại → chưa kết thúc (`None`).

## 9. Giao thức WebSocket

Một endpoint: `GET /ws`. Mọi message là JSON một dòng.

### Client → Server

```json
{"type":"join","room":"ABCD","name":"Lâm","token":null}
{"type":"config","roles":{"fool":false},"timers":{"day_discuss":240}}
{"type":"start"}
{"type":"action","phase":"night_seer","targets":["p3"]}
{"type":"vote","target":"p3"}
```

- `config` và `start` chỉ host gọi được.
- `action.targets` là list để Cupid gửi 2 id và Phù Thủy gửi `[]`/`[heal]`/`[poison]`
  kèm `extra` (xem mục vai trong plan).

### Server → Client

```json
{"type":"joined","you":{"id":"p1","name":"Lâm"},"token":"…","is_host":true}
{"type":"state","phase":"night_seer","deadline":1757548800,"night":2,
 "players":[{"id":"p1","name":"Lâm","alive":true,"role":null}],
 "you":{"id":"p3","role":"seer","alive":true},
 "prompt":{"action":"pick","count":1,"candidates":["p1","p2"]}}
{"type":"private","text":"Lâm KHÔNG thuộc phe Sói"}
{"type":"night_result","night":2,"deaths":[{"id":"p1","name":"Lâm","role":"guard"}],"public_log":["…"]}
{"type":"day_result","lynched":{"id":"p2","name":"An","role":"wolf"},"votes":{"p2":3}}
{"type":"game_over","winner":"village","roles":{"p1":"guard"},"full_log":["…"]}
{"type":"error","message":"Không phải lượt của bạn"}
```

**Nguyên tắc bảo mật thông tin:** `state.players[].role` luôn `null` trừ khi
(a) là chính người xem, (b) người đó đã chết, (c) người xem thuộc phe Sói và người
đó cũng thuộc phe Sói, (d) người đó là người yêu của người xem. Việc lọc nằm gọn
trong `views.py` và phải có test riêng.

## 10. Phòng & kết nối lại

- Mã phòng 4 ký tự `A–Z0–9`, sinh ngẫu nhiên, tránh trùng.
- Người đầu tiên vào = host. Host thoát → host chuyển cho người còn lại sớm nhất.
- Mỗi người nhận một `token` khi join. Reconnect bằng `{"type":"join","token":…}`
  lấy lại đúng ghế, đúng vai, đúng state. Mất kết nối **không** giết nhân vật.
- Ván đang chạy mà hết người kết nối trong 10 phút → xóa phòng.

## 11. Ngoài phạm vi v1

Voice/chat trong app, lưu DB, tài khoản người dùng, xem lại ván (replay UI),
bảng xếp hạng, mobile app, vai tùy biến do người dùng tự viết.

## 12. Rủi ro đã biết

- **Luật chồng chéo** là nguồn bug chính → mọi tổ hợp trong mục 5 phải có test.
  Ca kinh điển bắt buộc test: Bảo Vệ đỡ đúng người Sói cắn **và** Phù Thủy cứu
  cùng lúc; Thợ Săn bị độc chết và bắn ngược Phù Thủy; cặp đôi chết chung kéo theo
  Thợ Săn; Sói Trắng giết sói cuối cùng làm phe Dân thắng ngay.
- **Timer + WebSocket** dễ rò task → mỗi phòng đúng một task pha, hủy khi chuyển pha.
