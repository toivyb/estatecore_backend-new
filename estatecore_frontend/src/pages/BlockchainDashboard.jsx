import React, { useState, useEffect } from 'react';
import { 
  CircleStackIcon, 
  HashtagIcon, 
  ArrowTrendingUpIcon, 
  ChartBarIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  ClockIcon,
  KeyIcon,
  EyeIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const BlockchainDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchBlockchainData();
    const interval = setInterval(fetchBlockchainData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchBlockchainData = async () => {
    try {
      setIsLoading(true);
      
      // Mock data - replace with actual API calls
      const mockData = {
        statistics: {
          total_records: 1247,
          total_transactions: 1189,
          record_types: {
            property_deed: 156,
            lease_agreement: 423,
            payment_record: 567,
            maintenance_log: 89,
            ownership_transfer: 12
          },
          transaction_status: {
            confirmed: 1156,
            pending: 23,
            failed: 10
          },
          network_usage: {
            ethereum: 245,
            polygon: 789,
            private_network: 155
          },
          gas_analytics: {
            total_gas_used: 2456789,
            average_gas_price: 25000000000,
            estimated_cost_eth: 0.0614
          },
          success_rate: 0.972
        },
        recent_transactions: [
          {
            id: 'tx-001',
            record_type: 'payment_record',
            transaction_hash: '0x1234567890abcdef...',
            block_number: 12345678,
            network: 'polygon',
            status: 'confirmed',
            gas_used: 150000,
            created_at: '2024-09-27T14:30:00Z',
            metadata: { property_id: 123, amount: 1200 }
          },
          {
            id: 'tx-002',
            record_type: 'lease_agreement',
            transaction_hash: '0xabcdef1234567890...',
            block_number: 12345679,
            network: 'ethereum',
            status: 'confirmed',
            gas_used: 200000,
            created_at: '2024-09-27T13:15:00Z',
            metadata: { property_id: 456, tenant_id: 789 }
          },
          {
            id: 'tx-003',
            record_type: 'ownership_transfer',
            transaction_hash: '0xfedcba0987654321...',
            block_number: null,
            network: 'ethereum',
            status: 'pending',
            gas_used: null,
            created_at: '2024-09-27T15:45:00Z',
            metadata: { property_id: 789, from_user: 123, to_user: 456 }
          }
        ],
        recent_records: [
          {
            property_id: 123,
            record_type: 'payment_record',
            hash: 'abc123def456...',
            timestamp: '2024-09-27T14:30:00Z',
            blockchain_tx_id: 'tx-001',
            ipfs_hash: 'QmXYZ789...',
            data: { amount: 1200, payment_type: 'rent' }
          },
          {
            property_id: 456,
            record_type: 'lease_agreement',
            hash: 'def456ghi789...',
            timestamp: '2024-09-27T13:15:00Z',
            blockchain_tx_id: 'tx-002',
            ipfs_hash: 'QmABC123...',
            data: { lease_term: '12 months', rent: 1500 }
          }
        ],
        system_status: {
          network_connected: true,
          ipfs_connected: true,
          last_block_processed: 12345680,
          pending_transactions: 23
        }
      };
      
      setDashboardData(mockData);
    } catch (error) {
      console.error('Error fetching blockchain data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'confirmed': return 'text-green-600 bg-green-100 border-green-200';
      case 'pending': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'failed': return 'text-red-600 bg-red-100 border-red-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  const getNetworkColor = (network) => {
    switch (network) {
      case 'ethereum': return 'text-blue-600 bg-blue-100';
      case 'polygon': return 'text-purple-600 bg-purple-100';
      case 'binance_smart_chain': return 'text-yellow-600 bg-yellow-100';
      case 'private_network': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRecordTypeIcon = (type) => {
    switch (type) {
      case 'property_deed': return <DocumentTextIcon className="w-4 h-4" />;
      case 'lease_agreement': return <ShieldCheckIcon className="w-4 h-4" />;
      case 'payment_record': return <ChartBarIcon className="w-4 h-4" />;
      case 'maintenance_log': return <ClockIcon className="w-4 h-4" />;
      case 'ownership_transfer': return <KeyIcon className="w-4 h-4" />;
      default: return <CircleStackIcon className="w-4 h-4" />;
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(new Date(timestamp));
  };

  const formatHash = (hash, length = 12) => {
    if (!hash) return 'N/A';
    return `${hash.substring(0, length)}...`;
  };

  const verifyRecord = async (recordId) => {
    try {
      // Mock verification - replace with actual API call
      console.log('Verifying record:', recordId);
      alert('Record verification completed successfully!');
    } catch (error) {
      console.error('Error verifying record:', error);
    }
  };

  const StatCard = ({ title, value, icon: Icon, color = 'blue', subtitle = null }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-full bg-${color}-100 dark:bg-${color}-900/20`}>
          <Icon className={`w-6 h-6 text-${color}-600 dark:text-${color}-400`} />
        </div>
      </div>
    </div>
  );

  const TransactionCard = ({ transaction }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-full bg-blue-100 dark:bg-blue-900/20">
            {getRecordTypeIcon(transaction.record_type)}
          </div>
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white capitalize">
              {transaction.record_type.replace('_', ' ')}
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {formatTimestamp(transaction.created_at)}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(transaction.status)}`}>
            {transaction.status}
          </span>
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getNetworkColor(transaction.network)}`}>
            {transaction.network}
          </span>
        </div>
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">Hash:</span>
          <span className="font-mono text-gray-900 dark:text-white">
            {formatHash(transaction.transaction_hash)}
          </span>
        </div>
        
        {transaction.block_number && (
          <div className="flex justify-between">
            <span className="text-gray-500 dark:text-gray-400">Block:</span>
            <span className="font-mono text-gray-900 dark:text-white">
              #{transaction.block_number}
            </span>
          </div>
        )}
        
        {transaction.gas_used && (
          <div className="flex justify-between">
            <span className="text-gray-500 dark:text-gray-400">Gas Used:</span>
            <span className="font-mono text-gray-900 dark:text-white">
              {transaction.gas_used.toLocaleString()}
            </span>
          </div>
        )}
      </div>
      
      <div className="mt-3 flex justify-end">
        <button
          onClick={() => setSelectedRecord(transaction)}
          className="flex items-center px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <EyeIcon className="w-3 h-3 mr-1" />
          View Details
        </button>
      </div>
    </div>
  );

  const RecordCard = ({ record }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-full bg-green-100 dark:bg-green-900/20">
            {getRecordTypeIcon(record.record_type)}
          </div>
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white capitalize">
              {record.record_type.replace('_', ' ')}
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Property #{record.property_id}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-1">
          {record.blockchain_tx_id && <CheckCircleIcon className="w-4 h-4 text-green-500" />}
          {record.ipfs_hash && <CircleStackIcon className="w-4 h-4 text-blue-500" />}
        </div>
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">Hash:</span>
          <span className="font-mono text-gray-900 dark:text-white">
            {formatHash(record.hash)}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-500 dark:text-gray-400">Timestamp:</span>
          <span className="text-gray-900 dark:text-white">
            {formatTimestamp(record.timestamp)}
          </span>
        </div>
      </div>
      
      <div className="mt-3 flex justify-end space-x-2">
        <button
          onClick={() => verifyRecord(record.hash)}
          className="flex items-center px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
        >
          <ShieldCheckIcon className="w-3 h-3 mr-1" />
          Verify
        </button>
        <button
          onClick={() => setSelectedRecord(record)}
          className="flex items-center px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <EyeIcon className="w-3 h-3 mr-1" />
          View
        </button>
      </div>
    </div>
  );

  if (isLoading || !dashboardData) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Blockchain Dashboard</h1>
              <p className="text-gray-600 dark:text-gray-400">Property records on distributed ledger</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${dashboardData.system_status.network_connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {dashboardData.system_status.network_connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Records"
            value={dashboardData.statistics.total_records.toLocaleString()}
            icon={CircleStackIcon}
            color="blue"
            subtitle="Stored on blockchain"
          />
          <StatCard
            title="Transactions"
            value={dashboardData.statistics.total_transactions.toLocaleString()}
            icon={HashtagIcon}
            color="green"
            subtitle={`${dashboardData.statistics.transaction_status.pending} pending`}
          />
          <StatCard
            title="Success Rate"
            value={`${(dashboardData.statistics.success_rate * 100).toFixed(1)}%`}
            icon={ArrowTrendingUpIcon}
            color="purple"
            subtitle="Transaction success"
          />
          <StatCard
            title="Gas Cost"
            value={`${dashboardData.statistics.gas_analytics.estimated_cost_eth.toFixed(4)} ETH`}
            icon={ChartBarIcon}
            color="orange"
            subtitle="Total spent"
          />
        </div>

        {/* System Status */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Network Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Blockchain</span>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-green-600">Connected</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">IPFS</span>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-green-600">Connected</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Latest Block</span>
                <span className="text-sm font-mono text-gray-900 dark:text-white">
                  #{dashboardData.system_status.last_block_processed}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Record Types</h3>
            <div className="space-y-2">
              {Object.entries(dashboardData.statistics.record_types).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getRecordTypeIcon(type)}
                    <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                      {type.replace('_', ' ')}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Network Usage</h3>
            <div className="space-y-2">
              {Object.entries(dashboardData.statistics.network_usage).map(([network, count]) => (
                <div key={network} className="flex items-center justify-between">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getNetworkColor(network)}`}>
                    {network.replace('_', ' ')}
                  </span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'overview', label: 'Overview', icon: ChartBarIcon },
                { id: 'transactions', label: 'Transactions', icon: HashtagIcon },
                { id: 'records', label: 'Records', icon: DocumentTextIcon },
                { id: 'analytics', label: 'Analytics', icon: ArrowTrendingUpIcon }
              ].map(tab => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Content based on active tab */}
        {activeTab === 'transactions' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {dashboardData.recent_transactions.map(transaction => (
                <TransactionCard key={transaction.id} transaction={transaction} />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'records' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {dashboardData.recent_records.map((record, index) => (
                <RecordCard key={index} record={record} />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Transactions</h3>
              <div className="space-y-4">
                {dashboardData.recent_transactions.slice(0, 3).map(transaction => (
                  <div key={transaction.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700">
                    <div className="flex items-center space-x-3">
                      {getRecordTypeIcon(transaction.record_type)}
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                          {transaction.record_type.replace('_', ' ')}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {formatTimestamp(transaction.created_at)}
                        </p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(transaction.status)}`}>
                      {transaction.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Records</h3>
              <div className="space-y-4">
                {dashboardData.recent_records.slice(0, 3).map((record, index) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700">
                    <div className="flex items-center space-x-3">
                      {getRecordTypeIcon(record.record_type)}
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                          {record.record_type.replace('_', ' ')}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          Property #{record.property_id}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-1">
                      {record.blockchain_tx_id && <CheckCircleIcon className="w-4 h-4 text-green-500" />}
                      {record.ipfs_hash && <CircleStackIcon className="w-4 h-4 text-blue-500" />}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Record Details Modal */}
        {selectedRecord && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen px-4">
              <div className="fixed inset-0 bg-black opacity-50" onClick={() => setSelectedRecord(null)}></div>
              <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Record Details
                    </h3>
                    <button
                      onClick={() => setSelectedRecord(null)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                
                <div className="px-6 py-4 max-h-96 overflow-y-auto">
                  <pre className="text-sm bg-gray-100 dark:bg-gray-700 p-4 rounded-lg overflow-auto">
                    {JSON.stringify(selectedRecord, null, 2)}
                  </pre>
                </div>
                
                <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
                  <button
                    onClick={() => setSelectedRecord(null)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BlockchainDashboard;