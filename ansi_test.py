from time import sleep

# print("Hello, World", end="", flush=True)
# sleep(1)
# print("\x1b[2K\r", end="", flush=True)
# sleep(1)
# print("Goodbye world")
# sleep(1)

from rich.progress import track
from time import sleep

for n in track(range(10)):
    print(f"Line {n}")
    sleep(0.5)
