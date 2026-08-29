from __future__ import annotations

from collections import deque
# from copy import deepcopy
from typing import Callable

from .models import ExecutionSlice, Process, ProcessResult, ScheduleResult


def _result(
    name: str, processes: list[Process], timeline: list[ExecutionSlice]
) -> ScheduleResult:

    starts: dict[str, int] = {}

    completions: dict[str, int] = {}


    for item in timeline:
        starts.setdefault(item.process_id, item.start_time)
        completions[item.process_id] = item.end_time
    rows = []
    for process in sorted(processes, key=lambda p: p.process_id):
        start = starts.get(process.process_id)
        completion = completions.get(process.process_id)
        turnaround = (
            completion - process.arrival_time if completion is not None else None
        )
        waiting = turnaround - process.burst_time if turnaround is not None else None
        response = start - process.arrival_time if start is not None else None
        rows.append(
            ProcessResult(
                process.process_id,
                process.arrival_time,
                process.burst_time,
                process.priority,
                start,
                completion,
                waiting,
                turnaround,
                response,
            )
        )
    switches = sum(
        1 for a, b in zip(timeline, timeline[1:]) if a.process_id != b.process_id
    )
    idle = sum(item.duration for item in timeline if item.process_id == "IDLE")
    return ScheduleResult(name, rows, timeline, switches, idle)


def fcfs(processes: list[Process]) -> ScheduleResult:

#   ترتيب العمليات تصاعدياً بناءً على وقت الوصول
    ordered = sorted(processes, key=lambda p: (p.arrival_time, p.process_id))


# تختبر كل عملية: إذا كان وقت وصولها أكبر من الوقت الحالي (now)،
#  تضيف فترة "خمول" (IDLE) للمعالج.

    timeline, now = [], 0
    for process in ordered:
        if now < process.arrival_time:
            timeline.append(ExecutionSlice("IDLE", now, process.arrival_time))
            now = process.arrival_time

# تضيف العملية للجدول الزمني لتُنفذ بالكامل (غير قابلة للمقاطعة)،
#  وتزيد الوقت الحالي بمقدار وقت تنفيذ العملية (burst_time).
        timeline.append(
            ExecutionSlice(process.process_id, now, now + process.burst_time)
        )
        now += process.burst_time


    return _result("FCFS", processes, timeline)




def sjf(processes: list[Process]) -> ScheduleResult:
    # ستخدم مجموعة (remaining) لتتبع العمليات التي لم تُنفذ بعد
    remaining = set(processes)

    timeline, now = [], 0

    while remaining:
        # تجمع العمليات "المتاحة" (التي وصل وقتها).
        available = [p for p in remaining if p.arrival_time <= now]
        if not available:
            # إذا لم توجد عمليات متاحة، تقفز
            #  بالزمن إلى وقت وصول أقرب عملية تالية مع تسجيل فترة خمول.
            next_time = min(p.arrival_time for p in remaining)
            timeline.append(ExecutionSlice("IDLE", now, next_time))
            now = next_time
            continue
        # إذا وجدت عمليات متاحة، تختار العملية صاحبة أقل وقت تنفيذ (burst_time). 
        # في حال التعادل، تفاضل بوقت الوصول ثم بمعرف العملية.
        process = min(
            available, key=lambda p: (p.burst_time, p.arrival_time, p.process_id)
        )
        # تُنفذ العملية بالكامل وتزيلها من قائمة الانتظار.
        remaining.remove(process)
        timeline.append(
            ExecutionSlice(process.process_id, now, now + process.burst_time)
        )
        now += process.burst_time


    return _result("SJF", processes, timeline)


def round_robin(processes: list[Process], quantum: int) -> ScheduleResult:
# تتأكد أولاً أن الشريحة الزمنية 
# (quantum) رقم موجب
    if quantum <= 0:
        raise ValueError("Time Quantum must be positive")
    
    ordered = sorted(processes, key=lambda p: (p.arrival_time, p.process_id))

    remaining = {p.process_id: p.burst_time for p in processes}

    # by_id = {p.process_id: p for p in processes}
# تستخدم طابور انتظار deque لتنظيم العمليات.
    queue: deque[str] = deque()

    timeline, now, index = [], 0, 0
    while queue or index < len(ordered):
        if not queue:
            if now < ordered[index].arrival_time:
                timeline.append(
                    ExecutionSlice("IDLE", now, ordered[index].arrival_time)
                )
                now = ordered[index].arrival_time
            while index < len(ordered) and ordered[index].arrival_time <= now:
# أثناء تشغيل العملية الحالية، تقوم بإضافة أي عمليات جديدة وصل وقتها إلى طابور الانتظار.
                queue.append(ordered[index].process_id)
                index += 1
        pid = queue.popleft()
        run = min(quantum, remaining[pid])
        timeline.append(ExecutionSlice(pid, now, now + run))
        now += run
        remaining[pid] -= run

        # إذا لم تنتهِ العملية الحالية بعد استهلاك شريحتها الزمنية، يتم إعادتها إلى نهاية الطابور لتنتظر دورها مجدداً.
        while index < len(ordered) and ordered[index].arrival_time <= now:
            queue.append(ordered[index].process_id)
            index += 1
        if remaining[pid] > 0:
            queue.append(pid)
    return _result(f"Round Robin (q={quantum})", processes, timeline)



def priority(processes: list[Process]) -> ScheduleResult:
    # تحتوي على كافة العمليات. تم استخدام النوع set بدلاً من قائمة عادية لتسهيل وتسريع عملية حذف 
    # أي عملية بمجرد الانتهاء من تنفيذها.
    remaining = set(processes)

    timeline, now = [], 0

    while remaining:
        # تصفية العمليات المتبقية. يجمع فقط العمليات "المتاحة" حالياً، وهي التي يكون وقت وصولها 
        # (arrival_time) أقل من أو يساوي الوقت الحالي (now).
        available = [p for p in remaining if p.arrival_time <= now]
        if not available:
            # إذا كانت القائمة فارغة، يقوم هذا السطر بالبحث في العمليات المتبقية عن أصغر وقت وصول 
            # (arrival_time) قادم في المستقبل.
            next_time = min(p.arrival_time for p in remaining)
            # يُضيف للجدول الزمني فترة خمول (IDLE)، تبدأ من الوقت الحالي now وتنتهي عند 
            # next_time (وقت وصول العملية التالية).
            timeline.append(ExecutionSlice("IDLE", now, next_time))
            # يُحدث الوقت الحالي للمنظومة ليقفز مباشرة إلى وقت وصول العملية التالية.
            now = next_time
            continue
        process = min(
            available, key=lambda p: (p.priority, p.arrival_time, p.process_id)
        )
        remaining.remove(process)

        timeline.append(
            ExecutionSlice(process.process_id, now, now + process.burst_time)
        )
        now += process.burst_time
    return _result("Priority", processes, timeline)


ALGORITHMS: dict[str, Callable[..., ScheduleResult]] = {
    "FCFS": fcfs,
    "SJF": sjf,
    "Round Robin": round_robin,
    "Priority": priority,
}
