import {useEffect,useRef} from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export default function MapBox({bbox}){
  const ref=useRef(null);
  useEffect(()=>{
    if(!ref.current) return;
    const map=L.map(ref.current).setView([20,78],4);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"&copy; OSM"}).addTo(map);
    if(bbox?.length===4){
      const [minLon,minLat,maxLon,maxLat]=bbox;
      const rect=L.rectangle([[minLat,minLon],[maxLat,maxLon]],{weight:1});
      rect.addTo(map);
      map.fitBounds([[minLat,minLon],[maxLat,maxLon]]);
    }
    return()=>map.remove();
  },[bbox]);
  return <div ref={ref} style={{height:380,marginTop:16,borderRadius:12}}/>;
}
