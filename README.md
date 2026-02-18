# AWS Automated Greenhouse IoT Data Ingestion System

[ Update: The Greenhouse IoT API hosted by shef.ac.uk is now deprecated. Therefore, the API connection test in this project is skipped yet remains in the source code. See GitHub Actions for more. :)]
 
## Architectural Diagram
**Figure 1**

_Architectural Diagram of the Cloud System_

<img width="468" height="208" alt="image" src="https://github.com/user-attachments/assets/f4716c47-bfbd-44ad-87e1-61888c701631" />
    
In this project, the Greenhouse IoT data stream is ingested via a producer hosted on an Amazon EC2 instance (Virtual Machine) and buffered through Amazon Data Firehose, where AWS Lambda performs data transformation within Data Firehose before being stored in an S3 Data Lake. AWS Glue Crawlers scan the stored data to infer the schema and populate the Glue Data Catalog, enabling serverless SQL querying via Amazon Athena.

## Architectural Justifications
### <img width="20" height="20" alt="image" src="https://github.com/user-attachments/assets/3d3a0441-32af-4aec-b52e-c9346b3a004e" /> Amazon EC2

Amazon EC2 was selected to host a simple Python script which serves as an ingestion and transformation producer as it requires a persistent connection to the Greenhouse API stream. Although serverless alternatives like AWS Lambda can be used for polling new data, EC2 was chosen to make use of the scalability of using the API stream should the sensor data volume increase. AWS Lambda were ruled out in this case due to its 15-minute limited execution time limit, which would disrupt the continuous data stream and introduce potential data loss during restarts. Hence, EC2 upholds the performance of the digital twin system by uninterruptedly preserving the API stream connection.
Furthermore, EC2 offers cost-effective solution for this lightweight workload. In this project, a t2.micro instance is utilised, which falls within the AWS Free Tier. This approach eliminates the higher costs associated with other managed services such as AWS Fargate, whilst providing full control over the runtime environment. In addition, managed EC2 instances are scalable both vertically and horizontally according to demand, which allows us to maintain the performance of the digital twin system as data volume increases.

### <img width="20" height="20" alt="image" src="https://github.com/user-attachments/assets/a4f2c992-d2a2-4f58-a8d9-78c2f99c5585" /> Amazon Data Firehose

Amazon Data Firehose was chosen as a serverless, fully managed delivery and buffer service between the Python producer in EC2 and the S3 Data Lake. Given that the Greenhouse API stream sends infrequent and small bytes of data, Firehose is suitable for aggregating incoming records into batches configured with a buffer size and buffer interval, before being sent to S3. Furthermore, Data Firehose is fully scalable, enabling the adjustment of its buffer configurations in response to varying demand levels. This adaptability ensures optimal storage efficiency as data volumes expand.
For this architecture, the Firehose is configured with a 60-second buffer interval and a 1 MiB buffer size. This is because the data volume from the API stream is relatively low (~100-200 records/day). Although the minimum buffer interval in Firehose can be set to 0 second, this decision was made to balance the trade-off between providing near real-time performance in Digital Twin and mitigating the potential for creating significant numbers of small JSON files in the event of an abrupt and substantial surge in data volumes. By implementing this configuration, we avoid the “small file problem”, commonly known in distributed storage systems, which may potentially degrade the performance of SQL querying in Amazon Athena.

### <img width="20" height="20" alt="image" src="https://github.com/user-attachments/assets/c208f18a-8588-4764-925b-5927a410ca0d" /> AWS Lambda

In this architecture, AWS Lambda is implemented to parse, clean, and transform raw data from the API stream in real-time within Amazon Data Firehose prior to being transferred to S3. AWS Lambda is inexpensive as costs are only incurred when used. Additionally, AWS Lambda integrates efficiently with Data Firehose for in-flight data transformation.

### <img width="20" height="20" alt="image" src="https://github.com/user-attachments/assets/4b8ece54-5adc-4cff-a917-8defe82ff89d" /> Amazon S3

Amazon S3 was selected to serve as a centralised Data Lakehouse for this architecture due to its high durability (99.999999999%) and availability (99.99%), as well as its unlimited scalability and cost-effectiveness for unstructured data storage. Unlike traditional relational databases which require defined schemas and provisioned infrastructure, S3 supports a “Schema-on-Read” architecture, which allows the system to ingest raw JSON files via Firehose immediately whilst deferring table and schema definition to AWS Glue. Moreover, S3 provides significant cost-efficiency by decoupling storage from compute. This ensures the project only incurs costs for the storage volume consumed and avoids the expense of maintaining idle database servers during periods of low inactivity.

