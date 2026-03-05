
"use client"

import { useEffect,useState } from "react"
import { fetchSheet } from "../lib/sheets"
import { LineChart,Line,XAxis,YAxis,Tooltip } from "recharts"

export default function Dashboard(){

const [data,setData]=useState([])
const [email,setEmail]=useState("")

const KPI_URL="PASTE_KPI_SHEET_CSV_URL"

useEffect(()=>{

const userEmail = localStorage.getItem("advisorEmail")

setEmail(userEmail || "")

loadData(userEmail)

},[])

async function loadData(userEmail:string){

const kpi:any = await fetchSheet(KPI_URL)

const filtered = kpi.filter((row:any)=>row.Email===userEmail)

setData(filtered)

}

return(

<div className="p-10">

<h1 className="text-3xl mb-6">

Advisor Performance

</h1>

<LineChart width={700} height={300} data={data}>

<XAxis dataKey="Date"/>

<YAxis/>

<Tooltip/>

<Line type="monotone" dataKey="Shift_Score" stroke="#8884d8"/>

</LineChart>

</div>

)

}
