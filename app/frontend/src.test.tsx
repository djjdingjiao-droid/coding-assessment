import {afterEach, describe, expect, it, vi} from "vitest";
import {cleanup, fireEvent, render, screen, waitFor} from "@testing-library/react";
import {App} from "./src";

const product = {id:"trail-jacket",name:"Trail Jacket",description:"x",options:{colour:["Ocean","Clay"],size:["S","M"]},skus:[
  {id:"ocean-s",options:{colour:"Ocean",size:"S"},price_cents:12900,available_quantity:1,image:"x"},
  {id:"ocean-m",options:{colour:"Ocean",size:"M"},price_cents:12900,available_quantity:0,image:"x"},
  {id:"clay-s",options:{colour:"Clay",size:"S"},price_cents:13500,available_quantity:2,image:"x"}
]};
afterEach(()=>{cleanup(); vi.restoreAllMocks();});
function mockFetch(){ return vi.spyOn(globalThis,"fetch").mockImplementation((url, init)=>Promise.resolve(new Response(JSON.stringify(String(url).includes("products")?product:String(url).includes("/cart")&&!init?{item_count:0}:{cart:{item_count:1}}),{status:200}))); }

describe("PDP",()=>{
  it("未选完整规格时给出提示", async()=>{mockFetch(); render(<App/>); await screen.findByText("Trail Jacket"); expect(screen.getByText("请选择有效规格。")).toBeTruthy();});
  it("选择可售规格后更新库存和数量上限", async()=>{mockFetch(); render(<App/>); await screen.findByText("Trail Jacket"); fireEvent.click(screen.getByText("Ocean")); fireEvent.click(screen.getByText("S")); expect(screen.getByText("库存：1")).toBeTruthy(); expect(screen.getByLabelText("数量").getAttribute("max")).toBe("1");});
  it("提交中禁用重复加购", async()=>{let release: (value:Response)=>void; const pending=new Promise<Response>(r=>release=r); vi.spyOn(globalThis,"fetch").mockImplementation((url, init)=>String(url).includes("products")?Promise.resolve(new Response(JSON.stringify(product))):String(url).includes("/cart")&&!init?Promise.resolve(new Response(JSON.stringify({item_count:0}))):pending); render(<App/>); await screen.findByText("Trail Jacket"); fireEvent.click(screen.getByText("Ocean")); fireEvent.click(screen.getByText("S")); fireEvent.click(screen.getByText("加入购物车")); expect(screen.getByText("正在加入…")).toBeTruthy(); release!(new Response(JSON.stringify({cart:{item_count:1}}))); await waitFor(()=>expect(screen.getByText("已加入购物车。")).toBeTruthy());});
});
