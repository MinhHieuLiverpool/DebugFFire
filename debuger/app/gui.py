import json
import os
import queue
import re
import threading
import tkinter as tk
import urllib.error
import urllib.request
from tkinter import filedialog, messagebox
from tkinter import ttk

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
        self.companion_ip_var = tk.StringVar(value="127.0.0.1:8000")
        self._companion_map_path = os.path.join(
            os.path.dirname(__file__),
            "companion_map.json",
        )
        self._companion_map: dict[str, dict[str, tuple[int, int, int]]] = {
            "team": {},
            "player": {},
            "booyah": {},
        }

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
        self._team_last_kill_pattern = re.compile(
            r"isTeamLastKill:\s+(True|False)"
        )

        self._build_ui()
        self._load_companion_map()
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

        companion_label = tk.Label(options_row, text="Companion IP:")
        companion_label.pack(side="left", padx=(8, 0))

        companion_entry = tk.Entry(options_row, width=20, textvariable=self.companion_ip_var)
        companion_entry.pack(side="left", padx=6)

        self.start_button = tk.Button(options_row, text="Start", command=self.start_tracking)
        self.start_button.pack(side="left", padx=6)

        self.stop_button = tk.Button(options_row, text="Stop", command=self.stop_tracking, state="disabled")
        self.stop_button.pack(side="left")

        config_button = tk.Button(options_row, text="Config Companion", command=self.open_companion_dialog)
        config_button.pack(side="left", padx=6)

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

        self.logs_text = tk.Text(logs_list_frame, wrap="none", height=20)
        self.logs_text.pack(side="left", fill="both", expand=True)
        self.logs_text.configure(state="disabled")

        self.logs_text.tag_configure("team", foreground="blue")
        self.logs_text.tag_configure("killer", foreground="darkgreen")
        self.logs_text.tag_configure("victim", foreground="darkred")

        logs_scrollbar = tk.Scrollbar(logs_list_frame, command=self.logs_text.yview)
        logs_scrollbar.pack(side="right", fill="y")
        self.logs_text.configure(yscrollcommand=logs_scrollbar.set)

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

    def _load_companion_map(self) -> None:
        if not os.path.isfile(self._companion_map_path):
            self._companion_map = {"team": {}, "player": {}, "booyah": {}}
            return

        try:
            with open(self._companion_map_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            self._companion_map = {}
            return

        self._companion_map = {"team": {}, "player": {}, "booyah": {}}
        if "team" in data or "player" in data or "booyah" in data:
            for section in ("team", "player", "booyah"):
                section_data = data.get(section, {})
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        if isinstance(value, list) and len(value) == 3:
                            self._companion_map[section][str(key)] = (
                                int(value[0]),
                                int(value[1]),
                                int(value[2]),
                            )
                        elif isinstance(value, str) and value.count("/") == 2:
                            parts = value.split("/")
                            self._companion_map[section][str(key)] = (
                                int(parts[0]),
                                int(parts[1]),
                                int(parts[2]),
                            )
        else:
            for key, value in data.items():
                if isinstance(value, list) and len(value) == 3:
                    self._companion_map["team"][str(key)] = (
                        int(value[0]),
                        int(value[1]),
                        int(value[2]),
                    )
                elif isinstance(value, str) and value.count("/") == 2:
                    parts = value.split("/")
                    self._companion_map["team"][str(key)] = (
                        int(parts[0]),
                        int(parts[1]),
                        int(parts[2]),
                    )

    def _save_companion_map(self) -> None:
        payload: dict[str, dict[str, list[int]]] = {
            "team": {},
            "player": {},
            "booyah": {},
        }
        for section, items in self._companion_map.items():
            for key, value in items.items():
                payload[section][key] = [value[0], value[1], value[2]]

        with open(self._companion_map_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=4, ensure_ascii=True)

    def open_companion_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Companion Map")
        dialog.geometry("520x420")

        info_row = tk.Frame(dialog)
        info_row.pack(fill="x", padx=10, pady=(10, 4))

        info = tk.Label(
            info_row,
            text="Nhap map theo tung nhom (Team / Player / Booyah).",
            anchor="w",
        )
        info.pack(side="left", fill="x", expand=True)

        notebook = ttk.Notebook(dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=6)

        team_text = tk.Text(notebook, wrap="none")
        player_text = tk.Text(notebook, wrap="none")
        booyah_text = tk.Text(notebook, wrap="none")

        notebook.add(team_text, text="Team")
        notebook.add(player_text, text="Player")
        notebook.add(booyah_text, text="Booyah")

        team_payload = {
            k: f"{v[0]}/{v[1]}/{v[2]}" for k, v in self._companion_map.get("team", {}).items()
        }
        player_payload = {
            k: f"{v[0]}/{v[1]}/{v[2]}" for k, v in self._companion_map.get("player", {}).items()
        }
        booyah_payload = {
            k: f"{v[0]}/{v[1]}/{v[2]}" for k, v in self._companion_map.get("booyah", {}).items()
        }

        if not team_payload and not player_payload and not booyah_payload:
            team_payload = {
                "HEV": "1/0/0",
                "WAG": "1/0/3",
            }
            player_payload = {
                "HEV.ALAN": "1/0/1",
            }
            booyah_payload = {
                "BOOYAH WAG": "1/0/2",
            }

        team_text.insert("1.0", json.dumps(team_payload, indent=4, ensure_ascii=True))
        player_text.insert("1.0", json.dumps(player_payload, indent=4, ensure_ascii=True))
        booyah_text.insert("1.0", json.dumps(booyah_payload, indent=4, ensure_ascii=True))

        def on_save() -> None:
            raw_team = team_text.get("1.0", "end").strip()
            raw_player = player_text.get("1.0", "end").strip()
            raw_booyah = booyah_text.get("1.0", "end").strip()

            try:
                team_data = json.loads(raw_team) if raw_team else {}
                player_data = json.loads(raw_player) if raw_player else {}
                booyah_data = json.loads(raw_booyah) if raw_booyah else {}
            except json.JSONDecodeError:
                messagebox.showerror("Invalid JSON", "JSON khong hop le.")
                return

            def parse_section(section_data: dict, section_name: str) -> dict[str, tuple[int, int, int]]:
                result: dict[str, tuple[int, int, int]] = {}
                for key, value in section_data.items():
                    if not isinstance(value, str) or value.count("/") != 2:
                        messagebox.showerror("Invalid format", f"Gia tri khong hop le: {section_name}.{key}")
                        raise ValueError("Invalid format")
                    parts = value.split("/")
                    result[str(key)] = (int(parts[0]), int(parts[1]), int(parts[2]))
                return result

            try:
                new_team = parse_section(team_data, "team")
                new_player = parse_section(player_data, "player")
                new_booyah = parse_section(booyah_data, "booyah")
            except ValueError:
                return

            self._companion_map = {
                "team": new_team,
                "player": new_player,
                "booyah": new_booyah,
            }
            self._save_companion_map()
            dialog.destroy()

        save_button = tk.Button(info_row, text="Save", command=on_save)
        save_button.pack(side="right")

        cancel_button = tk.Button(info_row, text="Cancel", command=dialog.destroy)
        cancel_button.pack(side="right", padx=6)

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
                self._trigger_companion("player", name)
                if self.log_add_var.get():
                    message = self._format_add_player(line, player_id, name)
                    if message:
                        self._queue.put(("log", message))

            init_match = self._init_tracking_pattern.search(line)
            if init_match:
                player_id = int(init_match.group(1))
                name = init_match.group(2)
                team = self._extract_team(name)
                if team:
                    self._trigger_companion("team", team)
                self._trigger_companion("player", name)
                if self.log_init_var.get():
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

            team_last_kill = self._team_last_kill_pattern.search(line)
            if team_last_kill and self.log_match_var.get():
                is_team_last_kill = team_last_kill.group(1) == "True"
                message = self._format_team_cleared(line, is_team_last_kill)
                if message:
                    self._queue.put(("log", message))
                if is_team_last_kill:
                    cleared_team = self._get_last_victim_team()
                    if cleared_team:
                        self._trigger_companion("team", cleared_team)

            match_last_kill = self._match_last_kill_pattern.search(line)
            if match_last_kill and self.log_match_var.get():
                is_last_kill = match_last_kill.group(1) == "True"
                message = self._format_match_state(line, is_last_kill)
                if message:
                    self._queue.put(("log", message))
                banner = self._format_match_banner(is_last_kill)
                if banner:
                    self._queue.put(("banner", banner))
                if is_last_kill:
                    booyah_team = self._get_last_killer_team()
                    if booyah_team:
                        booyah_label = f"BOOYAH {booyah_team}"
                        self._trigger_companion("booyah", booyah_label)

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
                self._append_log(text)

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
            return ""

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
            return ""

        team = "Unknown"
        if self._last_kill:
            _, killer_id = self._last_kill
            killer_name = self._name_by_id.get(killer_id, "Unknown")
            if killer_name != "Unknown":
                team = self._extract_team(killer_name) or "Unknown"

        return f"BOOYAH - TEAM: {team}"

    def _append_log(self, text: str) -> None:
        self.logs_text.configure(state="normal")
        if " KILLED BY " in text:
            self._append_kill_log(text)
        else:
            self._append_generic_log(text)
        self.logs_text.configure(state="disabled")
        self.logs_text.see("end")

    def _append_generic_log(self, text: str) -> None:
        team_marker = "Team: "
        name_marker = "Name: "

        if team_marker not in text and name_marker not in text:
            self.logs_text.insert("end", text + "\n")
            return

        idx = 0
        while idx < len(text):
            if name_marker in text[idx:]:
                name_pos = text.find(name_marker, idx)
            else:
                name_pos = -1

            if team_marker in text[idx:]:
                team_pos = text.find(team_marker, idx)
            else:
                team_pos = -1

            next_pos = -1
            if name_pos != -1 and team_pos != -1:
                next_pos = min(name_pos, team_pos)
            elif name_pos != -1:
                next_pos = name_pos
            elif team_pos != -1:
                next_pos = team_pos

            if next_pos == -1:
                self.logs_text.insert("end", text[idx:])
                break

            self.logs_text.insert("end", text[idx:next_pos])
            if next_pos == name_pos:
                self.logs_text.insert("end", name_marker)
                value_start = next_pos + len(name_marker)
                value_end = text.find(",", value_start)
                if value_end == -1:
                    value_end = len(text)
                self.logs_text.insert("end", text[value_start:value_end], "killer")
                idx = value_end
            else:
                self.logs_text.insert("end", team_marker)
                value_start = next_pos + len(team_marker)
                value_end = text.find(",", value_start)
                if value_end == -1:
                    value_end = len(text)
                self.logs_text.insert("end", text[value_start:value_end], "team")
                idx = value_end

        self.logs_text.insert("end", "\n")

    def _append_kill_log(self, text: str) -> None:
        marker = " KILLED BY "
        marker_pos = text.find(marker)
        if marker_pos == -1:
            self.logs_text.insert("end", text + "\n")
            return

        left = text[:marker_pos]
        right = text[marker_pos + len(marker):]

        last_space = left.rfind(" ")
        if last_space == -1:
            self.logs_text.insert("end", left + marker)
            self.logs_text.insert("end", right, "killer")
            self.logs_text.insert("end", "\n")
            return

        prefix = left[: last_space + 1]
        victim = left[last_space + 1:]
        self.logs_text.insert("end", prefix)
        self.logs_text.insert("end", victim, "victim")
        self.logs_text.insert("end", marker)
        self.logs_text.insert("end", right, "killer")
        self.logs_text.insert("end", "\n")

    def _format_team_cleared(self, line: str, is_team_last_kill: bool) -> str:
        if not is_team_last_kill:
            return ""

        timestamp = self._extract_timestamp(line)
        team = self._get_last_victim_team() or "Unknown"

        if timestamp:
            return f"[{timestamp}] Team {team} CLEARED"
        return f"Team {team} CLEARED"

    def _get_last_victim_team(self) -> str:
        if not self._last_kill:
            return ""
        victim_id, _ = self._last_kill
        victim_name = self._name_by_id.get(victim_id, "Unknown")
        if victim_name == "Unknown":
            return ""
        return self._extract_team(victim_name)

    def _get_last_killer_team(self) -> str:
        if not self._last_kill:
            return ""
        _, killer_id = self._last_kill
        killer_name = self._name_by_id.get(killer_id, "Unknown")
        if killer_name == "Unknown":
            return ""
        return self._extract_team(killer_name)

    def _trigger_companion(self, section: str, label: str) -> None:
        if not label:
            return
        mapping = self._companion_map.get(section, {})
        location = mapping.get(label)
        if not location:
            return

        host = self.companion_ip_var.get().strip()
        if not host:
            return

        page, row, col = location
        url = f"http://{host}/api/location/{page}/{row}/{col}/press"
        request = urllib.request.Request(url, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                response.read()
        except urllib.error.URLError:
            return

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
