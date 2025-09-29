import logging
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import requests
from web3 import Web3
from eth_account import Account

from flask import current_app
from estatecore_backend.models import db, User, Property
from services.rbac_service import require_permission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BlockchainNetwork(Enum):
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BINANCE = "binance_smart_chain"
    PRIVATE = "private_network"

class TransactionStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RecordType(Enum):
    PROPERTY_DEED = "property_deed"
    LEASE_AGREEMENT = "lease_agreement"
    PAYMENT_RECORD = "payment_record"
    MAINTENANCE_LOG = "maintenance_log"
    INSPECTION_REPORT = "inspection_report"
    OWNERSHIP_TRANSFER = "ownership_transfer"
    RENTAL_HISTORY = "rental_history"

@dataclass
class BlockchainTransaction:
    id: str
    record_type: RecordType
    transaction_hash: Optional[str]
    block_number: Optional[int]
    network: BlockchainNetwork
    status: TransactionStatus
    gas_used: Optional[int]
    gas_price: Optional[int]
    data_hash: str
    metadata: Dict[str, Any]
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'record_type': self.record_type.value,
            'transaction_hash': self.transaction_hash,
            'block_number': self.block_number,
            'network': self.network.value,
            'status': self.status.value,
            'gas_used': self.gas_used,
            'gas_price': self.gas_price,
            'data_hash': self.data_hash,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None
        }

@dataclass
class PropertyRecord:
    property_id: int
    record_type: RecordType
    data: Dict[str, Any]
    hash: str
    timestamp: datetime
    blockchain_tx_id: Optional[str] = None
    ipfs_hash: Optional[str] = None
    signatures: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self):
        return {
            'property_id': self.property_id,
            'record_type': self.record_type.value,
            'data': self.data,
            'hash': self.hash,
            'timestamp': self.timestamp.isoformat(),
            'blockchain_tx_id': self.blockchain_tx_id,
            'ipfs_hash': self.ipfs_hash,
            'signatures': self.signatures
        }

