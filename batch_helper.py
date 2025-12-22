    def _batch_upload_data(self, endpoint: str, data_key: str, items: List[Dict], 
                          extra_body: Dict = None, batch_size: int = API_BATCH_SIZE) -> Dict[str, Any]:
        """
        Helper to upload data in batches.
        
        Args:
            endpoint: API endpoint
            data_key: Key for the list of items in the body (e.g., "cards", "changes")
            items: List of items to upload
            extra_body: Additional fields for the body
            batch_size: Number of items per batch
            
        Returns:
            Aggregated result dictionary
        """
        if not items:
            return {"success": True, "processed": 0}
            
        total = len(items)
        # Use a sensible batch size from constants
        chunk_size = min(batch_size, API_MAX_BATCH_SIZE)
        
        logger.info(f"Starting batch upload: {total} items to {endpoint} (batch size: {chunk_size})")
        
        aggregated_stats = {"processed": 0}
        
        for i in range(0, total, chunk_size):
            batch = items[i:i+chunk_size]
            body = {data_key: batch}
            if extra_body:
                body.update(extra_body)
                
            try:
                result = self.post(endpoint, json_body=body)
                
                # Aggregate stats if returned keys are numeric
                if isinstance(result, dict):
                    for k, v in result.items():
                        if isinstance(v, (int, float)) and not isinstance(v, bool):
                            aggregated_stats[k] = aggregated_stats.get(k, 0) + v
                        elif k not in aggregated_stats:
                            aggregated_stats[k] = v
                            
                aggregated_stats["processed"] += len(batch)
                logger.info(f"Uploaded batch {i//chunk_size + 1}: {len(batch)} items")
                
            except Exception as e:
                logger.error(f"Batch upload failed at offset {i}: {e}")
                return {
                    "success": False, 
                    "error": str(e), 
                    "processed": aggregated_stats["processed"]
                }
                
        aggregated_stats["success"] = True
        return aggregated_stats
