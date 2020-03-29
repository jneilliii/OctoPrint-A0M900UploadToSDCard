/*
 * View model for OctoPrint-A0M900UploadToSDCard
 *
 * Author: Aegean Odyssey
 * License: AGPLv3
 */
$(function() {
	function ao_m990_upload_to_sdcardViewModel(parameters) {
		var self = this;

		self.filesViewModel = parameters[0];

		self.onDataUpdaterPluginMessage = function(plugin, data) {
			if (plugin != "ao_m990_upload_to_sdcard") {
				return;
			}
			if(data.hasOwnProperty("pct")){
				self.filesViewModel._setProgressBar(pct, 'Uploading ...', false);
			}
		}
	}

	OCTOPRINT_VIEWMODELS.push({
		construct: ao_m990_upload_to_sdcardViewModel,
		dependencies: [ "filesViewModel" ],
		elements: [ /* ... */ ]
	});
});
