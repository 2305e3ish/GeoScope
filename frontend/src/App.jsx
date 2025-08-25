import { useState } from "react";
import axios from "axios";
import MapBox from "./components/MapBox";
import ResultCard from "./components/ResultCard";

export default function App(){
  const [q,setQ]=useState("");
  const [resp,setResp]=useState(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState(null);
  const API_BASE=import.meta.env.VITE_API_BASE||"http://localhost:5001";

  const search=async(e)=>{
    e.preventDefault();
    if(!q) return;
    setLoading(true); setError(null);
    try{
      const {data}=await axios.get(`${API_BASE}/api/search`,{params:{q}});
      setResp(data);
    }catch(err){setError(err.message)}finally{setLoading(false);}
  };

  return(
    <div style={{maxWidth:900,margin:"2rem auto",fontFamily:"system-ui"}}>
      <h1>EarthData Finder</h1>
      <form onSubmit={search} style={{display:"flex",gap:8}}>
        <input value={q} onChange={e=>setQ(e.target.value)}
          placeholder='Try: "floods in India 2019"'
          style={{flex:1,padding:12,borderRadius:8,border:"1px solid #ccc"}}/>
        <button style={{padding:"12px 16px"}}>Search</button>
      </form>
      {loading&&<p>Loading…</p>}
      {error&&<p style={{color:"red"}}>{error}</p>}
      {resp?.query&&<>
        <h3>Interpreted Query</h3>
        <pre>{JSON.stringify(resp.query,null,2)}</pre>
      </>}
      {resp?.query?.params_sent?.bounding_box&&
        <MapBox bbox={resp.query.params_sent.bounding_box.split(",").map(Number)}/>}
      {resp?.results?.length>0&&<>
        <h3>Results</h3>
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(260px,1fr))",gap:12}}>
          {resp.results.map(r=><ResultCard key={r.id} item={r}/>)}
        </div>
      </>}
    </div>);
}
