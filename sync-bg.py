from os import listdir, rename, environ
from time import ctime, strftime, strptime
from os.path import isfile, join, dirname, getctime, realpath
from ctypes import windll
from sys import executable as pyexe
import argparse
import imagesize as img # https://pypi.org/project/imagesize/#history
import configparser
from shutil import copy2
import codecs
import hashlib
import winreg

class syncbg:
    def __init__(self):
        self.default_resolution = windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1)
        self.folder = join(environ['USERPROFILE'], "AppData\Local\Packages\Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy\LocalState\Assets")
        self.config = configparser.ConfigParser()
        self.config.read_file(codecs.open(join(dirname(realpath(__file__)), "sync-bg.ini"), "r", "utf8"))
        self.sync_dir = self.config['syncbg']['sync_dir']
        if len(self.sync_dir) == 0:
            self.sync_dir = join(environ['USERPROFILE'], "Pictures")

    def update_bg(self):
        name, date = "", 0
        for fn in listdir(self.sync_dir):
            if not ".txt" in fn and getctime(join(self.sync_dir, fn)) > date:
                name, date = join(self.sync_dir, fn), getctime(join(self.sync_dir, fn))
        windll.user32.SystemParametersInfoW(20, 0, name, 0)
        print("Background has been changed -> " + name)

    def sync_folder(self):
        def get_file_hash(f):
            hasher = hashlib.md5()
            with open(f, 'rb') as afile:
                buf = afile.read()
                hasher.update(buf)
            return hasher.hexdigest()
        print("Synchronizing...")
        for fn in listdir(self.folder):
            if self.default_resolution == img.get(join(self.folder, fn)):
                if isfile(join(self.sync_dir, get_file_hash(join(self.folder, fn)) + ".png")):
                    print("{} -> {}\t{}".format(fn, get_file_hash(join(self.folder, fn)) + ".png", "\x1B[31mOLD\x1B[0m"))
                else:
                    print("{} -> {}\t{}".format(fn, get_file_hash(join(self.folder, fn)) + ".png", "\x1B[32mNEW\x1B[0m"))
                    copy2(join(self.folder, fn), join(self.sync_dir, get_file_hash(join(self.folder, fn)) + ".png"))
        else:
            f = open(join(self.sync_dir, ".sync.txt"), "w")
            f.write(strftime("%d.%m.%Y - %H:%M:%S"))
            f.close()
            print("Synchronizing has been finished!")

    def add_startup_script(update = False):
        reg = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(reg, "SYNC_BG", 0, winreg.REG_SZ, join(dirname(pyexe), "pythonw.exe") + " \"" + realpath(__file__) + "\" -S" + ("u" if update == True else ""))
        winreg.CloseKey(reg)

    def remove_startup_script():
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
        winreg.DeleteValue(key, "SYNC_BG")
        winreg.CloseKey(key)

parser = argparse.ArgumentParser(description="Sync Windows Spotlight pictures", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-S", action="store_true", help="sync pictures")
parser.add_argument("-Su", action="store_true", help="sync pictures and update background")
parser.add_argument("-sd", type=str, help="set sync directory")
parser.add_argument("-Si", action="store_true", help="add to startup -S")
parser.add_argument("-Siu", action="store_true", help="add to startup -Su")
parser.add_argument("-R", action="store_true", help="remove from startup")

args = parser.parse_args()
sb = syncbg()
if args.sd:
    try:
        config = configparser.ConfigParser()
        config["syncbg"]={"sync_dir": args.sd}
        with codecs.open(join(dirname(realpath(__file__)), "sync-bg.ini"), "w", "utf8") as configfile:
            config.write(configfile)
        print("Sync directory has been changed!")
    except Exception as e:
        raise e
elif args.Si:
    sb.add_startup_script()
elif args.Siu:
    sb.add_startup_script(True)
elif args.R:
    sb.remove_startup_script()
elif args.S:
    sb.sync_folder()
elif args.Su:
    sb.sync_folder()
    sb.update_bg()
else:
	print("for usage: sync-bg.py -h")
