import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";

export default function DatasetPage() {
  const { id } = useParams();
  const [dataset, setDataset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5001";

  useEffect(() => {
    const fetchDataset = async () => {
      try {
        const { data } = await axios.get(`${API_BASE}/api/dataset/${id}`);
        setDataset(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDataset();
  }, [id]);

  if (loading) return <div>Loading dataset...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div style={{ padding: "2rem" }}>
      <h1>{dataset?.title || "Dataset Details"}</h1>
      <p>{dataset?.summary || "No summary available."}</p>
      {dataset?.link && (
        <a href={dataset.link} target="_blank" rel="noopener noreferrer">
          View Dataset
        </a>
      )}
    </div>
  );
}
