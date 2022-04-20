def freeze_images(path, generated_dir):
    path = convert_path(path)
    generated_dir = convert_path(generated_dir)
    convert_script = convert_path("$(MPY_DIR)/../st7789/utils/imgtobitmap.py")
    generated_modules = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext == ".png" or ext == ".jpg":
                filepath = os.path.join(dirpath, filename)

                relpath = os.path.relpath(filepath, path)
                genpath = os.path.splitext(os.path.join(generated_dir, relpath))[0] + ext.replace(".", "_") + ".py"
                if not os.path.isfile(genpath):
                    os.makedirs(os.path.dirname(genpath), exist_ok=True)
                    output = subprocess.check_output([
                        sys.executable,
                        convert_script,
                        filepath,
                        "8" # bpp
                    ], stderr=subprocess.DEVNULL)
                    with open(genpath, "wb") as f:
                        f.write(output)
                generated_modules.append(os.path.relpath(genpath, generated_dir))

    if generated_modules:
        freeze(generated_dir, generated_modules)

freeze("$(PORT_DIR)/modules")
freeze("$(MPY_DIR)/tools", ("upip.py", "upip_utarfile.py"))
freeze("$(MPY_DIR)/ports/esp8266/modules", "ntptime.py")
freeze("$(MPY_DIR)/drivers/dht", "dht.py")
freeze("$(MPY_DIR)/drivers/onewire")
freeze("$(MPY_DIR)/../modules")
freeze_images("$(MPY_DIR)/../modules", "$(PORT_DIR)/build-tildamk6/modules_generated")

freeze("$(MPY_DIR)/../st7789/fonts/bitmap", "vga1_8x8.py")
include("$(MPY_DIR)/extmod/uasyncio/manifest.py")
include("$(MPY_DIR)/extmod/webrepl/manifest.py")
include("$(MPY_DIR)/drivers/neopixel/manifest.py")
