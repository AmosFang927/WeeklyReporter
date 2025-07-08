# Google Cloud Run Log Monitor

A comprehensive shell script for monitoring logs from any Google Cloud Run service with various filtering and display options.

## Features

- 🔍 **View recent logs** with customizable time windows
- 📡 **Real-time log streaming** (tail -f like behavior)
- 👁️ **Periodic refresh monitoring** with automatic updates
- 🚨 **Error filtering** to show only warnings and errors
- 📊 **Severity filtering** for specific log levels
- 🎨 **Colored output** with emojis for better readability
- 🔧 **Verbose mode** with HTTP request details
- ⚙️ **Flexible configuration** for different projects and regions

## Prerequisites

- Google Cloud SDK (`gcloud`) installed and configured
- Authenticated with Google Cloud (`gcloud auth login`)
- Access to Cloud Run services in the target project

## Installation

1. Make the script executable:
   ```bash
   chmod +x monitor_cloudrun_logs.sh
   ```

2. Optionally, move it to your PATH:
   ```bash
   sudo mv monitor_cloudrun_logs.sh /usr/local/bin/monitor-cloudrun-logs
   ```

## Usage

### Basic Usage

```bash
./monitor_cloudrun_logs.sh [OPTIONS] <service-name>
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-p, --project` | Google Cloud Project ID | Current gcloud project |
| `-r, --region` | Google Cloud region | us-central1 |
| `-l, --limit` | Number of log entries to show | 20 |
| `-f, --freshness` | Time window for logs | 1h |
| `-t, --tail` | Follow logs in real-time | false |
| `-w, --watch` | Watch logs with periodic refresh | false |
| `-e, --errors` | Show only error and warning logs | false |
| `-s, --severity` | Filter by severity (INFO, WARNING, ERROR, DEBUG, CRITICAL) | all |
| `-v, --verbose` | Show verbose output with request details | false |
| `-h, --help` | Show help message | - |

### Examples

#### Basic log viewing
```bash
# View recent logs for a service
./monitor_cloudrun_logs.sh my-service

# Specify project and region
./monitor_cloudrun_logs.sh -p my-project -r us-east1 my-service
```

#### Real-time monitoring
```bash
# Follow logs in real-time (like tail -f)
./monitor_cloudrun_logs.sh --tail my-service

# Watch with periodic refresh
./monitor_cloudrun_logs.sh --watch my-service
```

#### Error monitoring
```bash
# Show only errors and warnings
./monitor_cloudrun_logs.sh --errors my-service

# Show only ERROR level logs
./monitor_cloudrun_logs.sh --severity ERROR my-service
```

#### Advanced usage
```bash
# Verbose output with HTTP details, 50 entries, 2 hours
./monitor_cloudrun_logs.sh --verbose --limit 50 --freshness 2h my-service

# Real-time error monitoring
./monitor_cloudrun_logs.sh --tail --errors my-service
```

### Time Format

Time windows can be specified using:
- `m` = minutes (e.g., `30m`)
- `h` = hours (e.g., `2h`)
- `d` = days (e.g., `1d`)

### Log Severity Levels

- `INFO` - General information
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `DEBUG` - Debug information
- `CRITICAL` - Critical errors

## Output Format

The script provides color-coded output:
- ❌ **Red** - Errors
- ⚠️ **Yellow** - Warnings
- ℹ️ **Green** - Info messages
- 🔧 **Blue** - Debug messages
- 📝 **White** - Other messages

## Configuration

The script automatically detects:
- Current Google Cloud project (if not specified)
- Available Cloud Run services in the region
- Service existence and accessibility

## Comparison with Existing Scripts

This script complements your existing monitoring tools:

### vs. `view_logs.sh`
- **Generic**: Works with any service (not just reporter-agent)
- **More options**: Additional filtering and display modes
- **Better UX**: Colored output and emojis
- **Validation**: Checks service existence and accessibility

### vs. `monitor_reporter_agent.sh`
- **Focused**: Specifically for log monitoring (not full service monitoring)
- **Reusable**: Can be used with any Cloud Run service
- **Simpler**: Focused on logs rather than comprehensive monitoring

## Error Handling

The script includes comprehensive error handling:
- Validates Google Cloud SDK installation
- Checks project and service existence
- Provides helpful error messages
- Suggests fixes for common issues

## Performance

- Uses efficient `gcloud logging read` commands
- Minimizes API calls with appropriate time windows
- Implements smart refresh intervals for real-time monitoring

## Examples with Your Services

Based on your existing setup:

```bash
# Monitor reporter-agent logs
./monitor_cloudrun_logs.sh -p solar-idea-463423-h8 -r asia-southeast1 reporter-agent

# Real-time monitoring with errors only
./monitor_cloudrun_logs.sh --tail --errors -p solar-idea-463423-h8 -r asia-southeast1 reporter-agent

# Verbose monitoring with HTTP details
./monitor_cloudrun_logs.sh --verbose --watch -p solar-idea-463423-h8 -r asia-southeast1 reporter-agent
```

## Troubleshooting

### Common Issues

1. **"gcloud not found"**
   - Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install

2. **"Project not found"**
   - Check project ID: `gcloud projects list`
   - Set default project: `gcloud config set project PROJECT_ID`

3. **"Service not found"**
   - List available services: `gcloud run services list --region=REGION`
   - Check region setting

4. **"Permission denied"**
   - Ensure you have Cloud Run and Cloud Logging permissions
   - Check authentication: `gcloud auth list`

### Debug Mode

For debugging, you can run with verbose output:
```bash
./monitor_cloudrun_logs.sh --verbose --limit 5 my-service
```

## Contributing

Feel free to enhance this script with additional features:
- JSON output format
- Log export functionality
- Integration with other monitoring tools
- Custom filter expressions

## License

This script is provided as-is for monitoring Google Cloud Run services.