class BlockchainService:
    """Blockchain integration service for property records"""
    
    def __init__(self):
        self.networks = {
            BlockchainNetwork.ETHEREUM: {
                'rpc_url': 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID',
                'chain_id': 1,
                'contract_address': '0x...',  # Property records contract
                'gas_limit': 200000
            },
            BlockchainNetwork.POLYGON: {
                'rpc_url': 'https://polygon-rpc.com/',
                'chain_id': 137,
                'contract_address': '0x...',
                'gas_limit': 150000
            },
            BlockchainNetwork.PRIVATE: {
                'rpc_url': 'http://localhost:8545',
                'chain_id': 1337,
                'contract_address': '0x...',
                'gas_limit': 100000
            }
        }
        
        self.transactions: Dict[str, BlockchainTransaction] = {}
        self.property_records: Dict[str, PropertyRecord] = {}
        self.active_network = BlockchainNetwork.PRIVATE
        self.private_key = None  # Set from environment
        self.contract_abi = self._load_contract_abi()
        
        # IPFS configuration
        self.ipfs_api_url = "https://ipfs.infura.io:5001/api/v0"
        self.ipfs_gateway = "https://ipfs.io/ipfs/"
        
    def _load_contract_abi(self) -> List[Dict]:
        """Load smart contract ABI"""
        # Simplified ABI for property records contract
        return [
            {
                "inputs": [
                    {"name": "_propertyId", "type": "uint256"},
                    {"name": "_recordType", "type": "string"},
                    {"name": "_dataHash", "type": "string"},
                    {"name": "_ipfsHash", "type": "string"}
                ],
                "name": "createPropertyRecord",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "_recordId", "type": "uint256"}],
                "name": "getPropertyRecord",
                "outputs": [
                    {"name": "propertyId", "type": "uint256"},
                    {"name": "recordType", "type": "string"},
                    {"name": "dataHash", "type": "string"},
                    {"name": "ipfsHash", "type": "string"},
                    {"name": "timestamp", "type": "uint256"},
                    {"name": "isValid", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "_propertyId", "type": "uint256"}],
                "name": "getPropertyRecords",
                "outputs": [{"name": "", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def store_property_record(self, property_id: int, record_type: RecordType, 
                             data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Store property record on blockchain"""
        try:
            # Validate property exists
            property_obj = Property.query.get(property_id)
            if not property_obj:
                return {'success': False, 'error': 'Property not found'}
            
            # Create data hash
            data_json = json.dumps(data, sort_keys=True)
            data_hash = hashlib.sha256(data_json.encode()).hexdigest()
            
            # Store data on IPFS first
            ipfs_result = self._store_on_ipfs(data)
            if not ipfs_result['success']:
                return {'success': False, 'error': 'Failed to store data on IPFS'}
            
            ipfs_hash = ipfs_result['hash']
            
            # Create property record
            record_id = str(uuid.uuid4())
            property_record = PropertyRecord(
                property_id=property_id,
                record_type=record_type,
                data=data,
                hash=data_hash,
                timestamp=datetime.utcnow(),
                ipfs_hash=ipfs_hash
            )
            
            # Store record on blockchain
            blockchain_result = self._store_on_blockchain(property_record, user_id)
            if blockchain_result['success']:
                property_record.blockchain_tx_id = blockchain_result['transaction_id']
            
            # Store record locally
            self.property_records[record_id] = property_record
            
            logger.info(f"Property record stored: {record_id} for property {property_id}")
            
            return {
                'success': True,
                'record_id': record_id,
                'data_hash': data_hash,
                'ipfs_hash': ipfs_hash,
                'blockchain_tx_id': property_record.blockchain_tx_id,
                'message': 'Property record stored successfully'
            }
            
        except Exception as e:
            logger.error(f"Error storing property record: {str(e)}")
            return {'success': False, 'error': 'Failed to store property record'}
    
    def verify_property_record(self, record_id: str) -> Dict[str, Any]:
        """Verify property record integrity"""
        try:
            if record_id not in self.property_records:
                return {'success': False, 'error': 'Record not found'}
            
            record = self.property_records[record_id]
            
            # Verify data hash
            data_json = json.dumps(record.data, sort_keys=True)
            calculated_hash = hashlib.sha256(data_json.encode()).hexdigest()
            
            hash_valid = calculated_hash == record.hash
            
            # Verify blockchain transaction if available
            blockchain_valid = True
            if record.blockchain_tx_id:
                blockchain_result = self._verify_blockchain_transaction(record.blockchain_tx_id)
                blockchain_valid = blockchain_result['valid']
            
            # Verify IPFS data if available
            ipfs_valid = True
            if record.ipfs_hash:
                ipfs_result = self._verify_ipfs_data(record.ipfs_hash, record.data)
                ipfs_valid = ipfs_result['valid']
            
            verification_result = {
                'record_id': record_id,
                'hash_valid': hash_valid,
                'blockchain_valid': blockchain_valid,
                'ipfs_valid': ipfs_valid,
                'overall_valid': hash_valid and blockchain_valid and ipfs_valid,
                'verification_timestamp': datetime.utcnow().isoformat()
            }
            
            return {
                'success': True,
                'verification': verification_result
            }
            
        except Exception as e:
            logger.error(f"Error verifying record: {str(e)}")
            return {'success': False, 'error': 'Failed to verify record'}
    
    def get_property_blockchain_history(self, property_id: int) -> Dict[str, Any]:
        """Get complete blockchain history for a property"""
        try:
            # Get all records for the property
            property_records = [
                record for record in self.property_records.values()
                if record.property_id == property_id
            ]
            
            # Sort by timestamp
            property_records.sort(key=lambda x: x.timestamp)
            
            # Get blockchain transactions
            blockchain_txs = []
            for record in property_records:
                if record.blockchain_tx_id and record.blockchain_tx_id in self.transactions:
                    blockchain_txs.append(self.transactions[record.blockchain_tx_id])
            
            # Create timeline
            timeline = []
            for record in property_records:
                timeline.append({
                    'timestamp': record.timestamp.isoformat(),
                    'record_type': record.record_type.value,
                    'hash': record.hash,
                    'blockchain_confirmed': record.blockchain_tx_id is not None,
                    'ipfs_stored': record.ipfs_hash is not None
                })
            
            return {
                'success': True,
                'property_id': property_id,
                'total_records': len(property_records),
                'blockchain_transactions': len(blockchain_txs),
                'timeline': timeline,
                'records': [record.to_dict() for record in property_records]
            }
            
        except Exception as e:
            logger.error(f"Error getting property history: {str(e)}")
            return {'success': False, 'error': 'Failed to get property history'}
    
    def transfer_property_ownership(self, property_id: int, from_user_id: int, 
                                   to_user_id: int, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record property ownership transfer on blockchain"""
        try:
            # Validate users
            from_user = User.query.get(from_user_id)
            to_user = User.query.get(to_user_id)
            
            if not from_user or not to_user:
                return {'success': False, 'error': 'Invalid user(s)'}
            
            # Create transfer record
            transfer_record = {
                'transfer_type': 'ownership',
                'from_user': {
                    'id': from_user_id,
                    'name': from_user.username,
                    'email': from_user.email
                },
                'to_user': {
                    'id': to_user_id,
                    'name': to_user.username,
                    'email': to_user.email
                },
                'transfer_date': datetime.utcnow().isoformat(),
                'transfer_data': transfer_data,
                'legal_documents': transfer_data.get('legal_documents', []),
                'consideration': transfer_data.get('consideration', 0),
                'conditions': transfer_data.get('conditions', [])
            }
            
            # Store on blockchain
            result = self.store_property_record(
                property_id=property_id,
                record_type=RecordType.OWNERSHIP_TRANSFER,
                data=transfer_record,
                user_id=from_user_id
            )
            
            if result['success']:
                # Update property ownership in database
                property_obj = Property.query.get(property_id)
                if property_obj:
                    property_obj.owner_id = to_user_id
                    db.session.commit()
                
                logger.info(f"Property ownership transferred: {property_id} from {from_user_id} to {to_user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error transferring ownership: {str(e)}")
            return {'success': False, 'error': 'Failed to transfer ownership'}
    
    def create_lease_agreement(self, property_id: int, tenant_id: int, 
                              lease_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create immutable lease agreement on blockchain"""
        try:
            # Create comprehensive lease record
            lease_record = {
                'lease_type': 'residential',  # or commercial
                'property_id': property_id,
                'tenant_id': tenant_id,
                'landlord_id': lease_data.get('landlord_id'),
                'lease_terms': {
                    'start_date': lease_data.get('start_date'),
                    'end_date': lease_data.get('end_date'),
                    'rent_amount': lease_data.get('rent_amount'),
                    'deposit_amount': lease_data.get('deposit_amount'),
                    'payment_frequency': lease_data.get('payment_frequency', 'monthly'),
                    'late_fee': lease_data.get('late_fee', 0),
                    'utilities_included': lease_data.get('utilities_included', [])
                },
                'clauses': lease_data.get('clauses', []),
                'restrictions': lease_data.get('restrictions', []),
                'maintenance_responsibility': lease_data.get('maintenance_responsibility', {}),
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            # Store on blockchain
            result = self.store_property_record(
                property_id=property_id,
                record_type=RecordType.LEASE_AGREEMENT,
                data=lease_record,
                user_id=lease_data.get('landlord_id')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating lease agreement: {str(e)}")
            return {'success': False, 'error': 'Failed to create lease agreement'}
    
    def record_payment(self, property_id: int, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record payment on blockchain for immutable payment history"""
        try:
            payment_record = {
                'payment_id': payment_data.get('payment_id'),
                'tenant_id': payment_data.get('tenant_id'),
                'amount': payment_data.get('amount'),
                'payment_type': payment_data.get('payment_type', 'rent'),
                'payment_method': payment_data.get('payment_method'),
                'payment_date': payment_data.get('payment_date'),
                'due_date': payment_data.get('due_date'),
                'late_fees': payment_data.get('late_fees', 0),
                'receipt_number': payment_data.get('receipt_number'),
                'transaction_reference': payment_data.get('transaction_reference'),
                'recorded_at': datetime.utcnow().isoformat()
            }
            
            result = self.store_property_record(
                property_id=property_id,
                record_type=RecordType.PAYMENT_RECORD,
                data=payment_record,
                user_id=payment_data.get('tenant_id')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error recording payment: {str(e)}")
            return {'success': False, 'error': 'Failed to record payment'}
    
    def get_blockchain_analytics(self) -> Dict[str, Any]:
        """Get blockchain system analytics"""
        try:
            total_records = len(self.property_records)
            total_transactions = len(self.transactions)
            
            # Count by record type
            record_type_counts = {}
            for record in self.property_records.values():
                record_type = record.record_type.value
                record_type_counts[record_type] = record_type_counts.get(record_type, 0) + 1
            
            # Transaction status counts
            status_counts = {}
            for tx in self.transactions.values():
                status = tx.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Network usage
            network_counts = {}
            for tx in self.transactions.values():
                network = tx.network.value
                network_counts[network] = network_counts.get(network, 0) + 1
            
            # Calculate costs (mock)
            total_gas_used = sum(tx.gas_used or 0 for tx in self.transactions.values())
            avg_gas_price = sum(tx.gas_price or 0 for tx in self.transactions.values()) / len(self.transactions) if self.transactions else 0
            
            return {
                'success': True,
                'analytics': {
                    'total_records': total_records,
                    'total_transactions': total_transactions,
                    'record_types': record_type_counts,
                    'transaction_status': status_counts,
                    'network_usage': network_counts,
                    'gas_analytics': {
                        'total_gas_used': total_gas_used,
                        'average_gas_price': avg_gas_price,
                        'estimated_cost_eth': total_gas_used * avg_gas_price / 1e18 if avg_gas_price else 0
                    },
                    'success_rate': status_counts.get('confirmed', 0) / total_transactions if total_transactions else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            return {'success': False, 'error': 'Failed to get analytics'}
    
    def _store_on_blockchain(self, record: PropertyRecord, user_id: int) -> Dict[str, Any]:
        """Store record on blockchain network"""
        try:
            # Create blockchain transaction
            tx_id = str(uuid.uuid4())
            
            # Mock blockchain transaction - in production, use actual Web3 calls
            blockchain_tx = BlockchainTransaction(
                id=tx_id,
                record_type=record.record_type,
                transaction_hash=f"0x{hashlib.sha256(tx_id.encode()).hexdigest()}",
                block_number=None,  # Will be set when confirmed
                network=self.active_network,
                status=TransactionStatus.PENDING,
                gas_used=None,
                gas_price=None,
                data_hash=record.hash,
                metadata={
                    'property_id': record.property_id,
                    'user_id': user_id,
                    'ipfs_hash': record.ipfs_hash
                },
                created_at=datetime.utcnow()
            )
            
            self.transactions[tx_id] = blockchain_tx
            
            # Simulate blockchain confirmation after delay
            import threading
            def confirm_transaction():
                time.sleep(5)  # Simulate blockchain confirmation time
                blockchain_tx.status = TransactionStatus.CONFIRMED
                blockchain_tx.block_number = 12345678  # Mock block number
                blockchain_tx.gas_used = 150000
                blockchain_tx.gas_price = 20000000000  # 20 gwei
                blockchain_tx.confirmed_at = datetime.utcnow()
            
            threading.Thread(target=confirm_transaction).start()
            
            return {
                'success': True,
                'transaction_id': tx_id,
                'transaction_hash': blockchain_tx.transaction_hash
            }
            
        except Exception as e:
            logger.error(f"Error storing on blockchain: {str(e)}")
            return {'success': False, 'error': 'Failed to store on blockchain'}
    
    def _store_on_ipfs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Store data on IPFS"""
        try:
            # Mock IPFS storage - in production, use actual IPFS API
            data_json = json.dumps(data, sort_keys=True)
            ipfs_hash = f"Qm{hashlib.sha256(data_json.encode()).hexdigest()[:44]}"
            
            logger.info(f"Mock IPFS storage: {ipfs_hash}")
            
            return {
                'success': True,
                'hash': ipfs_hash,
                'size': len(data_json)
            }
            
        except Exception as e:
            logger.error(f"Error storing on IPFS: {str(e)}")
            return {'success': False, 'error': 'Failed to store on IPFS'}
    
    def _verify_blockchain_transaction(self, tx_id: str) -> Dict[str, Any]:
        """Verify blockchain transaction"""
        try:
            if tx_id not in self.transactions:
                return {'valid': False, 'error': 'Transaction not found'}
            
            tx = self.transactions[tx_id]
            
            # Mock verification - in production, verify on actual blockchain
            is_valid = tx.status == TransactionStatus.CONFIRMED
            
            return {
                'valid': is_valid,
                'transaction_hash': tx.transaction_hash,
                'block_number': tx.block_number,
                'confirmation_time': tx.confirmed_at.isoformat() if tx.confirmed_at else None
            }
            
        except Exception as e:
            logger.error(f"Error verifying blockchain transaction: {str(e)}")
            return {'valid': False, 'error': 'Failed to verify transaction'}
    
    def _verify_ipfs_data(self, ipfs_hash: str, expected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify data stored on IPFS"""
        try:
            # Mock IPFS verification - in production, retrieve and compare actual data
            expected_json = json.dumps(expected_data, sort_keys=True)
            expected_hash = f"Qm{hashlib.sha256(expected_json.encode()).hexdigest()[:44]}"
            
            is_valid = ipfs_hash == expected_hash
            
            return {
                'valid': is_valid,
                'ipfs_hash': ipfs_hash,
                'data_integrity': is_valid
            }
            
        except Exception as e:
            logger.error(f"Error verifying IPFS data: {str(e)}")
            return {'valid': False, 'error': 'Failed to verify IPFS data'}

# Global blockchain service instance
blockchain_service = BlockchainService()