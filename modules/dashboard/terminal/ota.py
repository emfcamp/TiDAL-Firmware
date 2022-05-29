import ota, wifi, term, machine

while True:
    term.clear()
    term.header(f"Updating from {ota.get_version()}...")
    wifi.connect()
    wifi.wait()
    def progress(ver, pct):
        term.goto(0, 3)
        term.color(35, 40, 1)
        print(ver)
        term.color()
        
        twentieths = pct // 5
        term.goto(5, 5)
        term.color(37,47, 0)
        print(" " * twentieths, end="")
        term.color(30,40, 0)
        print(" " * (20-twentieths), end="")
        term.color()
        print(f" - {pct}%")
        print()
        return True
    try:
        result = ota.update(progress)
    except OSError as e:
        print("Error:" + str(e))
    machine.reset()