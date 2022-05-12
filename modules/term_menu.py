import term, consts

system = None

class UartMenu():
	def __init__(self, gts, pm, safe = False, pol="Power off"):
		self.gts = gts
		self.menu = self.menu_main
		if (safe):
			self.menu = self.menu_safe
		self.buff = ""
		self.pm = pm
		self.power_off_label = pol
	
	def main(self):
		if self.pm:
			term.setPowerManagement(self.pm)
		while self.menu:
			self.menu()
		
	def drop_to_shell(self):
		self.menu = False
		term.clear()
		import shell
	
	def menu_main(self):
		items = ["Python shell", "Apps", "Installer", "Settings", "Tools", "About", "Check for updates"]
		if self.gts:
			items.append(self.power_off_label)
		callbacks = [self.drop_to_shell, self.opt_launcher, self.opt_installer, self.menu_settings, self.menu_tools, self.opt_about, self.opt_ota_check, self.go_to_sleep]
		#message = "Welcome!\nYour badge is running firmware version "+str(consts.INFO_FIRMWARE_BUILD)+": "+consts.INFO_FIRMWARE_NAME+"\n"
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
	
	def opt_launcher(self):
		import dashboard.terminal.launcher
	
	def opt_configure_wifi(self):
		import dashboard.terminal.wifi
		
	def opt_configure_orientation(self):
		import dashboard.terminal.orientation

	def opt_configure_picture(self):
		import dashboard.terminal.picture
	
	def opt_configure_services(self):
		import dashboard.terminal.services
	
	def opt_configure_homescreen(self):
		import dashboard.terminal.home_settings
		
	def opt_configure_calibrate(self):
		import dashboard.terminal.calibrate
		
	def opt_ota(self):
		system.ota(True)
		
	def opt_ota_check(self):
		import dashboard.tools.update_firmware
	
	def opt_about(self):
		import dashboard.other.about
		
	def opt_downloader(self):
		import dashboard.terminal.downloader
		
	def menu_settings(self):
		items = ["Change nickname", "Change picture", "WiFi configuration", "Change display orientation", "Homescreen configuration", "Services", "Update firmware", "< Return to main menu"]
		callbacks = [self.opt_change_nickname, self.opt_configure_picture, self.opt_configure_wifi, self.opt_configure_orientation, self.opt_configure_homescreen, self.opt_configure_services, self.opt_ota, self.menu_main, self.menu_main]
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