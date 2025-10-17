import React from 'react'
import { Navigate } from 'react-router-dom'

export default function RoleProtectedRoute({ children, allowedRoles = [], redirectTo = '/' }) {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  
  // Check if user is authenticated
  if (!token) {
    return <Navigate to="/login" replace />
  }
  
  // Check if user has required role
  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to={redirectTo} replace />
  }
  
  return children
}