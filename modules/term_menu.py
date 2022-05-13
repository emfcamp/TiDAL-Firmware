import term, consts

system = None
return_to_home = lambda: None

class UartMenu():
	def __init__(self, gts, pm, safe = False, pol="Power off"):
		global return_to_home
		self.gts = gts
		self.menu = self.menu_main
		if (safe):
			self.menu = self.menu_safe
		self.buff = ""
		self.pm = pm
		self.power_off_label = pol
		return_to_home = self.return_to_home
	
	def return_to_home(self):
		self.menu = self.menu_main()
	
	def main(self):
		if self.pm:
			term.setPowerManagement(self.pm)
		while self.menu:
			self.menu()
		
	def drop_to_shell(self):
		self.menu = False
		term.clear()
	
	def menu_main(self):
		items = ["Python shell", "Installer", "Settings", "Tools", "Check for updates"]
		if self.gts:
			items.append(self.power_off_label)
		callbacks = [self.drop_to_shell, self.opt_installer, self.menu_settings, self.menu_tools, self.opt_ota_check, self.go_to_sleep]
		message = ""
		cb = term.menu("Main menu", items, 0, message)
		self.menu = callbacks[cb]
		return
	
	def go_to_sleep(self):
		self.gts()
		
	def opt_change_nickname(self):
		import dashboard.terminal.nickname
		
	def opt_installer(self):
		import dashboard.terminal.installer
	
	def opt_configure_wifi(self):
		import dashboard.terminal.wifi
		
	def opt_configure_services(self):
		import dashboard.terminal.services
	
	def opt_ota_check(self):
		import dashboard.terminal.ota
		
	def opt_downloader(self):
		import dashboard.terminal.downloader
		
	def menu_settings(self):
		items = ["Change nickname", "WiFi configuration", "Services", "Update firmware", "< Return to main menu"]
		callbacks = [self.opt_change_nickname, self.opt_configure_wifi, self.opt_configure_services, self.opt_ota, self.menu_main, self.menu_main]
		cb = term.menu("Settings", items)
		self.menu = callbacks[cb]
	
	def menu_tools(self):
		items = ["File downloader", "< Return to main menu"]
		callbacks = [self.opt_downloader, self.menu_main, self.menu_main]
		cb = term.menu("Tools", items)
		self.menu = callbacks[cb]
	
	def menu_safe(self):
		items = ["Main menu"]
		callbacks = [self.menu_main]
		cb = term.menu("You have started the badge in safe mode!", items)
		self.menu = callbacks[cb]