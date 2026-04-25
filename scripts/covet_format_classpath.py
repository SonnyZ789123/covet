def covet_format_classpath(compiled_root, runtime_deps_cp, has_runtime_deps):
    entries = [compiled_root]

    if has_runtime_deps and runtime_deps_cp:
        entries.extend(runtime_deps_cp.split(":"))

    return "\\\n    " + ";\\\n    ".join(entries)
