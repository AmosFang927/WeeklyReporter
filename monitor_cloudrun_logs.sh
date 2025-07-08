#!/bin/bash

# Generic Google Cloud Run Service Log Monitor
# Author: AI Assistant
# Description: Monitor logs from any Google Cloud Run service with various options

set -e

# Color definitions for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_PROJECT_ID=""
DEFAULT_REGION="us-central1"
DEFAULT_LIMIT=20
DEFAULT_FRESHNESS="1h"

# Script usage
show_usage() {
    echo -e "${WHITE}🔍 Google Cloud Run Service Log Monitor${NC}"
    echo -e "${CYAN}=========================================${NC}"
    echo ""
    echo -e "${WHITE}Usage:${NC} $0 [OPTIONS] <service-name>"
    echo ""
    echo -e "${WHITE}Required:${NC}"
    echo -e "  ${GREEN}service-name${NC}        Name of the Cloud Run service"
    echo ""
    echo -e "${WHITE}Options:${NC}"
    echo -e "  ${GREEN}-p, --project${NC}       Google Cloud Project ID (default: current gcloud project)"
    echo -e "  ${GREEN}-r, --region${NC}        Google Cloud region (default: us-central1)"
    echo -e "  ${GREEN}-l, --limit${NC}         Number of log entries to show (default: 20)"
    echo -e "  ${GREEN}-f, --freshness${NC}     Time window for logs (default: 1h)"
    echo -e "  ${GREEN}-t, --tail${NC}          Follow logs in real-time (like tail -f)"
    echo -e "  ${GREEN}-w, --watch${NC}         Watch logs with periodic refresh"
    echo -e "  ${GREEN}-e, --errors${NC}        Show only error and warning logs"
    echo -e "  ${GREEN}-s, --severity${NC}      Filter by severity (INFO, WARNING, ERROR)"
    echo -e "  ${GREEN}-v, --verbose${NC}       Show verbose output with request details"
    echo -e "  ${GREEN}-h, --help${NC}          Show this help message"
    echo ""
    echo -e "${WHITE}Examples:${NC}"
    echo -e "  $0 my-service                           # View recent logs"
    echo -e "  $0 -p my-project -r us-east1 my-service # Specify project and region"
    echo -e "  $0 --tail my-service                    # Follow logs in real-time"
    echo -e "  $0 --watch --limit 50 my-service        # Watch with 50 entries"
    echo -e "  $0 --errors my-service                  # Show only errors"
    echo -e "  $0 --severity ERROR my-service          # Show only ERROR level logs"
    echo -e "  $0 --verbose --freshness 2h my-service # Verbose output for 2 hours"
    echo ""
    echo -e "${WHITE}Time formats:${NC}"
    echo -e "  ${YELLOW}m${NC} = minutes, ${YELLOW}h${NC} = hours, ${YELLOW}d${NC} = days"
    echo -e "  Examples: 30m, 2h, 1d"
    echo ""
}

# Parse command line arguments
parse_args() {
    local TEMP
    TEMP=$(getopt -o p:r:l:f:s:twevh --long project:,region:,limit:,freshness:,severity:,tail,watch,errors,verbose,help -n 'monitor_cloudrun_logs.sh' -- "$@")
    
    if [ $? != 0 ]; then
        echo "Error parsing arguments" >&2
        exit 1
    fi
    
    eval set -- "$TEMP"
    
    # Initialize variables
    PROJECT_ID=""
    REGION="$DEFAULT_REGION"
    LIMIT="$DEFAULT_LIMIT"
    FRESHNESS="$DEFAULT_FRESHNESS"
    TAIL_MODE=false
    WATCH_MODE=false
    ERRORS_ONLY=false
    SEVERITY=""
    VERBOSE=false
    SERVICE_NAME=""
    
    while true; do
        case "$1" in
            -p|--project)
                PROJECT_ID="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -l|--limit)
                LIMIT="$2"
                shift 2
                ;;
            -f|--freshness)
                FRESHNESS="$2"
                shift 2
                ;;
            -s|--severity)
                SEVERITY="$2"
                shift 2
                ;;
            -t|--tail)
                TAIL_MODE=true
                shift
                ;;
            -w|--watch)
                WATCH_MODE=true
                shift
                ;;
            -e|--errors)
                ERRORS_ONLY=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            --)
                shift
                break
                ;;
            *)
                echo "Internal error!" >&2
                exit 1
                ;;
        esac
    done
    
    # Get service name (remaining argument)
    if [ $# -eq 0 ]; then
        echo -e "${RED}❌ Error: Service name is required${NC}"
        echo ""
        show_usage
        exit 1
    fi
    
    SERVICE_NAME="$1"
    
    # Use current project if not specified
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [ -z "$PROJECT_ID" ]; then
            echo -e "${RED}❌ Error: No project specified and no default project configured${NC}"
            echo "Please specify a project with -p or set default with: gcloud config set project PROJECT_ID"
            exit 1
        fi
    fi
}

# Validate inputs
validate_inputs() {
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ Error: gcloud CLI is not installed${NC}"
        echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Validate project exists and is accessible
    if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
        echo -e "${RED}❌ Error: Project '$PROJECT_ID' not found or not accessible${NC}"
        exit 1
    fi
    
    # Validate service exists
    if ! gcloud run services describe "$SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
        echo -e "${RED}❌ Error: Service '$SERVICE_NAME' not found in region '$REGION'${NC}"
        echo "Available services in region $REGION:"
        gcloud run services list --region="$REGION" --project="$PROJECT_ID" --format="value(metadata.name)" 2>/dev/null || echo "No services found"
        exit 1
    fi
    
    # Validate severity if specified
    if [ -n "$SEVERITY" ]; then
        case "$SEVERITY" in
            INFO|WARNING|ERROR|DEBUG|CRITICAL)
                ;;
            *)
                echo -e "${RED}❌ Error: Invalid severity '$SEVERITY'${NC}"
                echo "Valid severities: INFO, WARNING, ERROR, DEBUG, CRITICAL"
                exit 1
                ;;
        esac
    fi
}

