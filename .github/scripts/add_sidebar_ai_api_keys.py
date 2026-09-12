from pathlib import Path


app_path = Path( 'app.py' )
app = app_path.read_text( encoding='utf-8' )
anchor = "\twith st.expander( label='API', expanded=False ):\n"
if anchor not in app:
    raise RuntimeError( 'Missing Credentials API expander anchor.' )
if "'OpenAI API Key'" in app or "'Grok / xAI API Key'" in app:
    raise RuntimeError( 'AI provider API key controls already exist.' )

controls = """\twith st.expander( label='API', expanded=False ):
\t\tinit_env_state( 'openai_api_key', 'OPENAI_API_KEY', 'OPENAI_API_KEY' )
\t\tinit_env_state( 'gemini_api_key', 'GEMINI_API_KEY', 'GEMINI_API_KEY' )
\t\tinit_env_state( 'xai_api_key', 'XAI_API_KEY', 'XAI_API_KEY' )
\t\tinit_env_state( 'claude_api_key', 'CLAUDE_API_KEY', 'CLAUDE_API_KEY' )
\t\tinit_env_state( 'mistral_api_key', 'MISTRAL_API_KEY', 'MISTRAL_API_KEY' )

\t\topenai_key = st.text_input( 'OpenAI API Key', type='password',
\t\t\tvalue=st.session_state.openai_api_key or '',
\t\t\thelp='Overrides OPENAI_API_KEY from config.py for this session only.' )
\t\tif openai_key:
\t\t\tst.session_state.openai_api_key = openai_key
\t\t\tos.environ[ 'OPENAI_API_KEY' ] = openai_key

\t\tgemini_key = st.text_input( 'Gemini API Key', type='password',
\t\t\tvalue=st.session_state.gemini_api_key or '',
\t\t\thelp='Overrides GEMINI_API_KEY from config.py for this session only.' )
\t\tif gemini_key:
\t\t\tst.session_state.gemini_api_key = gemini_key
\t\t\tos.environ[ 'GEMINI_API_KEY' ] = gemini_key

\t\txai_key = st.text_input( 'Grok / xAI API Key', type='password',
\t\t\tvalue=st.session_state.xai_api_key or '',
\t\t\thelp='Overrides XAI_API_KEY from config.py for this session only.' )
\t\tif xai_key:
\t\t\tst.session_state.xai_api_key = xai_key
\t\t\tos.environ[ 'XAI_API_KEY' ] = xai_key

\t\tclaude_key = st.text_input( 'Claude API Key', type='password',
\t\t\tvalue=st.session_state.claude_api_key or '',
\t\t\thelp='Overrides CLAUDE_API_KEY from config.py for this session only.' )
\t\tif claude_key:
\t\t\tst.session_state.claude_api_key = claude_key
\t\t\tos.environ[ 'CLAUDE_API_KEY' ] = claude_key

\t\tmistral_key = st.text_input( 'Mistral API Key', type='password',
\t\t\tvalue=st.session_state.mistral_api_key or '',
\t\t\thelp='Overrides MISTRAL_API_KEY from config.py for this session only.' )
\t\tif mistral_key:
\t\t\tst.session_state.mistral_api_key = mistral_key
\t\t\tos.environ[ 'MISTRAL_API_KEY' ] = mistral_key

"""

app = app.replace( anchor, controls, 1 )
app_path.write_text( app, encoding='utf-8' )
