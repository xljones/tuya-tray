function show_help() 
{
    echo "Tuya Tray"
    echo "Xander Jones (xljones.com)"
    echo 
    echo "Syntax: ./tuya.sh [--help/-h|--config/-c]"
    echo "options:"
    echo "--help|-h                    Print this Help."
    echo "--config|-c EMAIL PASSWORD   Configure config.json"
    echo
}

function setup_config() 
{
    echo "configuring './config.json' with email=$1 password=$2"
    echo "{\"username\": \"$1\", \"password\": \"$2\", \"country_code\": \"44\", \"application\": \"tuya\"}" > config.json
}

function venv_activate() 
{
    if [ ! -d "venv" ]; then
        python -m venv venv
    fi
    source venv/bin/activate
    python -m pip install -r requirements.txt --quiet
}

if [ "$1" = "--help" -o "$1" = "-h" ]; then
    show_help
elif [ "$1" = "--config" -o "$1" = "-c" ]; then
    setup_config $2 $3
elif [ "$1" = "" ]; then
    "starting tuya-tray.."
    venv_activate
    python -m tuya
else
    echo "Invalid option"
fi
