/* Restores jQuery.browser (removed in jQuery 1.9) for the theme's hashchange plugin. */
if (window.jQuery && !jQuery.browser) { jQuery.browser = { msie: false, version: '0' }; }
/* The theme bundles the goMap plugin, which needs these two Google Maps classes at load time.
   The site shows no maps, so the Maps API is not loaded; minimal placeholders keep plugins.js running. */
if (!window.google) { window.google = {}; }
if (!google.maps) { google.maps = { Geocoder: function () {}, OverlayView: function () {} }; }