### <img width="55" height="28" alt="image" src="https://github.com/user-attachments/assets/6038ef18-3598-4f49-8304-b973d53346d2" /> AWS Glue & Athena

AWS Glue is a fully managed, serverless environment which serves as the central metadata repository and schema management layer in this architecture. While Amazon S3 stores the raw data, it lacks the structural definitions required for SQL querying. AWS Glue bridges this gap by using a Crawler to automatically discover the schema of the JSON data in S3 and populate the AWS Glue Data Catalog. This functionality eliminates the need to manually define or update table definitions as the IoT data structure evolves. By maintaining an up-to-date Data Catalog, Glue effectively turns the S3 Data Lake into a structured database which can be immediately queried by Amazon Athena without the additional overhead of managing a traditional relational database such as Amazon RDS.
On the other hand, Amazon Athena was selected as the serverless query engine to analyse the data stored in S3. Its serverless nature minimises the operational cost as it requires no infrastructure provisioning or cluster management, unlike Amazon Redshift. Athena uses a pay-per-query pricing which is highly cost-efficient for this workload since costs are incurred only when analysis is performed. Additionally, Athena supports the seamless integration with Amazon QuickSight for visualising the digital twin system. 

## Data Ingestion Pipeline

**Figure 2**

_Data Ingestion Pipeline Diagram_

<img width="419" height="350" alt="image" src="https://github.com/user-attachments/assets/efd522ef-b8cf-4fb7-8103-b3a6099cbf23" />


To ensure the Digital Twin relies on high-quality, continuous data, the service implements a robustness strategy targeting both data integrity and system resilience (availability of service).
	
Firstly, instead of ingesting raw API directly into storage, AWS Data Firehose triggers an AWS Lambda Transformation function (refer to Section 3.3). This function validates every record to contain essential fields such as ‘timestamp’. To prevent data loss while maintaining dataset purity, the system flags the record as ‘ProcessingFailed’, instead of discarding it. Firehose automatically routes these failed records to a dedicated “Error Bucket” in S3. This ensures that the primary storage remains “clean” for analytics, whilst preserving corrupt data in quarantine for debugging and manual recovery. Additionally, the Lambda function also enforces data types and explicitly appends a ‘\n’ delimiter to every JSON object. This transformation ensures data stored in S3 is strictly compatible with Amazon Athena, preventing errors during SQL querying.

On the other hand, this service is designed to recover automatically from the transient failures. The Producer on EC2 wraps all network operations in robust exception handling blocks (i.e., try-except). In the event of API outage or network partition (Connection Timeout), the service logs the error to CloudWatch (see Figure 12) and pauses execution (i.e., 60 seconds) before attempting to reconnect, ensuring the system remains robust. 

Moreover, Data Firehose acts as a temporal buffer between the Producer and S3. If S3 experiences a momentary throughput limit or latency spike, Firehose holds the data in its internal buffer for up to 24 hours and retries the delivery until successful. This prevents data loss even in the event of a rare S3 downtime.

## Implementation

### Connecting to the Greenhouse IoT API Stream

**Figure 3**

_Connecting to the Greenhouse IoT API Stream & Ingesting Data_

<img width="468" height="400" alt="image" src="https://github.com/user-attachments/assets/41526a12-6a25-4e95-bbf5-cbde74f54c27" />
 
**Figure 3** illustrates a Python function which establishes a connection to the Greenhouse IoT data stream and awaits incoming data before ingesting it into Amazon Data Firehose. Furthermore, it effectively manages and logs potential errors, including network-related issues, API connection retries, and unexpected errors.

### Amazon Data Firehose
**Figure 4**

_Firehose Stream Details in AWS_

<img width="442" height="153" alt="image" src="https://github.com/user-attachments/assets/3a9f181c-7bff-4e3c-9c04-8436466292d2" />

# Amazon S3
**Figure 5**

_Processed JSON Files Stored in S3_

<img width="474" height="412" alt="image" src="https://github.com/user-attachments/assets/389dbf5a-3e1b-419e-9993-180800271dbb" />

### Amazon Glue & Athena
**Figure 6**

_Querying Data in the AWS Glue Data Catalog Database_

<img width="409" height="307" alt="image" src="https://github.com/user-attachments/assets/a04d1698-d794-49e0-a444-906f2a04e130" />

### Amazon CloudWatch
**Figure 7**

_CloudWatch Log Events_

<img width="468" height="252" alt="image" src="https://github.com/user-attachments/assets/69dfd2b4-215f-4403-b523-7b4d5214ee74" />

 









