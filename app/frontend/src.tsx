import React, {useEffect, useMemo, useState} from "react";
import {createRoot} from "react-dom/client";
import "./style.css";

type Sku = {id:string; options:{colour:string; size:string}; price_cents:number; available_quantity:number; image:string};
type Product = {id:string; name:string; description:string; options:{colour:string[];size:string[]}; skus:Sku[]};
const api = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";
const key = () => crypto.randomUUID();

export function App() {
  const [product,setProduct] = useState<Product>(); const [selection,setSelection] = useState({colour:"",size:""});
  const [quantity,setQuantity] = useState(1); const [count,setCount] = useState(0); const [message,setMessage] = useState(""); const [busy,setBusy]=useState(false); const [error,setError]=useState("");
  const load = () => { setError(""); fetch(`${api}/api/products/trail-jacket`).then(r=>r.ok?r.json():Promise.reject()).then(setProduct).catch(()=>setError("商品加载失败，请重试。")); };
  useEffect(load,[]); useEffect(()=>{fetch(`${api}/api/cart`).then(r=>r.json()).then(x=>setCount(x.item_count)).catch(()=>undefined)},[]);
  const sku = useMemo(()=>product?.skus.find(s=>s.options.colour===selection.colour && s.options.size===selection.size),[product,selection]);
  useEffect(()=>setQuantity(q=>Math.max(1,Math.min(q,sku?.available_quantity || 1))),[sku?.id,sku?.available_quantity]);
  if(error) return <main><p role="alert">{error}</p><button onClick={load}>重新加载</button></main>;
  if(!product) return <main aria-busy="true">商品加载中…</main>;
  const choose=(field:"colour"|"size", value:string)=>setSelection(s=>({...s,[field]:value}));
  const disabled=(field:"colour"|"size", value:string)=>field==="colour" ? !product.skus.some(s=>s.options.colour===value && (!selection.size||s.options.size===selection.size)) : !product.skus.some(s=>s.options.size===value && (!selection.colour||s.options.colour===selection.colour));
  async function add(){ if(!sku) return setMessage("请先选择可售颜色和尺码。"); setBusy(true); setMessage(""); try { const r=await fetch(`${api}/api/cart/items`,{method:"POST",headers:{"Content-Type":"application/json","Idempotency-Key":key()},body:JSON.stringify({sku_id:sku.id,quantity})}); const data=await r.json(); if(!r.ok) throw new Error(data.detail?.message||"加入购物车失败"); setCount(data.cart.item_count); setMessage("已加入购物车。"); } catch(e) {setMessage(e instanceof Error?e.message:"发生未知错误");} finally {setBusy(false);} }
  const optionName={colour:"颜色",size:"尺码"};
  return <main><header><strong>Northstar</strong><span aria-label="购物车商品数">购物车（{count}）</span></header><section className="pdp"><img src={sku?.image||product.skus[0].image} alt="Trail Jacket"/><div><p className="eyebrow">户外服饰</p><h1>{product.name}</h1><p>{product.description}</p><p className="price">{sku?`¥${(sku.price_cents/100).toFixed(2)}`:"请选择规格"}</p>{(["colour","size"] as const).map(field=><fieldset key={field}><legend>{optionName[field]}</legend>{product.options[field].map(value=><button className={selection[field]===value?"selected":""} disabled={disabled(field,value)} aria-pressed={selection[field]===value} onClick={()=>choose(field,value)} key={value}>{value}</button>)}</fieldset>)}<p>{!sku?"请选择有效规格。":sku.available_quantity?`库存：${sku.available_quantity}`:"暂时缺货"}</p><label>数量 <input aria-label="数量" type="number" min="1" max={sku?.available_quantity||1} value={quantity} disabled={!sku||!sku.available_quantity} onChange={e=>setQuantity(Number(e.target.value))}/></label><button className="add" disabled={!sku||!sku.available_quantity||busy} onClick={add}>{busy?"正在加入…":"加入购物车"}</button><p aria-live="polite">{message}</p></div></section></main>
}
createRoot(document.getElementById("root")!).render(<App/>);

