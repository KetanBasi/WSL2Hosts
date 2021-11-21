#
# * isUserAdmin() and runAsAdmin() Source: https://stackoverflow.com/a/19719292
# * Both might need some improvements
import os
import pathlib
import sys
import traceback


script_location = pathlib.Path(__file__)
script_dir = script_location.parent.resolve()

help_str = f"""usage: {script_location} <command>
       where <command> is either "start" or "stop"
       
       Run as Windows service is not supported yet"""


def isUserAdmin():
    if os.name == 'nt':
        import ctypes
        # WARNING: requires Windows XP SP2 or higher!
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except:
            traceback.print_exc()
            print("Admin check failed, assuming not an admin.")
            return False
    elif os.name == 'posix':
        return os.getuid() == 0
    else:
        raise RuntimeError("Unsupported operating system for this module: %s" % (os.name,))


def runAsAdmin(cmdLine=None, wait=True):
    if os.name != 'nt':
        raise RuntimeError("This function is only implemented on Windows.")
    import win32con
    import win32process
    from win32com.shell.shell import ShellExecuteEx
    from win32com.shell import shellcon
    python_exe = sys.executable
    if cmdLine is None:
        cmdLine = [python_exe]+sys.argv
    elif type(cmdLine) not in (tuple, list):
        raise ValueError("cmdLine is not a sequence.")
    cmd = '"%s"' % (cmdLine[0],)
    params = " ".join(['"%s"' % (x,) for x in cmdLine[1:]])
    showCmd = win32con.SW_SHOWNORMAL
    lpVerb = 'runas'
    try:
        procInfo = ShellExecuteEx(
            nShow=showCmd,
            fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
            lpVerb=lpVerb,
            lpFile=cmd,
            lpParameters=params)
    except Exception as error:
        raise RuntimeError(error)
    if wait:
        procHandle = procInfo['hProcess']
        rc = win32process.GetExitCodeProcess(procHandle)
    else:
        rc = None
    return rc


def run():
    command = f"pythonw {os.path.join(script_dir, 'wsl2hosts.py')}"
    print(command)
    if not isUserAdmin():
        runAsAdmin(command.split())
    else:
        os.system(command)


def main():
    try:
        arg = sys.argv[1].strip().lower()
        lock_file = os.path.join(script_dir, "main.lock")
        lock_file_2 = os.path.join(os.environ.get('temp'),
                                   'WSL2Hosts',
                                   "main.lock")
        
        if arg == "start":
            if os.path.isfile(lock_file):
                print("Already running")
            else:
                run()
        
        elif arg == "stop":
            try:
                if os.path.isfile(lock_file):
                    os.remove(lock_file)
                elif os.path.isfile(lock_file_2):
                    os.remove(lock_file_2)
                else:
                    raise FileNotFoundError
            except FileNotFoundError:
                print("Not started yet")
        
        elif arg == "help":
            print(help_str)
        
        elif arg == "install":
            raise NotImplementedError("Not Implemented")
        
        elif arg == "uninstall":
            raise NotImplementedError("Not Implemented")
        
        else:
            print(f"Invalid command: {arg}")
    
    except IndexError:
        print("No command provided\n\n" + help_str)


main()
