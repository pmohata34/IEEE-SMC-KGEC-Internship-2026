// Create the map instance
const map = L.map('map', {
    zoomControl: true,
    attributionControl: true
});

// Dark basemap
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CartoDB',
    subdomains: 'abcd',
    maxZoom: 20
}).addTo(map);

// Node data from Flask (defined in dashboard.html)
const dashboardDataElement = document.getElementById('dashboard-data');
const dashboardData = dashboardDataElement
    ? JSON.parse(dashboardDataElement.textContent.trim())
    : { nodes: [], center: { lat: 22.6, lon: 88.36 } };

const nodes = dashboardData.nodes || [];
const center = dashboardData.center || { lat: 22.6, lon: 88.36 };
const latlngs = [];

// Add one marker per node (place)
nodes.forEach(node => {
    const latlng = [node.lat, node.lon];
    latlngs.push(latlng);

    const color = node.is_safe ? '#18d49b' : '#ff6b6b';

    const marker = L.circleMarker(latlng, {
        radius: 8,
        color: color,
        weight: 2,
        fillColor: color,
        fillOpacity: 0.9
    }).addTo(map);

    marker.bindPopup(
        `<div style="font-family: Outfit, sans-serif; min-width: 180px; color: #111;">
            <div style="font-size: 16px; font-weight: 700; margin-bottom: 6px;">${node.node}</div>
            <div style="font-size: 13px; margin-bottom: 4px;">Status: <b>${node.risk}</b></div>
            <div style="font-size: 13px;">Temp: <b>${node.temp}°C</b></div>
        </div>`
    );
});

// Fit map to all markers, or fallback center
if (latlngs.length > 0) {
    const bounds = L.latLngBounds(latlngs);
    map.fitBounds(bounds.pad(0.20));
} else {
    map.setView([center.lat, center.lon], 10);
}
