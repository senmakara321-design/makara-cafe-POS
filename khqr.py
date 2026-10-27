"""KHQR (Bakong) payload builder - EMVCo merchant-presented QR with CRC16.
The output is a text string; utils.qr_png() turns it into a QR picture."""
import time


def _tlv(tag, value):
    return f"{tag}{len(value.encode('utf-8')):02d}{value}"


def crc16(text):
    """CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) - required at the end of every KHQR."""
    crc = 0xFFFF
    for b in text.encode("utf-8"):
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def build_khqr(bakong_id, merchant_name, city="Phnom Penh", amount=None,
               currency="USD", bill_number=None, expire_minutes=10):
    """amount=None -> static QR (customer types the amount). amount given -> dynamic QR."""
    dynamic = amount is not None
    usd = currency.upper() == "USD"
    parts = [
        _tlv("00", "01"),
        _tlv("01", "12" if dynamic else "11"),
        _tlv("29", _tlv("00", bakong_id)),          # Bakong account of the shop
        _tlv("52", "5999"),                          # merchant category
        _tlv("53", "840" if usd else "116"),         # 840 = USD, 116 = KHR
    ]
    if dynamic:
        parts.append(_tlv("54", f"{amount:.2f}" if usd else str(int(round(amount)))))
    parts += [_tlv("58", "KH"), _tlv("59", merchant_name[:25]), _tlv("60", city[:15])]
    if bill_number:
        parts.append(_tlv("62", _tlv("01", bill_number[:25])))
    if dynamic:
        now = int(time.time() * 1000)
        parts.append(_tlv("99", _tlv("00", str(now)) + _tlv("01", str(now + expire_minutes * 60000))))
    payload = "".join(parts) + "6304"
    return payload + crc16(payload)
