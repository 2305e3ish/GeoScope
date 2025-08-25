import { Routes, Route, useNavigate } from "react-router-dom";
import Background3D from "./components/Background3D";
import { ReactTyped } from "react-typed";
import "./App.css";
import MapPage from "./components/MapPage"; // Create this file

function Home() {
  const navigate = useNavigate();

  return (
    <>
      <Background3D />
      <div className="overlay">
        <ReactTyped
          className="subtitle"
          strings={[
            "Explore the Earth in 3D.",
            "Discover insights with AI.",
            "Visualize geospatial data like never before."
          ]}
          typeSpeed={40}
          backSpeed={30}
          loop
        />
        <button className="button" onClick={() => navigate("/map")}>
          <span className="button_lg">
            <span className="button_sl"></span>
            <span className="button_text">Explore Now</span>
          </span>
        </button>
      </div>
    </>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/map" element={<MapPage />} />
    </Routes>
  );
}