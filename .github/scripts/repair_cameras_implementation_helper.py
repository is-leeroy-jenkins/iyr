from pathlib import Path


path = Path( '.github/scripts/implement_cameras_and_module_renames.py' )
text = path.read_text( encoding='utf-8' )
text = text.replace( "provider = r'''", 'provider = r"""', 1 )
text = text.replace( "\n'''\nif 'class OverpassCameras:' in sources:",
    "\n\"\"\"\nif 'class OverpassCameras:' in sources:", 1 )
text = text.replace( "camera_function = r'''", 'camera_function = r"""', 1 )
text = text.replace( "\n'''\nworld = replace_once(\n    world,\n    \"\\tst.session_state[ 'live_world_infrastructure_result' ] = result",
    "\n\"\"\"\nworld = replace_once(\n    world,\n    \"\\tst.session_state[ 'live_world_infrastructure_result' ] = result", 1 )
path.write_text( text, encoding='utf-8' )
