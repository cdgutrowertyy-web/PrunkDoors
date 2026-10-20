import os, sys, time, random, shutil, threading
import tkinter as tk
from tkinter import messagebox
import pygame
import keyboard

# ---------- НАСТРОЙКИ ----------
SECRET = "AAAYOUASLABAK"          # капсом
SECRET_TIMEOUT = 15                # сек на ввод серии
DISARM_AFTER = 5 * 60              # 5 минут до «выключения»
COIN_NAME = "coin.jpg"             # Имя картинки монетки (теперь jpg)
COINS_NEEDED = 5
COIN_FOLDERS = [                   # куда «разбросать» монетки
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Pictures"),
    os.path.expanduser("~/Music"),
]
# --------------------------------

BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(BASE, "assets")
STATE = {"disarmed": False, "collected": 0, "buffer": "", "last_key": 0.0}

# ---------- 1. СКРИМЕР ----------
def play_screamer():
    try:
        pygame.init()
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("")
        img_path = os.path.join(ASSETS, "rush_scream.jpg") # Теперь jpg
        img = pygame.image.load(img_path)
        img = pygame.transform.scale(img, screen.get_size())

        # Блок со звуком оставил на случай, если решишь добавить его позже
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(os.path.join(ASSETS, "scream.wav"))
            pygame.mixer.music.play()
        except Exception:
            pass # Если звука нет, просто пропускаем

        start = time.time()
        clock = pygame.time.Clock()
        while time.time() - start < 3:      # 3 секунды скримера
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
            screen.blit(img, (0, 0))
            pygame.display.flip()
            clock.tick(30)
        pygame.quit()
    except Exception as e:
        print(f"Ошибка скримера: {e}")

# ---------- 2. РАЗБРОС МОНЕТОК ----------
def scatter_coins():
    src = os.path.join(ASSETS, COIN_NAME)
    placed = []
    for folder in COIN_FOLDERS:
        if not os.path.isdir(folder):
            continue
        try:
            dst = os.path.join(folder, COIN_NAME)
            shutil.copyfile(src, dst)
            placed.append(dst)
            if len(placed) >= COINS_NEEDED:
                break
        except Exception:
            continue
    return placed

# ---------- 3. ГЛАВНОЕ ОКНО ----------
class PrankApp:
    def __init__(self, root, coin_paths):
        self.root = root
        self.coin_paths = coin_paths
        self.collected = 0
        self.start_time = time.time()

        root.title("DORS.exe — восстановление")
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        root.configure(bg="#1a1a1a")
        root.protocol("WM_DELETE_WINDOW", lambda: None)

        tk.Label(root, text="⚠ СИСТЕМА ПОВРЕЖДЕНА ⚠",
                 fg="red", bg="#1a1a1a",
                 font=("Segoe UI", 32, "bold")).pack(pady=20)

        tk.Label(root,
                 text=("Найди монеты DORS в папках (Документы, Загрузки, Рабочий стол,\n"
                       "Изображения, Музыка) и перетащи их в это окно.\n"
                       f"Нужно монет: {COINS_NEEDED}. Иначе через 5 минут — выключение."),
                 fg="white", bg="#1a1a1a",
                 font=("Segoe UI", 16)).pack(pady=10)

        self.counter = tk.Label(root, text=f"Собрано: 0 / {COINS_NEEDED}",
                                fg="gold", bg="#1a1a1a",
                                font=("Segoe UI", 22, "bold"))
        self.counter.pack(pady=10)

        self.timer = tk.Label(root, text="", fg="orange", bg="#1a1a1a",
                              font=("Segoe UI", 18))
        self.timer.pack(pady=10)

        self.dropzone = tk.Label(root, text="⬇ ПЕРЕТАЩИ МОНЕТЫ СЮДА ⬇\n(или нажимай на эту зону)",
                                 fg="white", bg="#333",
                                 font=("Segoe UI", 18, "bold"),
                                 width=40, height=8)
        self.dropzone.pack(pady=20)
        self.dropzone.bind("<Button-1>", lambda e: self.collect_one())

        tk.Label(root,
                 text="Экстренный выход: введи секретный код (капсом, 15 сек на серию)",
                 fg="gray", bg="#1a1a1a",
                 font=("Segoe UI", 12)).pack(side="bottom", pady=5)

        self.root.bind("<Key>", self.on_key)
        self.tick_timer()

    def collect_one(self, path=None):
        if self.collected >= COINS_NEEDED:
            return
        self.collected += 1
        self.counter.config(text=f"Собрано: {self.collected} / {COINS_NEEDED}")
        if self.collected >= COINS_NEEDED:
            self.success()

    def on_key(self, event):
        now = time.time()
        if now - STATE["last_key"] > SECRET_TIMEOUT:
            STATE["buffer"] = ""
        STATE["last_key"] = now

        ch = event.char
        if ch and ch.isprintable():
            STATE["buffer"] += ch.upper()
            if len(STATE["buffer"]) > len(SECRET):
                STATE["buffer"] = STATE["buffer"][-len(SECRET):]
            if STATE["buffer"].endswith(SECRET):
                self.disarm()

    def disarm(self):
        STATE["disarmed"] = True
        self.cleanup_coins()
        messagebox.showinfo("DORS.exe", "Код принят. Шутка окончена :)")
        self.root.destroy()

    def tick_timer(self):
        if STATE["disarmed"]:
            return
        elapsed = time.time() - self.start_time
        left = max(0, DISARM_AFTER - int(elapsed))
        m, s = divmod(left, 60)
        self.timer.config(text=f"До выключения: {m:02d}:{s:02d}")
        if left <= 0:
            self.fake_shutdown()
            return
        self.root.after(1000, self.tick_timer)

    def fake_shutdown(self):
        win = tk.Toplevel(self.root)
        win.attributes("-fullscreen", True)
        win.attributes("-topmost", True)
        win.configure(bg="black")
        tk.Label(win, text="Завершение работы...",
                 fg="white", bg="black",
                 font=("Segoe UI", 28)).pack(expand=True)
        tk.Label(win, text="(Это шутка. Нажми Esc)",
                 fg="gray", bg="black",
                 font=("Segoe UI", 14)).pack(pady=20)
        win.bind("<Escape>", lambda e: (win.destroy(), self.root.destroy()))

    def success(self):
        self.cleanup_coins()
        messagebox.showinfo("DORS.exe", "Все монеты собраны! Ты спасён 😎\n\n"
                                        "С тебя шаурма автору розыгрыша.")
        self.root.destroy()

    def cleanup_coins(self):
        for p in self.coin_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

# ---------- 4. ГЛОБАЛЬНЫЙ ХОТКЕЙ (запасной выход) ----------
def global_hotkey_watcher():
    buffer = {"s": "", "t": 0.0}
    def on_key(e):
        if e.event_type != "down":
            return
        now = time.time()
        if now - buffer["t"] > SECRET_TIMEOUT:
            buffer["s"] = ""
        buffer["t"] = now
        name = e.name.upper()
        if len(name) == 1:
            buffer["s"] = (buffer["s"] + name)[-len(SECRET):]
            if buffer["s"].endswith(SECRET):
                os._exit(0)  # мгновенный аварийный выход
    try:
        keyboard.hook(on_key)
        keyboard.wait()
    except:
        pass

# ---------- 5. ЗАПУСК ----------
def main():
    play_screamer()
    coins = scatter_coins()
    root = tk.Tk()
    app = PrankApp(root, coins)
    threading.Thread(target=global_hotkey_watcher, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
