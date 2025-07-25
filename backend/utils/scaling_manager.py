# backend/utils/scaling_manager.py
class ScalingManager:
    def __init__(self):
        self.shard_config = {
            'max_docs_per_shard': 1000000,  # 1M documents per shard
            'max_index_size_gb': 50,        # 50GB per shard
            'replication_factor': 2         # 2 replicas per shard
        }
    
    def check_scaling_needs(self, db_connection):
        """Check if system needs scaling"""
        total_docs = db_connection.books.count_documents({'status': 'active'})
        index_size = self._calculate_index_size(db_connection)
        
        needs_scaling = (
            total_docs > self.shard_config['max_docs_per_shard'] or
            index_size > self.shard_config['max_index_size_gb']
        )
        
        return {
            'needs_scaling': needs_scaling,
            'current_docs': total_docs,
            'current_size_gb': index_size,
            'recommended_shards': self._calculate_recommended_shards(total_docs, index_size)
        }
    
    def implement_sharding(self, db_connection):
        """Implement database sharding for scaling"""
        # Create shard key based on book subject or date
        shard_key = {'subject': 1, 'upload_date': 1}
        
        # Enable sharding on database
        db_connection.admin.command('enableSharding', 'desidoc_library')
        
        # Shard the collections
        db_connection.admin.command(
            'shardCollection',
            'desidoc_library.books',
            key=shard_key
        )
        
        db_connection.admin.command(
            'shardCollection',
            'desidoc_library.search_index',
            key={'book_id': 1, 'word': 1}
        )
