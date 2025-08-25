import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Import Russo One font in your index.html or main CSS file:
// <link href="https://fonts.googleapis.com/css?family=Russo+One&display=swap" rel="stylesheet">

const customIcon = new L.Icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/684/684908.png",
  iconSize: [40, 40],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32]
});

function MapPage() {
  const [showStreetView, setShowStreetView] = useState(false);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  // Example disaster details
  const disasterDetails = {
    title: "New Delhi Floods",
    description:
      "Severe flooding affected New Delhi in July 2023, impacting thousands of residents and causing significant infrastructure damage.",
    date: "July 15, 2023",
    time: "03:30 PM",
    place: "New Delhi, India"
  };

  // Coordinates for New Delhi (India Gate for Street View)
  const lat = 28.6129;
  const lng = 77.2295;

  // Handle search (for now, just log the query)
  const handleSearch = (e) => {
    e.preventDefault();
    // You can implement search logic here
    alert(`Searching for: ${search}`);
  };

  return (
    <div style={{ display: "flex", height: "100vh", width: "100vw" }}>
      {/* Left panel */}
      <div style={{
        width: "350px",
        background: "rgba(0, 0, 0)",
        color: "#fff",
        padding: "2rem",
        boxSizing: "border-box",
        overflowY: "auto",
        position: "relative"
      }}>
        {/* Logo line */}
        <div style={{ marginBottom: "1rem" }}>
          <span
            style={{
              fontFamily: "'Russo One', sans-serif",
              fontSize: "2rem",
              color: "#ffffffff",
              letterSpacing: "2px",
              display: "block"
            }}
          >
            GEOSCOPE.ai
          </span>
        </div>
        {/* Search bar line with back arrow */}
        <form onSubmit={handleSearch} style={{ display: "flex", alignItems: "center", width: "80%", marginBottom: "2rem" }}>
          <span
            style={{
              cursor: "pointer",
              marginRight: "0.5rem",
              fontSize: "1.5rem",
              color: "#ffffffff",
              display: "flex",
              alignItems: "center"
            }}
            onClick={() => navigate("/")}
            title="Go Back"
          >
            &#8592;
          </span>
          <input
            type="text"
            placeholder="Search disaster info..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              width: "100%",
              padding: "0.5rem 1rem",
              borderRadius: "6px",
              border: "none",
              fontSize: "1rem",
              background: "#333",
              color: "#ffffffff"
            }}
          />
        </form>
        <h2>Disaster Information</h2>
        <div>
          <h3>{disasterDetails.title}</h3>
          <p>{disasterDetails.description}</p>
          <p>
            <strong>Date:</strong> {disasterDetails.date}
            <br />
            <strong>Time:</strong> {disasterDetails.time}
            <br />
            <strong>Place:</strong> {disasterDetails.place}
            <br />
            <strong>Status:</strong> Relief operations ongoing.
          </p>
        </div>
      </div>
      {/* Map panel */}
      <div style={{ flex: 1, position: "relative" }}>
        <MapContainer
          center={[20, 0]}
          zoom={2}
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
          />
          <TileLayer
            url="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
            attribution="Labels &copy; Esri"
          />
          <Marker position={[lat, lng]} icon={customIcon}>
            <Popup>
              <h3 style={{ marginBottom: "1rem" }}>{disasterDetails.title}</h3>
              <strong>Date:</strong> {disasterDetails.date}
              <br />
              <strong>Time:</strong> {disasterDetails.time}
              <br />
              <strong>Place:</strong> {disasterDetails.place}
              <br />
              <button style={{background: "rgba(226, 226, 226, 1)", marginTop: "0.5rem" }} onClick={() => setShowStreetView(true)}>
                View location
              </button>
            </Popup>
          </Marker>
        </MapContainer>
        {/* Modal for Street View */}
        {showStreetView && (
          <div style={{
            position: "absolute",
            top: "10%",
            left: "10%",
            width: "80%",
            height: "80%",
            background: "#000",
            zIndex: 1000,
            borderRadius: "12px",
            overflow: "hidden",
            boxShadow: "0 0 20px rgba(0,0,0,0.7)",
            color: "#fff"
          }}>
            <button
              style={{
                position: "absolute",
                top: 10,
                right: 10,
                zIndex: 1001,
                background: "#e8e7e7ff",
                border: "none",
                borderRadius: "4px",
                padding: "6px 12px",
                cursor: "pointer",
                color: "#222"
              }}
              onClick={() => setShowStreetView(false)}
            >
              Close
            </button>
            <div style={{ padding: "1rem" }}>
              <h2 style={{ marginBottom: "1rem" }}>{disasterDetails.title}</h2>
              <p>
                <strong>Date:</strong> {disasterDetails.date}
                <br />
                <strong>Time:</strong> {disasterDetails.time}
                <br />
                <strong>Place:</strong> {disasterDetails.place}
              </p>
            </div>
            <iframe
              title="Google Street View"
              width="100%"
              height="70%"
              frameBorder="0"
              style={{ border: 0 }}
              src={`https://www.google.com/maps?q=&layer=c&cbll=${lat},${lng}&cbp=11,0,0,0,0&output=svembed`}
              allowFullScreen
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default MapPage;