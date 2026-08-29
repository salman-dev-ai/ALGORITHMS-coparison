from __future__ import annotations

from io import BytesIO, StringIO
import pandas as pd

REQUIRED_COLUMNS = ["process_id", "arrival_time", "burst_time", "priority"]


def template_csv() -> bytes:
    frame = pd.DataFrame(
        [
            {"process_id": "P1", "arrival_time": 0, "burst_time": 8, "priority": 2},
            {"process_id": "P2", "arrival_time": 1, "burst_time": 4, "priority": 1},
            {"process_id": "P3", "arrival_time": 2, "burst_time": 2, "priority": 3},
        ]
    )
    return frame.to_csv(index=False).encode("utf-8")


def load_processes(source: bytes | str) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    try:
        raw = source.decode("utf-8-sig") if isinstance(source, bytes) else source
        frame = pd.read_csv(StringIO(raw))
    except Exception as exc:
        return [], [f"تعذر قراءة ملف CSV: {exc}"]
    frame.columns = [str(c).strip().lower() for c in frame.columns]
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        return [], [f"الأعمدة المطلوبة غير موجودة: {', '.join(missing)}"]
    if frame.empty:
        return [], ["الملف لا يحتوي على عمليات."]
    if (
        frame["process_id"].isna().any()
        or frame["process_id"].astype(str).str.strip().eq("").any()
    ):
        errors.append("كل عملية يجب أن تحتوي على Process ID.")
    if frame["process_id"].astype(str).duplicated().any():
        errors.append("يجب أن تكون Process IDs غير مكررة.")
    for column in ["arrival_time", "burst_time", "priority"]:
        converted = pd.to_numeric(frame[column], errors="coerce")
        if converted.isna().any():
            errors.append(f"العمود {column} يحتوي على قيم غير رقمية.")
        elif (converted % 1 != 0).any():
            errors.append(f"العمود {column} يجب أن يحتوي على أعداد صحيحة.")
        frame[column] = converted
    if not errors:
        if (frame["arrival_time"] < 0).any():
            errors.append("Arrival Time لا يمكن أن يكون سالبًا.")
        if (frame["burst_time"] <= 0).any():
            errors.append("Burst Time يجب أن يكون أكبر من صفر.")
        if (frame["priority"] <= 0).any():
            errors.append("Priority يجب أن يكون أكبر من صفر.")
    if errors:
        return [], errors
    return (
        frame[REQUIRED_COLUMNS]
        .assign(process_id=frame["process_id"].astype(str).str.strip())
        .to_dict("records"),
        [],
    )
