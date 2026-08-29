from core.algorithms import fcfs, priority, round_robin, sjf
from core.csv_loader import load_processes
from core.models import Process


def test_fcfs_metrics():
    result = fcfs([Process("P1", 0, 5), Process("P2", 1, 3)])
    rows = {row.process_id: row for row in result.processes}
    assert rows["P1"].waiting_time == 0
    assert rows["P2"].waiting_time == 4
    assert result.average_waiting_time == 2


def test_sjf_non_preemptive_order():
    result = sjf([Process("P1", 0, 7), Process("P2", 0, 2), Process("P3", 1, 1)])
    assert [slice_.process_id for slice_ in result.timeline] == ["P2", "P3", "P1"]


def test_priority_order_and_tie_breaking():
    result = priority(
        [Process("P1", 0, 3, 2), Process("P2", 0, 2, 1), Process("P3", 0, 1, 1)]
    )
    assert [slice_.process_id for slice_ in result.timeline] == ["P2", "P3", "P1"]


def test_round_robin_splits_execution():
    result = round_robin([Process("P1", 0, 5), Process("P2", 0, 2)], quantum=2)
    assert [(s.process_id, s.start_time, s.end_time) for s in result.timeline] == [
        ("P1", 0, 2),
        ("P2", 2, 4),
        ("P1", 4, 6),
        ("P1", 6, 7),
    ]


def test_idle_time_is_recorded():
    result = fcfs([Process("P1", 3, 2)])
    assert result.idle_time == 3
    assert result.timeline[0].process_id == "IDLE"


def test_csv_loader_accepts_valid_data():
    records, errors = load_processes(
        "process_id,arrival_time,burst_time,priority\nP1,0,4,1\n"
    )
    assert not errors
    assert records[0]["process_id"] == "P1"


def test_csv_loader_rejects_missing_columns_and_duplicates():
    _, errors = load_processes("process_id,arrival_time,burst_time\nP1,0,4\nP1,1,2\n")
    assert errors
