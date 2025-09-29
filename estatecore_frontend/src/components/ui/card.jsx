export function Card({children, className=''}){
  return <div className={`bg-white rounded-lg shadow ${className}`}>{children}</div>
} 

export function CardHeader({children}){
  return <div className='px-6 py-4 border-b border-gray-200'>{children}</div>
} 

export function CardTitle({children, className=''}){
  return <h3 className={`text-lg font-medium text-gray-900 ${className}`}>{children}</h3>
}

export function CardContent({children}){
  return <div className='p-6'>{children}</div>
}
