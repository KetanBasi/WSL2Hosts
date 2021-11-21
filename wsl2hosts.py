import configparser
import os
import pathlib
import re
import time

try:
    from win10toast import ToastNotifier
except ModuleNotFoundError:
    os.system("pip install win10toast")
    try:
        from win10toast import ToastNotifier
    except ModuleNotFoundError:
        raise RuntimeError("'win10toast' module is missing. "
                           "Please install it manually")

notifier = ToastNotifier()
default_config = """[base]
domain = wsl.local
; delay in second, use decimal for ms value (i.e. 0.2)
delay = 5
"""
start_line = "# WSL\n"
content_line = "{0}\t{1}\n"
content_line_pattern = (
    r"\b((?:(?:2(?:[0-4][0-9]|5[0-5])|[0-1]?[0-9]?[0-9])\.){3}"
    r"(?:(?:2(?:[0-4][0-9]|5[0-5])|[0-1]?[0-9]?[0-9])))\b\W+([\w.]+)")
this_file_dir = pathlib.Path(__file__).parent.resolve()
hosts_location = "C:\\Windows\\System32\\drivers\\etc\\hosts"
lock_location = os.path.join(os.environ.get("temp"), "WSL2Hosts")
if os.environ.get("temp"):
    if not os.path.isdir(lock_location):
        os.makedirs(lock_location, exist_ok=True)
    lock_file = os.path.join(lock_location, "main.lock")
else:
    lock_file = os.path.join(this_file_dir, "main.lock")


class Wsl2Hosts:
    def __init__(self):
        self.domain = None
        self.delay = None
        self.ip_addr = None
        self.notif = None
        self.content_line = None
        self.get_wsl_ip()
    def __str__(self):
        return self.domain
    def get_wsl_ip(self):
        ip_addr = os.popen("wsl hostname -I")
        self.ip_addr = ip_addr.read().strip()
        if self.notif == "noisy":
            notifier.show_toast(
                "WSL2Hosts: Get WSL IP Address",
                f"Success: {self.ip_addr}")

    def write_hosts(self):
        self.content_line = content_line.format(self.ip_addr, self.domain)
        with open(hosts_location, "r") as hosts_file:
            hosts_content = hosts_file.readlines()
        try:
            target_line = hosts_content.index("# WSL\n") + 1
            line_match = re.match(
                content_line_pattern,
                hosts_content[target_line])
            if line_match and (
                    line_match[1] == self.ip_addr
                    and
                    line_match[2] == self.domain):
                if self.notif == "noisy":
                    notifier.show_toast(
                        "WSL2Hosts: Skip write",
                        "Same ip & domain")
                return
            hosts_content[target_line] = self.content_line
        except ValueError:
            hosts_content.append(start_line + self.content_line)
        with open(hosts_location, "w") as hosts_file:
            hosts_file.write(''.join(hosts_content))
        if self.notif == "noisy":
            notifier.show_toast(
                "WSL2Hosts: Write to hosts",
                f"Line: {self.content_line}")

    def read_config(self):
        config_file = os.path.join(this_file_dir, "config.ini")
        config = configparser.ConfigParser()
        if not os.path.isfile(config_file):
            with open(config_file, "w") as config_file:
                config_file.write(default_config)
        config.read(config_file)
        config.base = config["base"]
        self.domain = config.base.get("domain", "wsl.local")
        self.delay = config.base.getfloat("delay", 5.0)
        self.notif = config.base.get("notif", "default").strip().lower()
        if self.notif not in ("default", "silent", "noisy"):
            raise RuntimeWarning(f"Invalid \"notif\" value: {self.notif}")
        if self.notif not in ("default", "silent"):
            notifier.show_toast(
                "WSL2Hosts: Read config",
                f"Success:\ndomain = \"{self.domain}\"\n"
                "delay = \"{self.delay}\"\nnotif = \"{self.notif}\"")

    def run(self):
        self.read_config()
        run = os.path.isfile(lock_file)
        if not run:
            with open(lock_file, "w") as file:
                file.write("running")
            run = True
        if self.notif != "silent":
            notifier.show_toast(
                "WSL2Hosts: Started",
                f"Target: {hosts_location}")
        while run:
            run = os.path.isfile(lock_file)
            if not run:
                if self.notif != "silent":
                    notifier.show_toast(
                        "WSL2Hosts: Stopped",
                        f"Target: {hosts_location}")
                break
            self.get_wsl_ip()
            self.write_hosts()
            time.sleep(self.delay)


serv = Wsl2Hosts()
serv.run()
