# Telegram VoIP Notifier for Home Assistant

Custom integration gọi add-on **Telegram VoIP Notifier** qua REST API để:

- gửi tin nhắn Telegram từ nhiều tài khoản;
- gửi voice message bằng Edge TTS;
- gọi P2P 1:1 và phát TTS khi người nhận nghe máy;
- gọi lặp làm chuông báo động;
- theo dõi số tài khoản online và số cuộc gọi đang hoạt động.

Integration này **không chứa phần đăng nhập Telegram**. Cần cài add-on
`telegram_voip` trước, sau đó nhập URL và API token của add-on.

> Chưa kiểm thử với tài khoản Telegram thật hoặc Home Assistant runtime thật.
> Gọi tự động có thể vi phạm Telegram Terms of Service; chỉ dùng tài khoản phụ
> hoặc tài khoản bạn sở hữu.

## Cài đặt

### HACS

1. HACS > Integrations > Custom repositories.
2. Thêm `https://github.com/trankhanhduy2929-beep/telegramvoip_homeassistant`,
   category **Integration**.
3. Cài **Telegram VoIP Notifier**.
4. Restart Home Assistant.
5. Settings > Devices & services > Add integration > **Telegram VoIP Notifier**.
6. Nhập URL add-on, ví dụ `http://telegram_voip:8098`, và API token.

### Thủ công

Copy thư mục `custom_components/telegram_voip` vào
`/config/custom_components/telegram_voip`, restart Home Assistant, rồi thêm
integration.

## Cấu hình

- **Add-on URL**: URL nội bộ của add-on, thường là
  `http://telegram_voip:8098`. Không thêm dấu `/` ở cuối.
- **API token**: token trong add-on Configuration. Nếu để trống, add-on tự sinh
  token tại `/data/api_token`.

Có thể đổi URL/token sau khi cài bằng **Configure**.

## Services

### `telegram_voip.send_message`

```yaml
action: telegram_voip.send_message
data:
  account: "+84901234567"
  recipient: "@username"
  message: "Cảnh báo từ Home Assistant"
```

### `telegram_voip.send_tts`

```yaml
action: telegram_voip.send_tts
data:
  account: "+84901234567"
  recipient: "@username"
  text: "Cửa chính đang mở."
  voice: "vi-VN-HoaiMyNeural"
```

### `telegram_voip.call`

```yaml
action: telegram_voip.call
data:
  account: "+84901234567"
  recipient: "@username"
  text: "Có người lạ trước cửa."
  wait: true
  wait_seconds: 90
```

### `telegram_voip.ring`

```yaml
action: telegram_voip.ring
data:
  account: "+84901234567"
  recipient: "@username"
  text: "Cảnh báo động."
  attempts: 2
  interval: 15
```

### `telegram_voip.hangup`

```yaml
action: telegram_voip.hangup
data:
  account: "+84901234567"
```

## Sensors

- `sensor.telegram_voip_accounts_online`
- `sensor.telegram_voip_active_calls`

## Yêu cầu

- Home Assistant `2024.12.0` trở lên.
- Add-on Telegram VoIP Notifier đang chạy và truy cập được từ Home Assistant.
- Tài khoản gửi đã đăng nhập trong add-on.
- Tài khoản nhận cho phép nhận cuộc gọi từ tài khoản gửi.
