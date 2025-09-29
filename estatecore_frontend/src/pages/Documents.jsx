import React from 'react'
import Layout from '../components/Layout'
import DocumentManager from '../components/DocumentManager'

const Documents = () => {
  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <DocumentManager />
      </div>
    </Layout>
  )
}

export default Documents