(function () {
    window.StarMapApp = window.StarMapApp || {};

    class LocationPicker {
        constructor(containerId, options = {}) {
            this.containerId = containerId;
            this.onLocationChange = options.onLocationChange || (() => { });
            this.map = L.map(this.containerId).setView([options.initialLat || 20, options.initialLon || 0], 2);
            this.marker = null;
            this.init();
        }

        init() {
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map);

            L.Control.geocoder({
                defaultMarkGeocode: false
            }).on('markgeocode', (e) => {
                const { lat, lng } = e.geocode.center;
                this.updateMarker(lat, lng);
                this.map.setView([lat, lng], 8);
                this.onLocationChange(lat, lng);
            }).addTo(this.map);

            this.map.on('click', (e) => {
                const { lat, lng } = e.latlng;
                this.updateMarker(lat, lng);
                this.onLocationChange(lat, lng);
            });
        }

        updateMarker(lat, lng) {
            if (this.marker) {
                this.map.removeLayer(this.marker);
            }
            this.marker = L.marker([lat, lng]).addTo(this.map);
        }

        setView(lat, lng, zoom = 8) {
            this.map.setView([lat, lng], zoom);
            this.updateMarker(lat, lng);
        }

        getCurrentPosition() {
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject(new Error("Geolocation is not supported by your browser."));
                } else {
                    navigator.geolocation.getCurrentPosition(
                        (position) => resolve(position.coords),
                        (error) => reject(error)
                    );
                }
            });
        }
    }

    window.StarMapApp.LocationPicker = LocationPicker;
})();