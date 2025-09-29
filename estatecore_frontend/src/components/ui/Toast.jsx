import { useEffect, useState } from 'react';

export default function Toast({ message, type='success', onClose }) {
  const [open, setOpen] = useState(true);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setOpen(false);
      onClose && onClose();
    }, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);
  
  if (!open) return null;
  
  const typeClasses = {
    'success': 'border-green-400 text-green-800 bg-green-50',
    'error': 'border-red-400 text-red-800 bg-red-50',
    'warning': 'border-yellow-400 text-yellow-800 bg-yellow-50',
    'info': 'border-blue-400 text-blue-800 bg-blue-50'
  };
  
  return (
    <div className="fixed bottom-5 right-5 z-50">
      <div className={`px-4 py-3 rounded-lg shadow-lg border ${typeClasses[type] || typeClasses.success}`}>
        <span className="text-sm font-medium">{message}</span>
      </div>
    </div>
  );
}
