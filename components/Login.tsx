"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"

export default function Login(){

const [email,setEmail]=useState("")
const router = useRouter()

function login(){

localStorage.setItem("advisorEmail",email)

router.push("/dashboard")

}

return(

<div className="flex flex-col items-center justify-center h-screen">

<h1 className="text-3xl mb-6">Advisor Dashboard</h1>

<input
className="border p-2"
placeholder="Enter your email"
value={email}
onChange={(e)=>setEmail(e.target.value)}
/>

<button
className="bg-blue-500 text-white p-2 mt-4"
onClick={login}
>

Login

</button>

</div>

)
}
