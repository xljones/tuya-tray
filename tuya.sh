show_help() 
{
    echo "_______________ ________.___.  _____          _____________________    _____ _____.___."
    echo "\__    ___/    |   \__  |   | /  _  \         \__    ___/\______   \  /  _  \\__  |   |"
    echo "  |    |  |    |   //   |   |/  /_\  \   ______ |    |    |       _/ /  /_\  \/   |   |"
    echo "  |    |  |    |  / \____   /    |    \ /_____/ |    |    |    |   \/    |    \____   |"
    echo "  |____|  |______/  / ______\____|__  /         |____|    |____|_  /\____|__  / ______|"
    echo "                    \/              \/   X Jones (xljones.com)   \/         \/\/       "
    echo 
    echo "Syntax: ./tuya.sh [--help/-h|--config/-c]"
    echo "options:"
    echo "    --help|-h     Print this Help."
    echo "    --config|-c EMAIL PASSWORD COUNTRY_CODE APPLICATION   
                    Configure config.json with your details
                    APPLICATION will be one of smart_life|tuya"
    echo "    --active|-a   Run Tuya Tray and keep connected in the shell"
    echo
    echo "Use no option to run Tuya Tray in the background"
    echo
}

setup_config() 
{
    if [ "$4" != "tuya" -o "$4" != "smart_life" ]; then
        echo "application needs to be one of [tuya|smart_life]"
    else
        echo "configuring './config.json' with email=$1 password=$2 country_code=$3 application=$4"
        echo "{\"username\": \""$1"\", \"password\": \""$2"\", \"country_code\": \"$3\", \"application\": \"$4\"}" > config.json
    fi
}

venv_activate()
{
    if [ ! -d "venv" ]; then
        python -m venv venv
    fi
    source venv/bin/activate
    python -m pip install --upgrade pip $1
    python -m pip install -r requirements.txt $1
}

if [ "$1" = "--help" -o "$1" = "-h" ]; then
    show_help
elif [ "$1" = "--config" -o "$1" = "-c" ]; then
    setup_config $2 $3
elif [ "$1" = "--active" -o "$1" = "-a" ]; then
    echo "starting tuya-tray without disconnecting from process.."
    venv_activate
    python -m app
elif [ "$1" = "--install" -o "$1" = "-i" ]; then
    venv_activate
elif [ "$1" = "--test" -o "$1" = "-t" ]; then
    echo "running application tests"
    venv_activate "--quiet"
    echo "=== FLAKE8 ==="
    python -m flake8 .
    echo "=== MYPY ==="
    python -m mypy .
    echo "=== BLACK ==="
    python -m black --check .
    echo "=== ISORT ==="
    python -m isort --check .
    echo "=== PYTEST ==="
    python -m pytest .
elif [ "$1" = "" ]; then
    echo "starting tuya-tray with no hangup (nohup)..."
    venv_activate
    nohup python -m app > .tuya.log &
else
    echo "Invalid option"
fi
