import React, { createContext, useContext } from 'react'
export const Ctx = createContext({ apiBase:'/api' })
export const useApi = () => useContext(Ctx).apiBase
export function ConfigProvider({ apiBase, children }){ return <Ctx.Provider value={{ apiBase }}>{children}</Ctx.Provider> }
