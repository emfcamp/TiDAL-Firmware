import term, system, settings, term_menu

system.serialWarning()

term.header(True, "Configure nickname")
nickname = settings.get("hello_name")
if not nickname:
    nickname = ""
nickname = term.prompt("Nickname", 1, 3, nickname)
settings.set("hello_name", nickname)
term_menu.return_to_home()