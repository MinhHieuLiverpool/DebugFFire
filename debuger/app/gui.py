import json
import os
import queue
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from player_tracker import follow_lines, parse_add_player_line


class PlayerTrackerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FreeFire InitTrackingPlayer")
        self.root.geometry("1920x1080")
        self._sash_ratio = 0.3
        self._panes: tk.PanedWindow | None = None

        self.path_var = tk.StringVar()
        self.poll_var = tk.StringVar(value="0.2")
        self.status_var = tk.StringVar(value="Idle")
        self.config_count_var = tk.StringVar(value="Configs: 0")
        self.overwrite_count_var = tk.StringVar(value="Overwrites: 0")
        self.banner_var = tk.StringVar(value="")

        self.log_init_var = tk.BooleanVar(value=True)
        self.log_add_var = tk.BooleanVar(value=True)
        self.log_join_var = tk.BooleanVar(value=True)
        self.log_dead_var = tk.BooleanVar(value=True)
        self.log_match_var = tk.BooleanVar(value=True)

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._config_by_name: dict[str, int] = {}
        self._name_by_id: dict[int, str] = {}
        self._overwrite_count = 0
        self._total_configs = 0
        self._last_kill: tuple[int, int] | None = None

        self._timestamp_pattern = re.compile(r"^\[(\d{4}-\d{2}-\d{2}[^\]]+)\]")
        self._init_tracking_pattern = re.compile(
            r"\[InitTrackingPlayer\]\s+(\d+)\s+->\s+(\S+)"
        )
        self._player_join_pattern = re.compile(
            r"Player\s+Join,\s+\d+,\s*(\d+),\s*([^,\s]+)"
        )
        self._player_dead_pattern = re.compile(
            r"Player\s+(\d+)\s+Dead,\s+killed\s+by\s+(\d+)"
        )
        self._match_last_kill_pattern = re.compile(
            r"@zwt,\s+isMatchLastKill:\s+(True|False)"
        )

        self._build_ui()
        self._schedule_queue_pump()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        header = tk.Frame(self.root)
        header.pack(fill="x", padx=10, pady=8)

        path_label = tk.Label(header, text="Log file:")
        path_label.pack(anchor="w")

        banner_label = tk.Label(header, textvariable=self.banner_var, fg="green")
        banner_label.pack(anchor="e")

        path_row = tk.Frame(header)
        path_row.pack(fill="x", pady=4)

        path_entry = tk.Entry(path_row, textvariable=self.path_var)
        path_entry.pack(side="left", fill="x", expand=True)

        browse_button = tk.Button(path_row, text="Browse", command=self.browse_file)
        browse_button.pack(side="left", padx=6)

        options_row = tk.Frame(header)
        options_row.pack(fill="x", pady=4)

        poll_label = tk.Label(options_row, text="Poll (sec):")
        poll_label.pack(side="left")

        poll_entry = tk.Entry(options_row, width=8, textvariable=self.poll_var)
        poll_entry.pack(side="left", padx=6)

        self.start_button = tk.Button(options_row, text="Start", command=self.start_tracking)
        self.start_button.pack(side="left", padx=6)

        self.stop_button = tk.Button(options_row, text="Stop", command=self.stop_tracking, state="disabled")
        self.stop_button.pack(side="left")

        status_row = tk.Frame(self.root)
        status_row.pack(fill="x", padx=10)

        status_label = tk.Label(status_row, textvariable=self.status_var, anchor="w")
        status_label.pack(fill="x")

        panes = tk.PanedWindow(self.root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=10, pady=8)
        self._panes = panes

        config_frame = tk.Frame(panes)
        logs_frame = tk.Frame(panes)
        panes.add(config_frame, stretch="always")
        panes.add(logs_frame, stretch="always")

        config_label = tk.Label(config_frame, text="Config")
        config_label.pack(anchor="w")

        config_count = tk.Label(config_frame, textvariable=self.config_count_var, anchor="w")
        config_count.pack(anchor="w")

        overwrite_count = tk.Label(config_frame, textvariable=self.overwrite_count_var, anchor="w")
        overwrite_count.pack(anchor="w")

        config_list_frame = tk.Frame(config_frame)
        config_list_frame.pack(fill="both", expand=True)

        self.config_listbox = tk.Listbox(config_list_frame)
        self.config_listbox.pack(side="left", fill="both", expand=True)

        config_scrollbar = tk.Scrollbar(config_list_frame, command=self.config_listbox.yview)
        config_scrollbar.pack(side="right", fill="y")
        self.config_listbox.configure(yscrollcommand=config_scrollbar.set)

        logs_label = tk.Label(logs_frame, text="Logs")
        logs_label.pack(anchor="w")

        logs_filters = tk.Frame(logs_frame)
        logs_filters.pack(anchor="w", pady=4)

        init_check = tk.Checkbutton(logs_filters, text="InitTrackingPlayer", variable=self.log_init_var)
        init_check.pack(side="left", padx=4)

        add_check = tk.Checkbutton(logs_filters, text="AddPlayer", variable=self.log_add_var)
        add_check.pack(side="left", padx=4)

        join_check = tk.Checkbutton(logs_filters, text="Player Join", variable=self.log_join_var)
        join_check.pack(side="left", padx=4)

        dead_check = tk.Checkbutton(logs_filters, text="Player Dead", variable=self.log_dead_var)
        dead_check.pack(side="left", padx=4)

        match_check = tk.Checkbutton(logs_filters, text="Match End", variable=self.log_match_var)
        match_check.pack(side="left", padx=4)

        logs_list_frame = tk.Frame(logs_frame)
        logs_list_frame.pack(fill="both", expand=True)

        self.logs_listbox = tk.Listbox(logs_list_frame)
        self.logs_listbox.pack(side="left", fill="both", expand=True)

        logs_scrollbar = tk.Scrollbar(logs_list_frame, command=self.logs_listbox.yview)
        logs_scrollbar.pack(side="right", fill="y")
        self.logs_listbox.configure(yscrollcommand=logs_scrollbar.set)

        self.root.after(150, self._set_initial_sash)

    def _set_initial_sash(self) -> None:
        if not self._panes:
            return
        self.root.update_idletasks()
        total_width = self._panes.winfo_width()
        if total_width <= 1:
            self.root.after(150, self._set_initial_sash)
            return
        sash_x = int(total_width * self._sash_ratio)
        self._panes.sash_place(0, sash_x, 0)

    def browse_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select debug log",
            filetypes=[("Log files", "*.log"), ("All files", "*")],
        )
        if path:
            self.path_var.set(path)

    def start_tracking(self) -> None:
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("Missing path", "Please select a log file.")
            return
        if not os.path.isfile(path):
            messagebox.showerror("Invalid file", f"File not found: {path}")
            return

        try:
            poll_interval = float(self.poll_var.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid poll", "Poll must be a number.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_tracking,
            args=(path, poll_interval),
            daemon=True,
        )
        self._thread.start()

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("Tracking...")

    def stop_tracking(self) -> None:
        self._stop_event.set()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_var.set("Stopped")

    def _run_tracking(self, path: str, poll_interval: float) -> None:
        for line in follow_lines(path, poll_interval=poll_interval):
            if self._stop_event.is_set():
                break
            parsed = parse_add_player_line(line)
            if parsed:
                player_id, name = parsed
                self._queue.put(("config", (player_id, name)))
                if self.log_add_var.get():
                    message = self._format_add_player(line, player_id, name)
                    if message:
                        self._queue.put(("log", message))

            init_match = self._init_tracking_pattern.search(line)
            if init_match and self.log_init_var.get():
                player_id = int(init_match.group(1))
                name = init_match.group(2)
                message = self._format_tracking(line, player_id, name)
                if message:
                    self._queue.put(("log", message))

            join_match = self._player_join_pattern.search(line)
            if join_match and self.log_join_var.get():
                player_id = int(join_match.group(1))
                name = join_match.group(2)
                message = self._format_player_join(line, player_id, name)
                if message:
                    self._queue.put(("log", message))

            dead_match = self._player_dead_pattern.search(line)
            if dead_match and self.log_dead_var.get():
                victim_id = int(dead_match.group(1))
                killer_id = int(dead_match.group(2))
                self._last_kill = (victim_id, killer_id)
                message = self._format_player_dead(line, victim_id, killer_id)
                if message:
                    self._queue.put(("log", message))

            match_last_kill = self._match_last_kill_pattern.search(line)
            if match_last_kill and self.log_match_var.get():
                is_last_kill = match_last_kill.group(1) == "True"
                message = self._format_match_state(line, is_last_kill)
                if message:
                    self._queue.put(("log", message))
                banner = self._format_match_banner(is_last_kill)
                if banner:
                    self._queue.put(("banner", banner))

    def _schedule_queue_pump(self) -> None:
        self._pump_queue()
        self.root.after(100, self._schedule_queue_pump)

    def _pump_queue(self) -> None:
        while True:
            try:
                target, text = self._queue.get_nowait()
            except queue.Empty:
                break
            if target == "config":
                player_id, name = text
                self._upsert_config(player_id, name)
            elif target == "banner":
                self.banner_var.set(text)
            else:
                self.logs_listbox.insert("end", text)
                self.logs_listbox.see("end")

    def _upsert_config(self, player_id: int, name: str) -> None:
        overwritten = False
        is_new = name not in self._config_by_name and player_id not in self._name_by_id
        old_id = self._config_by_name.get(name)
        if old_id is not None and old_id != player_id:
            self._name_by_id.pop(old_id, None)
            overwritten = True

        old_name = self._name_by_id.get(player_id)
        if old_name is not None and old_name != name:
            self._config_by_name.pop(old_name, None)
            overwritten = True

        self._config_by_name[name] = player_id
        self._name_by_id[player_id] = name

        if overwritten:
            self._overwrite_count += 1

        if is_new:
            self._total_configs += 1

        self._refresh_config_list()

    def _refresh_config_list(self) -> None:
        self.config_listbox.delete(0, "end")
        for name, player_id in self._config_by_name.items():
            team = self._extract_team(name)
            payload = {"playerId": player_id, "name": name, "team": team}
            self.config_listbox.insert("end", json.dumps(payload, ensure_ascii=True))
        self.config_listbox.see("end")
        self.config_count_var.set(f"Configs: {self._total_configs}")
        self.overwrite_count_var.set(f"Overwrites: {self._overwrite_count}")

    def _extract_team(self, name: str) -> str:
        if "." in name:
            return name.split(".", 1)[0]
        return ""

    def _extract_timestamp(self, line: str) -> str:
        match = self._timestamp_pattern.match(line)
        if match:
            return match.group(1)
        return ""

    def _format_add_player(self, line: str, player_id: int, name: str) -> str:
        timestamp = self._extract_timestamp(line)
        team = self._extract_team(name)
        if timestamp:
            return f"[{timestamp}] Add PlayerID: {player_id}, PlayerName: {name}, Team: {team}"
        return f"Add PlayerID: {player_id}, PlayerName: {name}, Team: {team}"

    def _format_tracking(self, line: str, player_id: int, name: str) -> str:
        timestamp = self._extract_timestamp(line)
        team = self._extract_team(name)
        if timestamp:
            return f"[{timestamp}] Tracking PlayerID: {player_id}, Name: {name}, Team: {team}"
        return f"Tracking PlayerID: {player_id}, Name: {name}, Team: {team}"

    def _format_player_join(self, line: str, player_id: int, name: str) -> str:
        timestamp = self._extract_timestamp(line)
        team = self._extract_team(name)
        if timestamp:
            return f"[{timestamp}] Player Join PlayerID: {player_id}, Name: {name}, Team: {team}"
        return f"Player Join PlayerID: {player_id}, Name: {name}, Team: {team}"

    def _format_player_dead(self, line: str, victim_id: int, killer_id: int) -> str:
        timestamp = self._extract_timestamp(line)
        victim_name = self._name_by_id.get(victim_id, "Unknown")
        killer_name = self._name_by_id.get(killer_id, "Unknown")
        if timestamp:
            return f"[{timestamp}] {victim_name} KILLED BY {killer_name}"
        return f"{victim_name} KILLED BY {killer_name}"

    def _format_match_state(self, line: str, is_last_kill: bool) -> str:
        timestamp = self._extract_timestamp(line)
        if not is_last_kill:
            if timestamp:
                return f"[{timestamp}] Match Pending..."
            return "Match Pending..."

        team = "Unknown"
        killer_name = "Unknown"
        if self._last_kill:
            _, killer_id = self._last_kill
            killer_name = self._name_by_id.get(killer_id, "Unknown")
            if killer_name != "Unknown":
                team = self._extract_team(killer_name) or "Unknown"

        if timestamp:
            return f"[{timestamp}] BOOYAH - Team: {team} (Killer: {killer_name})"
        return f"BOOYAH - Team: {team} (Killer: {killer_name})"

    def _format_match_banner(self, is_last_kill: bool) -> str:
        if not is_last_kill:
            return "PENDING..."

        team = "Unknown"
        if self._last_kill:
            _, killer_id = self._last_kill
            killer_name = self._name_by_id.get(killer_id, "Unknown")
            if killer_name != "Unknown":
                team = self._extract_team(killer_name) or "Unknown"

        return f"BOOYAH - TEAM: {team}"

    def on_close(self) -> None:
        self._stop_event.set()
        self.root.destroy()


def main() -> int:
    root = tk.Tk()
    app = PlayerTrackerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
