# Oracle OCI to CloudZero Cost Sync

Fetches OCI usage data and uploads it to CloudZero AnyCost Stream.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

1. **Edit `env/.env`** with your OCI and CloudZero credentials:
```bash
# OCI Configuration
OCI_USER_OCID=ocid1.user.oc1..aaaaaaaa...
OCI_TENANCY_OCID=ocid1.tenancy.oc1..aaaaaaaa...
OCI_FINGERPRINT=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
OCI_PRIVATE_KEY_PATH=./env/your-key-file.pem
OCI_REGION=us-ashburn-1

# CloudZero Configuration  
CLOUDZERO_API_KEY=your-api-key
CLOUDZERO_CONNECTION_ID=your-connection-id
CLOUDZERO_API_URL=https://api.cloudzero.com
```

2. **Test connection**:
```bash
python run_oci_adaptor.py --test-connection
```

## Usage

### Daily Sync (Recommended)
```bash
# Run daily sync
./daily_sync.py

# Test before running (dry run)
./daily_sync.py --test

# Set up daily cron job
0 8 * * * cd /path/to/oracle-oci-anycost-adaptor && ./daily_sync.py
```

### Manual Runs
```bash
# Process specific month
python run_oci_adaptor.py --month 2025-09

# Process multiple months
python run_oci_adaptor.py --months 2025-08,2025-09

# Dry run (don't upload)
python run_oci_adaptor.py --month 2025-09 --dry-run
```

### Process CSV Files
```bash
# Convert OCI CSV to CloudZero format
python src/csv_to_cbf.py --input input/oci_data.csv
```

## What It Does

1. Fetches OCI usage data via API
2. Transforms to CloudZero CBF format
3. Uploads to CloudZero AnyCost Stream
4. Handles 5MB API limits with automatic batching
5. Saves data to `output/` for validation

## Documentation

- [CloudZero AnyCost Stream](https://docs.cloudzero.com/docs/anycost-stream-getting-started)
- [OCI Usage API](https://docs.oracle.com/en-us/iaas/api/#/en/usage/20200107/)

## Support

Questions: support@cloudzero.com  
Issues: [GitHub Issues](https://github.com/jakesciotto/oracle-oci-anycost-adaptor/issues)