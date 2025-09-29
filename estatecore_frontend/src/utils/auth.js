// Fix: jwt-decode uses named export in v4
import { jwtDecode } from 'jwt-decode'
const KEY = 'estatecore.session'
export function saveSession(token){
  const decoded = jwtDecode(token)
  localStorage.setItem(KEY, JSON.stringify({ token, decoded }))
}
export function getSession(){ try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch{return{}} }
export function clearSession(){ localStorage.removeItem(KEY) }

