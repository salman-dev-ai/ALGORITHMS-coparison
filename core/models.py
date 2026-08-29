from __future__ import annotations

# dataclass, field: تُستخدم لإنشاء فئات مخصصة لتخزين البيانات بسرعة دون الحاجة لكتابة دالة __init__ يدوياً.
#  دالة field تستخدم لإعطاء قيم افتراضية معقدة كالقوائم.
from dataclasses import dataclass, field
# Optional: تعني أن المتغير يمكن أن يحتوي على قيمة من نوع محدد
#  (مثل رقم صحيح) أو يكون فارغاً (None).
from typing import Optional



# @dataclass(frozen=True): تجعل هذه الفئة "مجمدة"، أي لا يمكن تعديل بيانات 
# أي عملية بعد إنشائها، مما يمنع الأخطاء أثناء المحاكاة.
@dataclass(frozen=True)
class Process:
    process_id: str
    arrival_time: int
    burst_time: int
    priority: int = 1

    def __post_init__(self) -> None:
        if not self.process_id.strip():
            raise ValueError("Process ID cannot be empty")
        if self.arrival_time < 0:
            raise ValueError("Arrival time must be non-negative")
        if self.burst_time <= 0:
            raise ValueError("Burst time must be positive")


# تُستخدم لتمثيل فترات عمل المعالج، سواء كان يُنفذ عملية معينة أو في حالة خمول.
@dataclass
class ExecutionSlice:
    process_id: str
    start_time: int
    end_time: int

    @property
    def duration(self) -> int:
        return self.end_time - self.start_time


# مخصصة لتخزين التقرير التفصيلي لكل عملية بعد
#  انتهاء تشغيل خوارزمية الجدولة.
@dataclass
class ProcessResult:
    process_id: str
    arrival_time: int
    burst_time: int
    priority: int
    start_time: Optional[int] = None
    completion_time: Optional[int] = None
    waiting_time: Optional[int] = None
    turnaround_time: Optional[int] = None
    response_time: Optional[int] = None


@dataclass
class ScheduleResult:
    algorithm: str
    processes: list[ProcessResult] = field(default_factory=list)
    timeline: list[ExecutionSlice] = field(default_factory=list)
    context_switches: int = 0
    idle_time: int = 0

    @property
    def average_waiting_time(self) -> float:
        return (
            sum(p.waiting_time or 0 for p in self.processes) / len(self.processes)
            if self.processes
            else 0.0
        )

    @property
    def average_turnaround_time(self) -> float:
        return (
            sum(p.turnaround_time or 0 for p in self.processes) / len(self.processes)
            if self.processes
            else 0.0
        )

    @property
    def average_response_time(self) -> float:
        return (
            sum(p.response_time or 0 for p in self.processes) / len(self.processes)
            if self.processes
            else 0.0
        )

    @property
    def makespan(self) -> int:
        return max((slice_.end_time for slice_ in self.timeline), default=0)
