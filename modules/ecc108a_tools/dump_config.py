import ecc108a

def run():
    config = ecc108a.read_config()

    serial_number = config[0:4] + config[8:13]
    serial_number_str = ' '.join(f'{c:02x}' for c in serial_number)
    print(f"Serial number: {serial_number_str}")
    print(f"Revision number: {hex(int.from_bytes(config[4:8], 'little'))}")
    print(f"Reserved 1: {hex(config[13])}")
    print(f"Interface mode: {'I2C' if config[14] & 1 else 'SWI'}")
    print(f"Reserved 2: {hex(config[14] & 0xfe)} {hex(config[15])}")
    if config[14] & 1:
        print(f"I2C address: {hex(config[16])}")
    else:
        print(f"GPIO mode: {hex(config[16])}")
    print(f"Reserved 3: {hex(config[17])}")
    otp_modes = {0xaa: 'read-only', 0x55: 'consumption', 0x0: 'legacy'}
    print(f"OTP mode: {hex(config[18])} ({otp_modes.get(config[18], 'unknown')})")
    print(f"Selector mode: {'only zero' if config[19] & 1 else 'unlimited'}")
    print(f"TTL reference mode: {'VCC' if config[19] & 2 else 'fixed'}")
    print(f"Watchdog timeout: {'10s' if config[19] & 4 else '1.3s'}")
    print(f"Reserved 4: {hex(config[19] & 0xf8)}")

    print(f"UserExtra: {hex(config[84])}")
    print(f"Selector: {hex(config[85])}")
    lock_state = {0x55: 'unlocked', 0: 'locked'}
    print(f"LockValue: {hex(config[86])} ({lock_state[config[86]]})")
    print(f"LockConfig: {hex(config[87])} ({lock_state[config[87]]})")

    slotlocked = int.from_bytes(config[88:90], 'little')

    print(f"Reserved 5: {hex(config[90])}")  # "must be zero" actually 0xffff, and changes when keys are modified somehow
    print(f"Reserved 6: {hex(config[91])}")

    for cert in range(4):
        print(f"X509format[{cert}].PublicPosition: {config[92 + cert] & 0xf}")
        print(f"X509format[{cert}].TemplateLength: {(config[92 + cert] >> 4) & 0xf}")

    for key in range(16):
        print(f"Key {key}:")
        print(f"  SlotLocked: {'1 (unlocked)' if slotlocked & (1 << key) else '0 (locked)'}")

        slotconfig = int.from_bytes(config[key * 2:][20:22], 'little')
        keyconfig = int.from_bytes(config[key * 2:][96:98], 'little')

        if key < 8:
            print(f"  UseFlag: {hex(config[52 + key * 2])}")
            update_count = config[53 + key * 2]
            print(f"  UpdateCount: {config[53 + key * 2]}")

        if key == 15:
            keyuse_str = ' '.join(f'{c:02x}' for c in config[68:84])
            print(f"  Key use: {keyuse_str}")

        # If private, Sign, GenKey and PrivWrite are the only commands that work, and vice versa

