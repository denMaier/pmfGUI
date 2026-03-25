from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
from typing import Any, Mapping

from foamlib import FoamFile

from app_core import FIELD_REGIONS, PATHS, SOLVER_OPTIONS, SOLVER_TYPE_MAP, case_path

RUN_LOG_NAME = ".pmf_run.log"
RUN_METADATA_NAME = ".pmf_run.json"

MESH_WORKFLOW_EXECUTABLES = {
    "blockMesh": "blockMesh",
    "cartesian2DMesh": "cartesian2DMesh",
}

_RUN_PROCESSES: dict[int, subprocess.Popen] = {}


@dataclass(frozen=True)
class PreflightIssue:
    code: str
    message: str
    blocking: bool = True


@dataclass(frozen=True)
class PreflightReport:
    issues: tuple[PreflightIssue, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return not any(issue.blocking for issue in self.issues)

    @property
    def blocking_issues(self) -> tuple[PreflightIssue, ...]:
        return tuple(issue for issue in self.issues if issue.blocking)


def default_run_state() -> dict[str, Any]:
    return {
        "status": "idle",
        "pid": None,
        "log_path": None,
        "return_code": None,
        "last_command": None,
        "started_at": None,
    }


def get_foam_run_path(env: Mapping[str, str] | None = None) -> Path | None:
    env = env or os.environ
    foam_run = env.get("FOAM_RUN")
    if not foam_run:
        return None

    candidate = Path(os.path.expanduser(foam_run))
    if candidate.exists() and candidate.is_dir():
        return candidate
    return None


def get_foam_run_report(env: Mapping[str, str] | None = None) -> PreflightReport:
    env = env or os.environ
    foam_run = env.get("FOAM_RUN")
    if not foam_run:
        return PreflightReport(
            issues=(
                PreflightIssue(
                    code="foam_run_missing",
                    message="FOAM_RUN is not set in the current shell environment.",
                ),
            )
        )

    candidate = Path(os.path.expanduser(foam_run))
    if not candidate.exists() or not candidate.is_dir():
        return PreflightReport(
            issues=(
                PreflightIssue(
                    code="foam_run_invalid",
                    message=f"FOAM_RUN points to a missing directory: {candidate}",
                ),
            )
        )

    return PreflightReport(details={"foam_run_path": candidate})


def collect_missing_paths(case_dir: Path | str, keys: list[str]) -> list[Path]:
    base = Path(case_dir)
    missing: list[Path] = []
    for key in keys:
        relative_path = PATHS.get(key)
        if relative_path is None:
            continue
        file_path = base / relative_path
        if not file_path.exists():
            missing.append(file_path)
    return missing


def load_cell_zones(case_dir: Path | str) -> dict[str, dict[str, Any]]:
    cell_zone_path = case_path(case_dir, "cellZones")
    if not cell_zone_path.exists():
        return {}

    content = cell_zone_path.read_text(encoding="utf-8")
    match = re.search(r"FoamFile\s*\{.*?\}\s*(.*)", content, re.DOTALL)
    if not match:
        return {}

    cell_zones: dict[str, dict[str, Any]] = {}
    for zone_name in re.findall(r"(\w+)\s*\{", match.group(1)):
        cell_zones[zone_name] = {"type": None, "parameters": {}}
    return cell_zones


def has_mesh(case_dir: Path | str) -> bool:
    return case_path(case_dir, "boundary").exists()


def detect_solver_type(case_dir: Path | str) -> str | None:
    physics_path = case_path(case_dir, "physicsProperties")
    if not physics_path.exists():
        return None

    physics_properties = FoamFile(physics_path).as_dict()
    solver_key = str(physics_properties.get("type"))
    return SOLVER_TYPE_MAP.get(solver_key)


def required_field_paths(case_dir: Path | str, solver_type: str | None = None) -> list[Path]:
    solver_type = solver_type or detect_solver_type(case_dir)
    if solver_type is None:
        return []

    fields = SOLVER_OPTIONS[solver_type]["fields"]
    base = Path(case_dir)
    return [base / "0" / FIELD_REGIONS[field_name] / field_name for field_name in fields]


def get_control_dict_application(case_dir: Path | str) -> str | None:
    control_dict_path = Path(case_dir) / "system" / "controlDict"
    if not control_dict_path.exists():
        return None

    control_dict = FoamFile(control_dict_path).as_dict()
    application = control_dict.get("application")
    if application is None:
        return None

    return str(application).strip()


def derive_launch_command(case_dir: Path | str) -> list[str]:
    application = get_control_dict_application(case_dir)
    if not application:
        raise ValueError("controlDict.application is missing")
    return [application]


def resolve_executable(command: str) -> str | None:
    return shutil.which(command)


def get_mesh_workflow_report(case_dir: Path | str | None, workflow: str) -> PreflightReport:
    issues: list[PreflightIssue] = []
    details: dict[str, Any] = {}

    if case_dir is None:
        issues.append(
            PreflightIssue(
                code="case_missing",
                message="Select a case before using mesh actions.",
            )
        )
        return PreflightReport(issues=tuple(issues), details=details)

    case_path_value = Path(case_dir)
    if not case_path_value.exists():
        issues.append(
            PreflightIssue(
                code="case_path_missing",
                message=f"Selected case does not exist: {case_path_value}",
            )
        )
        return PreflightReport(issues=tuple(issues), details=details)

    executable = MESH_WORKFLOW_EXECUTABLES.get(workflow)
    if executable:
        resolved = resolve_executable(executable)
        details["executable"] = executable
        details["resolved_executable"] = resolved
        if resolved is None:
            issues.append(
                PreflightIssue(
                    code=f"{workflow}_missing",
                    message=f"Required executable '{executable}' is not available on PATH.",
                )
            )

    if workflow == "cartesian2DMesh":
        mesh_dict_path = case_path_value / "system" / "meshDict"
        details["mesh_dict_path"] = mesh_dict_path
        if not mesh_dict_path.exists():
            issues.append(
                PreflightIssue(
                    code="mesh_dict_missing",
                    message=f"Required meshDict file is missing: {mesh_dict_path}",
                )
            )

    return PreflightReport(issues=tuple(issues), details=details)


def get_run_preflight_report(case_dir: Path | str | None, solver_type: str | None = None) -> PreflightReport:
    issues: list[PreflightIssue] = []
    details: dict[str, Any] = {}

    if case_dir is None:
        issues.append(
            PreflightIssue(
                code="case_missing",
                message="Select a case before launching a solver.",
            )
        )
        return PreflightReport(issues=tuple(issues), details=details)

    case_path_value = Path(case_dir)
    if not case_path_value.exists():
        issues.append(
            PreflightIssue(
                code="case_path_missing",
                message=f"Selected case does not exist: {case_path_value}",
            )
        )
        return PreflightReport(issues=tuple(issues), details=details)

    if not has_mesh(case_path_value):
        issues.append(
            PreflightIssue(
                code="mesh_missing",
                message="The selected case has no mesh yet.",
            )
        )

    solver_type = solver_type or detect_solver_type(case_path_value)
    details["solver_type"] = solver_type
    if solver_type is None:
        issues.append(
            PreflightIssue(
                code="solver_unknown",
                message="Could not infer the solver type from constant/physicsProperties.",
            )
        )
    else:
        missing_fields = [field_path for field_path in required_field_paths(case_path_value, solver_type) if not field_path.exists()]
        if missing_fields:
            joined_paths = ", ".join(str(field_path) for field_path in missing_fields)
            issues.append(
                PreflightIssue(
                    code="field_files_missing",
                    message=f"Required field files are missing: {joined_paths}",
                )
            )
        details["required_field_paths"] = required_field_paths(case_path_value, solver_type)

    control_dict_path = case_path_value / "system" / "controlDict"
    details["control_dict_path"] = control_dict_path
    if not control_dict_path.exists():
        issues.append(
            PreflightIssue(
                code="control_dict_missing",
                message=f"Run settings file is missing: {control_dict_path}",
            )
        )
        return PreflightReport(issues=tuple(issues), details=details)

    application = get_control_dict_application(case_path_value)
    details["application"] = application
    if not application:
        issues.append(
            PreflightIssue(
                code="application_missing",
                message="system/controlDict does not define an application entry.",
            )
        )
        return PreflightReport(issues=tuple(issues), details=details)

    resolved = resolve_executable(application)
    details["resolved_application"] = resolved
    if resolved is None:
        issues.append(
            PreflightIssue(
                code="application_not_found",
                message=f"The solver executable '{application}' is not available on PATH.",
            )
        )

    return PreflightReport(issues=tuple(issues), details=details)


def run_metadata_path(case_dir: Path | str) -> Path:
    return Path(case_dir) / RUN_METADATA_NAME


def run_log_path(case_dir: Path | str) -> Path:
    return Path(case_dir) / RUN_LOG_NAME


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_run_metadata(case_dir: Path | str) -> dict[str, Any]:
    metadata_path = run_metadata_path(case_dir)
    if not metadata_path.exists():
        return default_run_state()

    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default_run_state()

    state = default_run_state()
    for key, value in data.items():
        if key in state:
            state[key] = value
    return state


def save_run_metadata(case_dir: Path | str, state: dict[str, Any]) -> dict[str, Any]:
    normalized = default_run_state()
    normalized.update({key: value for key, value in state.items() if key in normalized})
    normalized["log_path"] = str(run_log_path(case_dir))
    _write_json(run_metadata_path(case_dir), normalized)
    return normalized


def process_is_alive(pid: int | None) -> bool:
    if pid in (None, 0):
        return False

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _reap_process(pid: int) -> int | None:
    try:
        waited_pid, status = os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return None

    if waited_pid == 0:
        return None
    return os.waitstatus_to_exitcode(status)


def sync_run_metadata(case_dir: Path | str) -> dict[str, Any]:
    case_path_value = Path(case_dir)
    state = load_run_metadata(case_path_value)
    pid = state.get("pid")

    if pid is None:
        return state

    tracked_process = _RUN_PROCESSES.get(pid)
    if tracked_process is not None:
        return_code = tracked_process.poll()
        if return_code is None:
            if state.get("status") != "running":
                state["status"] = "running"
                return save_run_metadata(case_path_value, state)
            return state

        _RUN_PROCESSES.pop(pid, None)
        state["return_code"] = return_code
        if return_code == 0:
            state["status"] = "completed"
        else:
            state["status"] = "failed"
        return save_run_metadata(case_path_value, state)

    return_code = _reap_process(pid)
    if return_code is not None:
        state["return_code"] = return_code
        if return_code == 0:
            state["status"] = "completed"
        else:
            state["status"] = "failed"
        return save_run_metadata(case_path_value, state)

    if process_is_alive(pid):
        if state.get("status") != "running":
            state["status"] = "running"
            return save_run_metadata(case_path_value, state)
        return state

    if state.get("return_code") is None:
        state["status"] = "finished"
    elif state["return_code"] == 0:
        state["status"] = "completed"
    else:
        state["status"] = "failed"

    return save_run_metadata(case_path_value, state)


def start_case_run(case_dir: Path | str) -> dict[str, Any]:
    case_path_value = Path(case_dir)
    preflight = get_run_preflight_report(case_path_value)
    if not preflight.ready:
        message = "\n".join(issue.message for issue in preflight.blocking_issues)
        raise RuntimeError(message)

    current_state = sync_run_metadata(case_path_value)
    if current_state.get("status") == "running" and process_is_alive(current_state.get("pid")):
        raise RuntimeError("A solver is already running for this case")

    command = derive_launch_command(case_path_value)
    log_path = run_log_path(case_path_value)
    started_at = datetime.now(timezone.utc).isoformat()

    with log_path.open("w", encoding="utf-8") as log_handle:
        process = subprocess.Popen(
            command,
            cwd=case_path_value,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    state = {
        "status": "running",
        "pid": process.pid,
        "log_path": str(log_path),
        "return_code": None,
        "last_command": " ".join(command),
        "started_at": started_at,
    }
    _RUN_PROCESSES[process.pid] = process
    return save_run_metadata(case_path_value, state)


def _wait_for_exit(pid: int, timeout_seconds: float) -> int | None:
    tracked_process = _RUN_PROCESSES.get(pid)
    if tracked_process is not None:
        try:
            return tracked_process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            return None

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        return_code = _reap_process(pid)
        if return_code is not None:
            return return_code
        if not process_is_alive(pid):
            return None
        time.sleep(0.1)

    return _reap_process(pid)


def stop_case_run(case_dir: Path | str, timeout_seconds: float = 5.0) -> dict[str, Any]:
    case_path_value = Path(case_dir)
    state = sync_run_metadata(case_path_value)
    pid = state.get("pid")

    if pid is None or not process_is_alive(pid):
        return state

    tracked_process = _RUN_PROCESSES.get(pid)
    if tracked_process is not None:
        tracked_process.terminate()
    else:
        os.kill(pid, signal.SIGTERM)

    return_code = _wait_for_exit(pid, timeout_seconds)

    if process_is_alive(pid):
        if tracked_process is not None:
            tracked_process.kill()
        else:
            os.kill(pid, signal.SIGKILL)
        return_code = _wait_for_exit(pid, 1.0)

    _RUN_PROCESSES.pop(pid, None)
    state["return_code"] = return_code
    state["status"] = "stopped"
    return save_run_metadata(case_path_value, state)


def tail_run_log(log_path: Path | str | None, max_lines: int = 80) -> str:
    if log_path is None:
        return ""

    path = Path(log_path)
    if not path.exists():
        return ""

    lines: deque[str] = deque(maxlen=max_lines)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            lines.append(line.rstrip("\n"))

    return "\n".join(lines)


def list_time_directories(case_dir: Path | str) -> list[str]:
    case_path_value = Path(case_dir)
    if not case_path_value.exists():
        return []

    time_dirs: list[tuple[float, str]] = []
    for child in case_path_value.iterdir():
        if not child.is_dir():
            continue
        try:
            sort_value = float(child.name)
        except ValueError:
            continue
        time_dirs.append((sort_value, child.name))

    time_dirs.sort()
    return [name for _, name in time_dirs]


def get_post_processing_path(case_dir: Path | str) -> Path:
    return Path(case_dir) / "postProcessing"
