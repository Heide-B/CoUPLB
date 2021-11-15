mkdir -p ~/.streamlit/

echo "\
[general]\n\
email = \"heidemlbalcera@gmail.com\"\n\
" > ~/.streamlit/credentials.toml

echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
[theme]\n\
font=\"sans serif\"\n
