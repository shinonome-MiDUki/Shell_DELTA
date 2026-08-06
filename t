SCRIPT_DIR=$(cd $(dirname $0) ; pwd)/
cd "${SCRIPT_DIR}"
./shelldelta_env/bin/python3 .src/shell_delta/main.py
