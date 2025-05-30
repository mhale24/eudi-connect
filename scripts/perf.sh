#!/bin/bash

# Function to display help message
show_help() {
    echo "EUDI-Connect Performance Testing Script"
    echo
    echo "Usage: ./perf.sh [command] [options]"
    echo
    echo "Commands:"
    echo "  benchmark     Run micro-benchmarks"
    echo "  advanced     Run advanced benchmarks with detailed metrics"
    echo "  load         Run basic load tests"
    echo "  load-adv     Run advanced load tests with detailed metrics"
    echo "  all          Run all performance tests"
    echo "  report       Generate performance report"
    echo "  dashboard    Launch real-time metrics dashboard"
    echo "  alerts       Launch alert management dashboard"
    echo "  help         Show this help message"
    echo
    echo "Options:"
    echo "  --users N    Number of concurrent users for load tests (default: 50)"
    echo "  --time N     Duration in minutes for load tests (default: 5)"
    echo "  --rate N     User spawn rate per second (default: 10)"
}

# Default values
USERS=50
TIME=5
RATE=10

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --users)
            USERS="$2"
            shift 2
            ;;
        --time)
            TIME="$2"
            shift 2
            ;;
        --rate)
            RATE="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

# Function to run basic micro-benchmarks
run_benchmarks() {
    echo "Running micro-benchmarks..."
    docker-compose exec api poetry run pytest tests/performance/test_benchmarks.py -v \
        --benchmark-only \
        --benchmark-autosave \
        --benchmark-compare
}

# Function to run advanced benchmarks
run_advanced_benchmarks() {
    echo "Running advanced benchmarks with detailed metrics..."
    docker-compose exec api poetry run pytest tests/performance/test_advanced_benchmarks.py -v \
        --benchmark-only \
        --benchmark-autosave \
        --benchmark-compare \
        --benchmark-histogram
}

# Function to run basic load tests
run_load_tests() {
    echo "Running load tests with $USERS users for ${TIME}m..."
    docker-compose exec api poetry run locust \
        -f tests/performance/locustfile.py \
        --headless \
        --users $USERS \
        --spawn-rate $RATE \
        --run-time ${TIME}m \
        --host http://localhost:8000 \
        --html reports/load_test_report.html
}

# Function to run advanced load tests
run_advanced_load_tests() {
    echo "Running advanced load tests with detailed metrics..."
    docker-compose exec api poetry run locust \
        -f tests/performance/advanced_locustfile.py \
        --headless \
        --users $USERS \
        --spawn-rate $RATE \
        --run-time ${TIME}m \
        --host http://localhost:8000 \
        --html reports/advanced_load_test_report.html
}

# Function to generate performance report
generate_report() {
    echo "Generating comprehensive performance report..."
    
    # Create reports directory if it doesn't exist
    mkdir -p reports
    
    # Combine all benchmark results
    echo "=== Benchmark Results ===" > reports/performance_report.txt
    cat .benchmarks/*/*.json >> reports/performance_report.txt
    
    # Add load test results
    echo "\n=== Load Test Results ===" >> reports/performance_report.txt
    cat reports/load_test_report.html >> reports/performance_report.txt
    
    # Add advanced metrics
    echo "\n=== Advanced Metrics ===" >> reports/performance_report.txt
    cat reports/advanced_load_test_report.html >> reports/performance_report.txt
    
    echo "Report generated at reports/performance_report.txt"
}

# Check if command is provided
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# Process commands
# Function to launch metrics dashboard
launch_dashboard() {
    echo "Launching performance metrics dashboard..."
    # Create reports directory if it doesn't exist
    mkdir -p reports

    # Launch dashboard in docker container
    docker-compose exec api poetry run streamlit run \
        tests/performance/dashboard.py \
        --server.port 8501 \
        --server.address 0.0.0.0 \
        --browser.serverAddress localhost \
        --theme.primaryColor "#FF4B4B" \
        --theme.backgroundColor "#FFFFFF" \
        --theme.secondaryBackgroundColor "#F0F2F6" \
        --theme.textColor "#262730"
}

# Function to launch alert dashboard
launch_alerts() {
    echo "Launching alert management dashboard..."
    # Create reports directory if it doesn't exist
    mkdir -p reports

    # Launch alert dashboard in docker container
    docker-compose exec api poetry run streamlit run \
        tests/performance/alert_dashboard.py \
        --server.port 8502 \
        --server.address 0.0.0.0 \
        --browser.serverAddress localhost \
        --theme.primaryColor "#dc3545" \
        --theme.backgroundColor "#FFFFFF" \
        --theme.secondaryBackgroundColor "#F0F2F6" \
        --theme.textColor "#262730"
}

case "$1" in
    benchmark)
        run_benchmarks
        ;;
    advanced)
        run_advanced_benchmarks
        ;;
    load)
        run_load_tests
        ;;
    load-adv)
        run_advanced_load_tests
        ;;
    all)
        run_benchmarks
        run_advanced_benchmarks
        run_load_tests
        run_advanced_load_tests
        generate_report
        launch_dashboard &
        launch_alerts &
        ;;
    report)
        generate_report
        ;;
    dashboard)
        launch_dashboard
        ;;
    alerts)
        launch_alerts
        ;;
    help)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
