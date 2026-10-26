"""Ejecuta el binario desde otra carpeta y sin referencias al entorno Python local."""

import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def normal_start(executable, isolated, environment, system):
    """Arranque sin flags y cierre por WM_CLOSE, solo sobre el proceso lanzado y su hijo."""
    with subprocess.Popen([str(executable)], cwd=isolated, env=environment) as process:
        script = (
            "$taskRootPid = "
            + str(process.pid)
            + "\n"
            + r"""
$taskDeadline = (Get-Date).AddSeconds(45)
while ((Get-Date) -lt $taskDeadline) {
    $taskChildren = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$taskRootPid" |
        Select-Object -ExpandProperty ProcessId)
    $taskIds = @($taskRootPid) + $taskChildren
    foreach ($taskId in $taskIds) {
        $taskWindow = Get-Process -Id $taskId -ErrorAction SilentlyContinue
        if ($taskWindow -and $taskWindow.MainWindowTitle -eq 'VaultLab — Matemática Aplicada') {
            if ($taskWindow.CloseMainWindow()) { exit 0 }
        }
    }
    Start-Sleep -Milliseconds 250
}
exit 1
"""
        )
        powershell = system / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        checked = subprocess.run(
            [str(powershell), "-NoProfile", "-Command", script],
            env=environment,
            capture_output=True,
            timeout=60,
        )
        if checked.returncode != 0:
            subprocess.run(
                [str(system / "System32" / "taskkill.exe"), "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                check=False,
            )
            raise SystemExit("No se pudo comprobar la ventana del arranque normal.")
        assert process.wait(timeout=20) == 0
    assert (Path(environment["LOCALAPPDATA"]) / "VaultLab").is_dir()


def main():
    executable = ROOT / "dist" / "VaultLab.exe"
    work = ROOT / ".tmp"
    work.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="exe-check-", dir=work) as directory:
        isolated = Path(directory)
        runtime_temp = isolated / "temp"
        profile = isolated / "profile"
        runtime_temp.mkdir()
        profile.mkdir()
        report = isolated / "result.json"
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.upper().startswith(("PYTHON", "TCL", "TK_", "_PYI_"))
            and key.upper() not in {"VIRTUAL_ENV", "CONDA_PREFIX"}
        }
        system = Path(os.environ["SystemRoot"])
        environment.update(
            PATH=os.pathsep.join((str(system / "System32"), str(system))),
            LOCALAPPDATA=str(profile),
            TEMP=str(runtime_temp),
            TMP=str(runtime_temp),
        )
        with subprocess.Popen(
            [str(executable), "--self-test", str(report)], cwd=isolated, env=environment
        ) as process:
            try:
                code = process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                subprocess.run(
                    [
                        str(system / "System32" / "taskkill.exe"),
                        "/PID",
                        str(process.pid),
                        "/T",
                        "/F",
                    ],
                    check=False,
                    capture_output=True,
                )
                raise SystemExit("La comprobación del ejecutable excedió el plazo.") from None
        if not report.exists():
            raise SystemExit("El ejecutable no produjo el informe de comprobación.")
        result = json.loads(report.read_text(encoding="utf-8"))
        result.update(
            exit_code=code,
            isolated_cwd=True,
            python_environment_removed=True,
            python_not_on_path=True,
        )
        output = ROOT / "docs" / "evidence" / "exe-smoke.json"
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        if code != 0 or not result.get("ok") or not result.get("frozen"):
            raise SystemExit("Falló la comprobación del ejecutable. Revisar exe-smoke.json.")
        normal_start(executable, isolated, environment, system)
        result.update(
            normal_double_click_start=True,
            native_window_close=True,
            default_data_directory_created=True,
        )
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("Ejecutable verificado: GUI, recursos, cifrado, reapertura, errores y laboratorio.")


if __name__ == "__main__":
    main()
