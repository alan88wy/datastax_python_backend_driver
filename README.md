# Flask Development with DataStax Astra & Cassandra Driver
### Packages Required

* SQLAlchemy
* Flask
* Flask-SQLAlchemy
* Flask-marshmallow
* marshmallow-sqlalchemy
* flask-login or flask-user or flask-JWT - we use JWT here
* pip install flask-jwt-extended
* flask-mail
* Mailtrap
* cassandra-driver
  
### SET the environment variables:
  
**In Powershell, to set environment variable, type $env:MAIL_USERNAME = 'abc'**
  
* MAIL_USERNAME  - in Powershell $env:MAIL_USERNAME = 'xxx'
* MAIL_PASSWORD 
* ASTRA_DB_ID
* ASTRA_DB_REGION
* ASTRA_DB_KEYSPACE
* ASTRA_DB_APPLICATION_TOKEN
* ASTRA_CLUSTER_ID
* CLIENT_ID
* CLIENT_SECRET
* JWT_SECRET

### ASTRA Database definition

```
CREATE KEYSPACE awcrm WITH replication = {'class': 'NetworkTopologyStrategy', 'ap-southeast-1': '3'}  AND durable_writes = true;

CREATE TABLE awcrm.planet (
    planet_id uuid PRIMARY KEY,
    distance float,
    home_star text,
    mass float,
    planet_name text,
    planet_type text,
    radius float
) WITH additional_write_policy = '99PERCENTILE'
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.UnifiedCompactionStrategy', 'log_all': 'true', 'num_shards': '128'}
    AND compression = {'chunk_length_in_kb': '64', 'class': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND crc_check_chance = 1.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair = 'BLOCKING'
    AND speculative_retry = '99PERCENTILE';
CREATE CUSTOM INDEX planet_idx1 ON awcrm.planet (planet_name) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex';

CREATE TABLE awcrm.users (
    id uuid PRIMARY KEY,
    email text,
    first_name text,
    last_name text,
    password text
) WITH additional_write_policy = '99PERCENTILE'
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.UnifiedCompactionStrategy', 'log_all': 'true', 'num_shards': '128'}
    AND compression = {'chunk_length_in_kb': '64', 'class': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND crc_check_chance = 1.0
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair = 'BLOCKING'
    AND speculative_retry = '99PERCENTILE';
CREATE CUSTOM INDEX users_idx1 ON awcrm.users (email) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex';
```

#### Created CLI command to create, seed and destroy database (if using SQLite)

##### Note: You need to change your app name to app.py in order to run the CLI.

We are using SQLite Database with SQLAlchemy/flask-sqlalchemy to access the database.

To run the CLI,

```
flask db_create // This will create the database
flask db_seed // This will seed the database
flask db_drop // This will destroy the database
```
