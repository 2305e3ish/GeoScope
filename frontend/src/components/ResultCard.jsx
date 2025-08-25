export default function ResultCard({item}){
  return(
    <div style={{border:"1px solid #eee",borderRadius:12,padding:12}}>
      <div style={{fontWeight:600}}>{item.title}</div>
      <div style={{fontSize:14,color:"#555",margin:"8px 0"}}>{item.summary||"—"}</div>
      {item.link&&<a href={item.link} target="_blank">Open dataset »</a>}
    </div>
  )
}
