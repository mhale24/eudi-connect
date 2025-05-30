#!/bin/bash

# Function to display help message
show_help() {
    echo "EUDI-Connect Development Script"
    echo
    echo "Usage: ./dev.sh [command]"
    echo
    echo "Commands:"
    echo "  up              Start the development environment"
    echo "  down            Stop the development environment"
    echo "  build           Rebuild containers"
    echo "  logs [service]  View logs (optionally for a specific service)"
    echo "  shell          Open a shell in the API container"
    echo "  db             Open a psql shell in the database container"
    echo "  test           Run tests"
    echo "  lint           Run linting checks"
    echo "  format         Format code"
    echo "  help           Show this help message"
}

# Check if command is provided
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# Process commands
case "$1" in
    up)
        docker-compose up -d
        echo "Development environment is up!"
        echo "API: http://localhost:8000"
        echo "API Docs: http://localhost:8000/docs"
        echo "Jaeger UI: http://localhost:16686"
        echo "MailHog UI: http://localhost:8025"
        ;;
    down)
        docker-compose down
        ;;
    build)
        docker-compose build
        ;;
    logs)
        if [ -z "$2" ]; then
            docker-compose logs -f
        else
            docker-compose logs -f "$2"
        fi
        ;;
    shell)
        docker-compose exec api /bin/bash
        ;;
    db)
        docker-compose exec db psql -U postgres -d eudi_connect
        ;;
    test)
        docker-compose exec api poetry run pytest
        ;;
    lint)
        docker-compose exec api poetry run mypy eudi_connect
        docker-compose exec api poetry run flake8 eudi_connect
        ;;
    format)
        docker-compose exec api poetry run black eudi_connect
        docker-compose exec api poetry run isort eudi_connect
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
