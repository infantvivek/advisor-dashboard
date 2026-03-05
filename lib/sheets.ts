import Papa from "papaparse";

export async function fetchSheet(url:string) {

const res = await fetch(url)
const text = await res.text()

return new Promise((resolve) => {
Papa.parse(text,{
header:true,
complete:(results)=>{
resolve(results.data)
}
})
})
}
