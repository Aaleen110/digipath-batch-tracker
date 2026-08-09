## Task 5 — Whole Slide Imaging System Design

### Ingestion

WSI files are large (1–5 GB) and hospital connections may be unreliable or slow, so I would use AWS S3 multipart upload rather than sending the entire file through our API. The client uploads the file in chunks directly to S3. Each part can be retried independently, allowing an interrupted upload to resume without restarting from the beginning. Checksums can be used to verify uploaded parts.

### Storage
S3 would store the original WSI files as the primary storage layer. It is designed to handle large files reliably and removes the need for our application servers to manage heavy file uploads. I would initially store files in S3 Standard and use lifecycle policies to automatically move older slides to lower-cost storage tiers based on access patterns and retention requirements.

A metadata database such as PostgreSQL would keep track of information about each slide, including the hospital it belongs to, slide ID, S3 location, upload status, processing status, timestamps, and any processing errors.

### Processing

After a multipart upload completes, an S3 event would publish a message to Amazon SQS. Workers would consume messages asynchronously to perform tasks such as validation, thumbnail generation, and WSI analysis. Using a queue separates ingestion from processing so hospitals do not need to wait for expensive image processing.

### Failed or Partial Uploads

The system would keep track of upload progress so that if a hospital connection drops, the upload can continue from where it stopped instead of starting again. For processing failures, jobs would be retried a limited number of times, and any jobs that continue failing would be moved to a dead-letter queue so they can be investigated separately.

### 10x Growth

If the number of hospitals and concurrent uploads increased by 10x, I would expect the upload layer to continue working well because S3 multipart upload is already designed to handle large files and high concurrency. The first bottleneck would likely appear in the processing pipeline rather than ingestion.

With more slides arriving simultaneously, the processing queue could grow faster than workers can handle. To address this, I would scale the processing workers horizontally based on queue depth, add proper monitoring for processing delays, and introduce retry handling with dead-letter queues for failed jobs.

As the system grows, I would also consider adding fair scheduling or per-hospital rate limits so that one partner uploading a large number of slides does not impact other hospitals. If hospitals are distributed globally, I would evaluate multi-region storage and processing to reduce upload latency and distribute workload.

The key architectural principle is to keep ingestion and processing separate, allowing each side to scale independently.