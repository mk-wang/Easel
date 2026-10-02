"""Check Easel's native runtime configuration without contacting a paid provider."""
GREEN="\033[0;32m"; RED="\033[0;31m"; NC="\033[0m"
def cmd_ping(_args):
    print("[easel] Easel runtime check\n")
    try:
        from easel.runtime import provider_config, RuntimeErrorBase
        base,_key,model,protocol=provider_config()
    except RuntimeErrorBase as exc:
        print(f"  {RED}FAIL{NC} model provider config\n    {exc}")
        return 1
    print(f"  {GREEN}OK{NC} native Easel runtime")
    print(f"  {GREEN}OK{NC} provider configured ({protocol}, {model or 'default model'})")
    print(f"  endpoint: {base}")
    print("\nProvider credentials are configured. No external request was made.")
    return 0
