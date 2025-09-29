import { useEffect } from 'react';
export default function Modal({ isOpen, open, title='Edit', children, onClose, size='md' }) {
  const isModalOpen = isOpen ?? open; // Support both isOpen and open props
  
  useEffect(() => {
    function onKey(e){ if(e.key === 'Escape') onClose?.(); }
    if(isModalOpen){ window.addEventListener('keydown', onKey); }
    return () => window.removeEventListener('keydown', onKey);
  }, [isModalOpen, onClose]);
  
  if (!isModalOpen) return null;
  
  const sizeClasses = {
    'sm': 'max-w-md',
    'md': 'max-w-xl',
    'lg': 'max-w-4xl',
    'large': 'max-w-4xl'
  };
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className={`w-full ${sizeClasses[size] || sizeClasses.md} bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-xl`}>
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
          <button 
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" 
            onClick={onClose}
          >
            ✕
          </button>
        </div>
        <div className="p-6 text-gray-900 dark:text-white">{children}</div>
      </div>
    </div>
  );
}
