#!/bin/bash
# Research Agent Scheduler
# Manages launchd job for daily digest generation

set -e

PLIST_FILE="com.leegonzales.research-agent.plist"
PLIST_SRC="$(cd "$(dirname "$0")" && pwd)/$PLIST_FILE"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_FILE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 {install|uninstall|status|test}"
    echo ""
    echo "Commands:"
    echo "  install    - Install and start the daily schedule (6 AM)"
    echo "  uninstall  - Stop and remove the schedule"
    echo "  status     - Check if the schedule is running"
    echo "  test       - Run the research agent once now"
    exit 1
}

generate_plist_from_template() {
    echo -e "${YELLOW}Generating plist from template...${NC}"

    # Get current user
    local USERNAME=$(whoami)

    # Find python3 path
    local PYTHON_PATH=$(which python3)
    if [ -z "$PYTHON_PATH" ]; then
        echo -e "${RED}✗${NC} Could not find python3 in PATH"
        exit 1
    fi

    # Get python bin directory
    local PYTHON_BIN_DIR=$(dirname "$PYTHON_PATH")

    # Get project path (current directory)
    local PROJECT_PATH=$(cd "$(dirname "$0")" && pwd)

    # Get home directory
    local HOME_DIR="$HOME"

    # Check if template exists
    if [ ! -f "${PROJECT_PATH}/com.leegonzales.research-agent.plist.example" ]; then
        echo -e "${RED}✗${NC} Template file not found: com.leegonzales.research-agent.plist.example"
        exit 1
    fi

    # Generate plist from template
    sed -e "s|{{USERNAME}}|${USERNAME}|g" \
        -e "s|{{PYTHON_PATH}}|${PYTHON_PATH}|g" \
        -e "s|{{PYTHON_BIN_DIR}}|${PYTHON_BIN_DIR}|g" \
        -e "s|{{PROJECT_PATH}}|${PROJECT_PATH}|g" \
        -e "s|{{HOME}}|${HOME_DIR}|g" \
        "${PROJECT_PATH}/com.leegonzales.research-agent.plist.example" > \
        "${PROJECT_PATH}/com.leegonzales.research-agent.plist"

    echo -e "${GREEN}✓${NC} Generated plist with your system paths"
}

install_schedule() {
    echo -e "${YELLOW}Installing research agent schedule...${NC}"

    # Generate plist from template
    generate_plist_from_template

    # Create LaunchAgents directory if it doesn't exist
    mkdir -p "$HOME/Library/LaunchAgents"

    # Copy plist file
    cp "$PLIST_SRC" "$PLIST_DEST"
    echo -e "${GREEN}✓${NC} Copied plist to ~/Library/LaunchAgents/"

    # Load the job
    launchctl load "$PLIST_DEST"
    echo -e "${GREEN}✓${NC} Loaded launchd job"

    # Verify it's running
    if launchctl list | grep -q "com.leegonzales.research-agent"; then
        echo -e "${GREEN}✓${NC} Schedule is active!"
        echo ""
        echo "Research agent will run daily at 6:00 AM"
        echo ""
        echo "To check status:  ./schedule.sh status"
        echo "To test now:      ./schedule.sh test"
        echo "To uninstall:     ./schedule.sh uninstall"
    else
        echo -e "${RED}✗${NC} Failed to load schedule"
        exit 1
    fi
}

uninstall_schedule() {
    echo -e "${YELLOW}Uninstalling research agent schedule...${NC}"

    # Unload the job if it's running
    if launchctl list | grep -q "com.leegonzales.research-agent"; then
        launchctl unload "$PLIST_DEST" 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Unloaded launchd job"
    fi

    # Remove plist file
    if [ -f "$PLIST_DEST" ]; then
        rm "$PLIST_DEST"
        echo -e "${GREEN}✓${NC} Removed plist file"
    fi

    echo -e "${GREEN}✓${NC} Schedule removed"
}

check_status() {
    echo "Research Agent Schedule Status:"
    echo "================================"

    if [ -f "$PLIST_DEST" ]; then
        echo -e "Plist file:       ${GREEN}✓ Installed${NC}"
    else
        echo -e "Plist file:       ${RED}✗ Not found${NC}"
    fi

    if launchctl list | grep -q "com.leegonzales.research-agent"; then
        echo -e "Launchd job:      ${GREEN}✓ Running${NC}"
        echo ""
        echo "Schedule: Daily at 6:00 AM"
        echo ""

        # Show recent logs
        if [ -f "$HOME/.research-agent/logs/launchd-stdout.log" ]; then
            echo "Last run output (last 10 lines):"
            tail -10 "$HOME/.research-agent/logs/launchd-stdout.log"
        fi
    else
        echo -e "Launchd job:      ${RED}✗ Not running${NC}"
        echo ""
        echo "Run './schedule.sh install' to set up the schedule"
    fi
}

test_run() {
    echo -e "${YELLOW}Running research agent now...${NC}"
    echo ""

    cd "$(dirname "$0")"
    python3 -m research_agent.cli.main run

    echo ""
    echo -e "${GREEN}✓${NC} Test run complete"
}

# Main script
case "${1:-}" in
    install)
        install_schedule
        ;;
    uninstall)
        uninstall_schedule
        ;;
    status)
        check_status
        ;;
    test)
        test_run
        ;;
    *)
        print_usage
        ;;
esac
