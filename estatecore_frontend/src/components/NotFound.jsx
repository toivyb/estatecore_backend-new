// src/components/NotFound.jsx
import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div style={{ textAlign: 'center', marginTop: '4rem' }}>
      <h1>404: Page Not Found</h1>
      <p>Sorry, we couldn’t find what you were looking for.</p>
      <Link to="/" style={{ color: '#0066cc' }}>
        Go back home
      </Link>
    </div>
  );
}