# Build log filter query
build_log_filter() {
    local filter='resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'"'
    
    if [ "$ERRORS_ONLY" = true ]; then
        filter="$filter AND (severity=\"ERROR\" OR severity=\"WARNING\")"
    elif [ -n "$SEVERITY" ]; then
        filter="$filter AND severity=\"$SEVERITY\""
    fi
    
    echo "$filter"
}

# Get log format based on verbosity
get_log_format() {
    if [ "$VERBOSE" = true ]; then
        echo "table(timestamp, severity, resource.labels.revision_name, httpRequest.requestMethod, httpRequest.status, textPayload)"
    else
        echo "table(timestamp, severity, textPayload)"
    fi
}

# Display configuration
show_config() {
    echo -e "${WHITE}🔧 Configuration${NC}"
    echo -e "${CYAN}===================${NC}"
    echo -e "${WHITE}Project:${NC} $PROJECT_ID"
    echo -e "${WHITE}Region:${NC} $REGION"
    echo -e "${WHITE}Service:${NC} $SERVICE_NAME"
    echo -e "${WHITE}Limit:${NC} $LIMIT"
    echo -e "${WHITE}Freshness:${NC} $FRESHNESS"
    [ "$ERRORS_ONLY" = true ] && echo -e "${WHITE}Filter:${NC} Errors and warnings only"
    [ -n "$SEVERITY" ] && echo -e "${WHITE}Severity:${NC} $SEVERITY"
    [ "$VERBOSE" = true ] && echo -e "${WHITE}Mode:${NC} Verbose"
    echo ""
}

# Get recent logs
get_recent_logs() {
    local filter=$(build_log_filter)
    local format=$(get_log_format)
    
    echo -e "${BLUE}📋 Fetching recent logs...${NC}"
    
    gcloud logging read "$filter" \
        --project="$PROJECT_ID" \
        --limit="$LIMIT" \
        --freshness="$FRESHNESS" \
        --format="$format" \
        --sort-by="~timestamp"
}

# Tail logs in real-time
tail_logs() {
    local filter=$(build_log_filter)
    local format="csv(timestamp, severity, textPayload)"
    
    echo -e "${BLUE}📋 Starting real-time log streaming...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo -e "${CYAN}==============================${NC}"
    
    local last_timestamp=""
    local first_run=true
    
    while true; do
        local logs=$(gcloud logging read "$filter" \
            --project="$PROJECT_ID" \
            --limit=10 \
            --freshness="2m" \
            --format="$format" \
            --sort-by="~timestamp" 2>/dev/null)
        
        if [ -n "$logs" ]; then
            # Skip CSV header
            logs=$(echo "$logs" | tail -n +2)
            
            if [ "$first_run" = true ]; then
                echo -e "${CYAN}=== Recent entries ===${NC}"
                echo "$logs" | head -3 | while IFS=',' read -r timestamp severity payload; do
                    format_log_entry "$timestamp" "$severity" "$payload"
                done
                echo -e "${CYAN}=== Live stream ===${NC}"
                first_run=false
                last_timestamp=$(echo "$logs" | head -1 | cut -d',' -f1 | tr -d '"')
            else
                # Show only new entries
                echo "$logs" | while IFS=',' read -r timestamp severity payload; do
                    timestamp=$(echo "$timestamp" | tr -d '"')
                    if [ "$timestamp" \> "$last_timestamp" ]; then
                        format_log_entry "$timestamp" "$severity" "$payload"
                        last_timestamp="$timestamp"
                    fi
                done
            fi
        fi
        
        sleep 2
    done
}

# Format log entry with colors
format_log_entry() {
    local timestamp="$1"
    local severity="$2"
    local payload="$3"
    
    # Clean up fields
    timestamp=$(echo "$timestamp" | tr -d '"')
    severity=$(echo "$severity" | tr -d '"')
    payload=$(echo "$payload" | tr -d '"')
    
    # Format timestamp
    local time_short=$(echo "$timestamp" | cut -d'T' -f2 | cut -d'.' -f1)
    
    # Color based on severity
    case "$severity" in
        "ERROR")
            echo -e "${RED}❌ [$time_short] $payload${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  [$time_short] $payload${NC}"
            ;;
        "INFO")
            echo -e "${GREEN}ℹ️  [$time_short] $payload${NC}"
            ;;
        "DEBUG")
            echo -e "${BLUE}🔧 [$time_short] $payload${NC}"
            ;;
        *)
            echo -e "${WHITE}📝 [$time_short] $payload${NC}"
            ;;
    esac
}

# Watch logs with periodic refresh
watch_logs() {
    echo -e "${BLUE}👁️ Starting log monitoring with periodic refresh...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    
    while true; do
        clear
        echo -e "${WHITE}📊 Cloud Run Log Monitor - $(date)${NC}"
        echo -e "${CYAN}================================================${NC}"
        show_config
        get_recent_logs
        echo ""
        echo -e "${YELLOW}⏱️ Refreshing in 10 seconds...${NC}"
        sleep 10
    done
}

# Main function
main() {
    parse_args "$@"
    validate_inputs
    show_config
    
    if [ "$TAIL_MODE" = true ]; then
        tail_logs
    elif [ "$WATCH_MODE" = true ]; then
        watch_logs
    else
        get_recent_logs
    fi
}

# Run main function with all arguments
main "$@"