import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print(" ".join(cmd))
    subprocess.check_call(cmd)


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except Exception:
        print("PyInstaller chua duoc cai. Dang cai...")
        run([sys.executable, "-m", "pip", "install", "pyinstaller"])


def make_shortcut(
    shortcut_path: Path,
    target_path: Path,
    work_dir: Path,
    relative: bool = False,
) -> None:
    # Use PowerShell COM to create a .lnk shortcut.
    target = target_path.name if relative else str(target_path)
    working_dir = "." if relative else str(work_dir)
    ps = (
        "$WshShell = New-Object -ComObject WScript.Shell; "
        f"$Shortcut = $WshShell.CreateShortcut('{shortcut_path}'); "
        f"$Shortcut.TargetPath = '{target}'; "
        f"$Shortcut.WorkingDirectory = '{working_dir}'; "
        "$Shortcut.Save();"
    )
    run(["powershell", "-NoProfile", "-Command", ps])


def find_7z() -> Path | None:
    exe = shutil.which("7z") or shutil.which("7z.exe")
    if exe:
        return Path(exe)

    candidates = [
        Path(os.environ.get("ProgramFiles", "")) / "7-Zip" / "7z.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "7-Zip" / "7z.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def create_sfx(dist_dir: Path, sfx_out: Path, title: str) -> None:
    seven_zip = find_7z()
    if not seven_zip:
        raise FileNotFoundError(
            "Khong tim thay 7z.exe. Hay cai 7-Zip truoc."
        )

    sfx_module = seven_zip.parent / "7z.sfx"
    if not sfx_module.exists():
        raise FileNotFoundError(
            f"Khong tim thay 7z.sfx tai: {sfx_module}"
        )

    archive_path = dist_dir.parent / f"{sfx_out.stem}.7z"
    if archive_path.exists():
        archive_path.unlink()

    run([
        str(seven_zip),
        "a",
        "-t7z",
        str(archive_path),
        str(dist_dir / "*"),
    ])

    # 7-Zip SFX config. Default GUI will ask for extract location.
    config_text = (
        ";!@Install@!UTF-8!\n"
        f"Title=\"{title}\"\n"
        ";!@Install@!UTF-8!\n"
    )

    config_path = dist_dir.parent / f"{sfx_out.stem}.sfx.txt"
    config_path.write_text(config_text, encoding="utf-8")

    if sfx_out.exists():
        sfx_out.unlink()

    with open(sfx_out, "wb") as out_fh:
        for path in (sfx_module, config_path, archive_path):
            with open(path, "rb") as in_fh:
                shutil.copyfileobj(in_fh, out_fh)

    archive_path.unlink(missing_ok=True)
    config_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--entry",
        default=str(Path("app") / "main.py"),
        help="Duong dan file main.py trong folder app",
    )
    parser.add_argument(
        "--name",
        default="app",
        help="Ten file exe",
    )
    parser.add_argument(
        "--dist",
        default="dist",
        help="Thu muc output",
    )
    parser.add_argument(
        "--sfx",
        action="store_true",
        help="Tao file SFX .exe tu giai nen",
    )
    parser.add_argument(
        "--sfx-out",
        default="",
        help="Duong dan file SFX output (mac dinh: <name>_sfx.exe)",
    )
    args = parser.parse_args()

    entry = Path(args.entry).resolve()
    if not entry.exists():
        print(f"Khong tim thay entry: {entry}")
        return 1

    ensure_pyinstaller()

    project_root = entry.parent.parent.resolve()
    dist_dir = Path(args.dist).resolve()
    build_dir = project_root / "build"
    spec_path = project_root / f"{args.name}.spec"

    # Clean old outputs to avoid stale artifacts.
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if spec_path.exists():
        spec_path.unlink()

    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--noconsole",
            "--name",
            args.name,
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(build_dir),
            str(entry),
        ]
    )

    exe_path = dist_dir / f"{args.name}.exe"
    if not exe_path.exists():
        print(f"Khong tim thay exe: {exe_path}")
        return 1

    # Create shortcut next to the exe (relative for portability).
    shortcut_path = dist_dir / f"{args.name}.lnk"
    make_shortcut(shortcut_path, exe_path, dist_dir, relative=True)

    print(f"Da build xong: {exe_path}")
    print(f"Shortcut: {shortcut_path}")

    if args.sfx:
        sfx_out = (
            Path(args.sfx_out).resolve()
            if args.sfx_out
            else dist_dir.parent / f"{args.name}_sfx.exe"
        )
        create_sfx(dist_dir, sfx_out, title=args.name)
        print(f"SFX: {sfx_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
