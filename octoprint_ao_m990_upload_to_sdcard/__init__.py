# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
import os, sys, time, logging, threading, serial
import octoprint.util as util

class ao_m990_upload_to_sdcardPlugin(octoprint.plugin.SettingsPlugin,
                                     octoprint.plugin.AssetPlugin,
                                     octoprint.plugin.TemplatePlugin):

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict()

	##~~ AssetPlugin mixin

	def get_assets(self):
		return dict(
			js=["js/ao_m990_upload_to_sdcard.js"]
		)

	def ao_m990_upload_to_sdcard(self, printer, filename, path,
								 started_f, success_f, failure_f,
								 *args, **kwargs):

		logger = logging.getLogger(__name__)

		target = util.get_dos_filename(filename, None, 'gco', ['g', 'gc'])
		if not target: target = 'CACHE.GCO'

		logger.info("Uploading {} to {}.".format(filename, target))
		started_f(filename, target)

		def ao_set_progress(pct):
			self._plugin_manager.send_plugin_message(self._identifier, dict(pct=pct))
			pass

		def ao_upload_protocol():

			TIMEOUT = 3  # time out, seconds

			# tiny hack for python 2/3 compatibility
			ORD = (lambda c: ord(c), lambda c: c)[sys.hexversion < 0x3000000]

			def ao_waitfor(sio, pattern):
				t = time.time() + TIMEOUT
				n = len(pattern)
				i = 0
				while time.time() < t:
					c = sio.read(1)
					if not c: continue
					i = i + 1 if ORD(c) == pattern[i] else 0
					if i < n: continue
					return False  # success
				return True       # timeout

			x, port, rate, prof = printer.get_current_connection()
			printer.disconnect()

			ERROR = 0
			try:
				sio = serial.Serial(port, rate, timeout = TIMEOUT)
				inp = open(path, "rb")
				
				inp.seek(0, os.SEEK_END)
				fz = inp.tell()  # file size, bytes
				inp.seek(0, os.SEEK_SET)

				ao_set_progress(0);
			
				dT = time.time()
				N = 0
				sio.write("\nM990 S{:d} /{:s}\n".format(fz, target).encode())
				if not ao_waitfor(sio, b'BEGIN\n'):
					BLKSZ = 0x200  # block size, bytes
					pkt = bytearray(BLKSZ)
					while True:
						u = inp.readinto(pkt)
						if u < BLKSZ:
							pkt[u:] = b'\0' *(BLKSZ - u)
						if sio.write(pkt) < BLKSZ: u = 0
						if ao_waitfor(sio, b'\n'): u = 0
						N += u
						if u < BLKSZ:
							break
						# update progress every 128 blocks
						if (N & 0xffff) == 0:
							ao_set_progress(N/fz)

				time.sleep(TIMEOUT)
				sio.write(b'\nM29\n')
				sio.flush()

				ao_set_progress(100)
				
				dT = time.time() - dT
				ERROR = int(N < fz)
				S = "{}. Sent {:d} of {:d} B in {:d} s ({:.0f} B/s)."
				logger.info(S.format(("SUCCESS", "FAILED")[ERROR],
									 N, fz, int(dT), N/dT))

			except serial.SerialException as e:
				logger.exception("{}".format(e))

			except IOError as e:
				logger.exception("{}".format(e))

			finally:
				if inp: inp.close
				if sio: sio.close

			printer.connect(port=port, baudrate=rate, profile=prof)
			# call the appropriate success or failure callback function
			(success_f, failure_f)[ERROR](filename, target, int(dT))

		thread = threading.Thread(target = ao_upload_protocol)
		thread.daemon = True
		thread.start()
		return target

	##~~ Softwareupdate hook

	def get_update_information(self):
		return dict(
			ao_m990_upload_to_sdcard=dict(
				displayName="Ao_m990_upload_to_sdcard Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="aegean-odyssey",
				repo="OctoPrint-A0M900UploadToSDCard",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/aegean-odyssey/OctoPrint-A0M900UploadToSDCard/archive/{target_version}.zip"
			)
		)

__plugin_name__          = "AO M990 Upload to SDCard"
__plugin_pythoncompat__  = ">=2.7,<4"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = ao_m990_upload_to_sdcardPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.printer.sdcardupload": __plugin_implementation__.ao_m990_upload_to_sdcard
	}

