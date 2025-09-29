export default function Button({variant='primary', size='md', className='', ...props}){
  const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none';
  
  const variantClasses = {
    'primary': 'bg-blue-600 text-white hover:bg-blue-700',
    'secondary': 'bg-gray-200 text-gray-900 hover:bg-gray-300',
    'outline': 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
    'ghost': 'hover:bg-gray-100 text-gray-700',
    'destructive': 'bg-red-600 text-white hover:bg-red-700'
  };
  
  const sizeClasses = {
    'sm': 'h-8 px-3 text-sm',
    'md': 'h-10 py-2 px-4',
    'lg': 'h-11 px-8'
  };
  
  return (
    <button 
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`} 
      {...props}
    />
  );
}
