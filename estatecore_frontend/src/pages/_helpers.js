
import client from "../api";
export async function fetchWithFallback(url, fallbackData){
  try{
    const { data } = await client.get(url);
    if(Array.isArray(data)) return data;
    if(Array.isArray(data?.items)) return data.items;
    return data || fallbackData;
  }catch(e){ return fallbackData; }
}
