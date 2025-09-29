
import React from 'react'
export default function RequireRole({ roles = [], children, fallback = null }){
  // Placeholder: always show (hook to your auth/session)
  return <>{children}</>
}
