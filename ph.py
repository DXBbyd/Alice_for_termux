from pg import get_plugin_registry, get_disabled_plugins

def call_plugin(user_input: str) -> str | None:
    """调用已启用的插件"""
    plugin_registry = get_plugin_registry()
    disabled = get_disabled_plugins()
    for cmd_prefix, (_, _, execute_func) in plugin_registry.items():
        if cmd_prefix in disabled:
            continue
        if user_input.startswith(cmd_prefix):
            params = user_input[len(cmd_prefix):].strip()
            return execute_func(params)
    return None
