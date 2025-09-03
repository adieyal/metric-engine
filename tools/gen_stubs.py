from __future__ import annotations

import importlib
import inspect
import io
import keyword
import pkgutil
import sys
from pathlib import Path
from typing import Any, Callable, TypeVar, get_args, get_origin, get_type_hints

PKG_IMPORT = "metricengine"
CALC_PKG_IMPORT = f"{PKG_IMPORT}.calculations"


def _pkg_dir(modname: str) -> Path:
    mod = importlib.import_module(modname)
    return Path(mod.__file__).resolve().parent


SRC_DIR = Path("src").resolve()
PKG_DIR = _pkg_dir(PKG_IMPORT)
CALC_DIR = _pkg_dir(CALC_PKG_IMPORT)

OUT_TYPED = PKG_DIR / "typed_api.pyi"
OUT_FWD = PKG_DIR / "_typed_forwarders.py"

HEADER_CALCS = (
    "# Auto-generated — DO NOT EDIT.\n"
    "from typing import Any, Union, Optional, List, Dict, Tuple, Sequence, TypeVar\n"
    "from decimal import Decimal, ROUND_HALF_UP\n"
    "from typing import SupportsFloat\n"
    "from metricengine import FinancialValue as FV, Unit, Dimensionless, Ratio, Percent, Money\n\n"
    "U = TypeVar('U', bound=Unit)\n\n"
)

HEADER_TYPED = (
    "# Auto-generated — DO NOT EDIT.\n"
    "from typing import Any, Protocol, Literal, overload, Union, Optional, List, Dict, Tuple, TypeVar, Sequence, Mapping\n"
    "from decimal import Decimal, ROUND_HALF_UP\n"
    "from typing import SupportsFloat\n"
    "from types import NoneType\n"
    "from metricengine import FinancialValue as FV, Unit, Dimensionless, Ratio, Percent, Money, Policy\n"
    "from metricengine.utils import SupportsDecimal\n\n"
    "U = TypeVar('U', bound=Unit)\n\n"
)


def _write_engine_pyi(calc_names: list[str], reg_get) -> None:
    """
    Generate src/metricengine/engine.pyi with per-calculation overloads for Engine.calculate,
    each including the FULL docstring of the target calculation.
    """
    out_path = _pkg_dir(f"{PKG_IMPORT}") / "engine.pyi"

    buf = io.StringIO()
    buf.write(HEADER_TYPED)
    # buf.write("# Auto-generated — DO NOT EDIT.\n")
    # buf.write("from __future__ import annotations\n")
    # buf.write("from typing import Any, Mapping, Literal, overload\n")
    # buf.write(
    #     "from metricengine import FinancialValue as FV, Unit, Dimensionless, Ratio, Percent, Money, Policy\n"
    # )
    # buf.write("from metricengine.utils import SupportsDecimal\n\n")

    buf.write("class Engine:\n")
    buf.write("    def __init__(self, *args: Any, **kwargs: Any) -> None: ...\n\n")

    for full in calc_names:
        fn = reg_get(full)
        params, _, ret = _params_for_stub(fn)  # preserves generics like FV[Ratio]
        doc = _doc_lines(fn, limit=None)  # <-- FULL docstring

        # Build the parameter block for calculate(...)
        # Engine.calculate(self, name=Literal["..."], ctx=..., *, policy=..., allow_partial=..., <calc kwargs>...)
        buf.write("    @overload\n")
        buf.write("    def calculate(\n")
        buf.write("        self,\n")
        buf.write(f'        name: Literal["{full}"],\n')
        buf.write("        ctx: Mapping[str, SupportsDecimal] | None = ..., \n")
        buf.write("        *,\n")
        buf.write("        policy: Policy | None = ..., \n")
        buf.write("        allow_partial: bool = ..., \n")
        if params:
            buf.write(f"        {', '.join(params)}\n")
        buf.write(f"    ) -> {ret}:\n")
        if doc:
            buf.write('        """\\\n')
            for ln in doc:
                buf.write("        " + ln + "\n")
            buf.write('        """\n')
        buf.write("        ...\n\n")

    # Fallback (unknown/non-literal)
    buf.write("    def calculate(\n")
    buf.write("        self,\n")
    buf.write("        name: str,\n")
    buf.write("        ctx: Mapping[str, SupportsDecimal] | None = ..., \n")
    buf.write("        *,\n")
    buf.write("        policy: Policy | None = ..., \n")
    buf.write("        allow_partial: bool = ..., \n")
    buf.write("        **kwargs: SupportsDecimal,\n")
    buf.write("    ) -> FV: ...\n")

    out_path.write_text(buf.getvalue(), encoding="utf-8")


def _safe_get_type_hints(fn):
    """
    Evaluate type hints even with deferred (string) annotations.
    Injects metricengine symbols and ALL TypeVars defined in metricengine.value.
    Falls back to raw __annotations__ if evaluation fails.
    """
    try:
        mod_globals = sys.modules[fn.__module__].__dict__.copy()

        # Bring in FV and units under the names used in annotations
        from metricengine import Dimensionless, Money, Percent, Ratio, Unit
        from metricengine import FinancialValue as _FV

        mod_globals.setdefault("FinancialValue", _FV)  # allow 'FinancialValue[...]'
        mod_globals.setdefault("FV", _FV)  # allow 'FV[...]'
        mod_globals.update(
            {
                "Unit": Unit,
                "Dimensionless": Dimensionless,
                "Ratio": Ratio,
                "Percent": Percent,
                "Money": Money,
            }
        )

        # Critically: inject all TypeVars from metricengine.value (e.g. U)
        import metricengine.value as _vmod

        for k, v in _vmod.__dict__.items():
            if isinstance(v, TypeVar):
                mod_globals.setdefault(k, v)

        return get_type_hints(fn, globalns=mod_globals, include_extras=True)
    except Exception:
        return getattr(fn, "__annotations__", {}) or {}


def _import_all_calc_modules() -> None:
    for m in pkgutil.iter_modules([str(CALC_DIR)]):
        name = m.name
        if not name.startswith("_"):
            importlib.import_module(f"{CALC_PKG_IMPORT}.{name}")


def _load_plugins_if_any() -> None:
    try:
        ftk = importlib.import_module(PKG_IMPORT)
        if hasattr(ftk, "load_plugins"):
            ftk.load_plugins({})
    except Exception:
        pass  # keep generation resilient


def _is_ident(name: str) -> bool:
    return name.isidentifier() and not keyword.iskeyword(name)


def _fmt_ann(tp: Any) -> str:
    # If raw string (from __annotations__), just clean it up.
    if isinstance(tp, str):
        s = tp
        s = s.replace("typing.", "")
        s = s.replace("metricengine.value.FinancialValue", "FV")
        s = s.replace("FinancialValue", "FV")
        s = s.replace("metricengine.units.", "")
        return s

    if tp is inspect._empty:
        return "Any"

    # Keep TypeVars (e.g., 'U')
    if isinstance(tp, TypeVar):
        return tp.__name__

    try:
        # Handle 'FV[Ratio]' style for evaluated typing objects
        origin = get_origin(tp)
        args = get_args(tp)
        if origin is not None:
            name = getattr(origin, "__name__", str(origin))
            # Normalize to FV and strip module prefixes for units
            name = name.replace("FinancialValue", "FV").replace(
                "metricengine.value.FinancialValue", "FV"
            )
            rendered_args = ", ".join(_fmt_ann(a) for a in args) if args else ""
            return f"{name}[{rendered_args}]" if rendered_args else name

        # Bare classes (no generics)
        nm = getattr(tp, "__name__", None)
        if nm:
            if nm == "FinancialValue":
                return "FV"
            return nm

        # Fallback string form
        s = str(tp).replace("typing.", "")
        s = s.replace("metricengine.value.FinancialValue", "FV")
        s = s.replace("metricengine.units.", "")
        return s
    except Exception:
        return "Any"


def _doc_lines(fn: Callable[..., Any], limit: int = 80) -> list[str]:
    doc = inspect.getdoc(fn) or ""
    if not doc:
        return []
    lines = [ln.rstrip() for ln in doc.splitlines()]
    return lines[:limit]


def _params_for_stub(fn):
    fn_unwrapped = inspect.unwrap(fn)
    sig = inspect.signature(fn_unwrapped)
    hints = _safe_get_type_hints(
        fn_unwrapped
    )  # evaluated (may drop generics if U missing)
    raw = (
        getattr(fn_unwrapped, "__annotations__", {}) or {}
    )  # raw strings preserve 'FV[U]'

    param_decls, arg_types = [], []
    saw_kwonly = False
    has_varpos = any(
        p.kind is inspect.Parameter.VAR_POSITIONAL for p in sig.parameters.values()
    )

    for name, p in sig.parameters.items():
        evaluated = hints.get(name, p.annotation)
        raw_ann = raw.get(name, None)

        # Choose the richer representation
        ann_str_eval = _fmt_ann(evaluated)
        ann_str_raw = _fmt_ann(raw_ann) if raw_ann is not None else None

        # If evaluated collapsed to 'FV' but raw has 'FV[... ]', use raw.
        if (
            ann_str_raw
            and (ann_str_eval in ("FV", "FinancialValue", "Any"))
            and "[" in ann_str_raw
        ):
            ann_str = ann_str_raw
        else:
            ann_str = ann_str_eval

        default = " = ..." if p.default is not inspect._empty else ""
        if p.kind is inspect.Parameter.POSITIONAL_ONLY:
            param_decls.append(f"{name}: {ann_str}{default}")
            arg_types.append(ann_str)
        elif p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
            param_decls.append(f"{name}: {ann_str}{default}")
            arg_types.append(ann_str)
        elif p.kind is inspect.Parameter.VAR_POSITIONAL:
            param_decls.append(f"*{name}: {ann_str}")
        elif p.kind is inspect.Parameter.KEYWORD_ONLY:
            if not saw_kwonly and not has_varpos:
                param_decls.append("*")
            saw_kwonly = True
            param_decls.append(f"{name}: {ann_str}{default}")
            arg_types.append(ann_str)
        elif p.kind is inspect.Parameter.VAR_KEYWORD:
            param_decls.append("**" + name + ": Any")

    # Return annotation
    ret_eval = hints.get("return", sig.return_annotation)
    ret_raw = raw.get("return", None)
    ret_eval_s = _fmt_ann(ret_eval)
    ret_raw_s = _fmt_ann(ret_raw) if ret_raw is not None else None
    if (
        ret_raw_s
        and (ret_eval_s in ("FV", "FinancialValue", "Any"))
        and "[" in ret_raw_s
    ):
        ret_s = ret_raw_s
    else:
        ret_s = ret_eval_s or "FV"

    return param_decls, arg_types, (ret_s or "FV")


def _ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _proto_name(full: str) -> str:
    return "Calc_" + full.replace(".", "_")


def _symbol_name(full: str) -> str:
    # forwarder function symbol (module.name -> module_name)
    sym = full.replace(".", "_")
    return sym if _is_ident(sym) else f"calc_{abs(hash(full))}"


def main() -> int:
    _import_all_calc_modules()
    _load_plugins_if_any()

    reg = importlib.import_module(f"{PKG_IMPORT}.registry")
    list_calculations = reg.list_calculations
    reg_get = reg.get

    calc_names = sorted(list_calculations().keys())
    _write_engine_pyi(calc_names, reg_get)

    # group by first-level namespace (module under calculations/)
    by_module: dict[str, list[tuple[str, Callable[..., Any]]]] = {}
    for full in calc_names:
        parts = full.split(".")
        module = ".".join(parts[:-1]) if len(parts) >= 2 else ""
        func = parts[-1]
        try:
            fn = reg_get(full)
        except KeyError:
            continue
        by_module.setdefault(module, []).append((func, fn))

    # 1) Write per-module calculation stubs + __init__.pyi barrel
    for module, items in by_module.items():
        pyi_path = (
            (CALC_DIR / f"{module}.pyi") if module else (CALC_DIR / "__init__.pyi")
        )
        _ensure_dir(pyi_path)
        buf = io.StringIO()
        buf.write(HEADER_CALCS)

        for func, fn in sorted(items, key=lambda x: x[0]):
            params, _, ret = _params_for_stub(fn)
            doc = _doc_lines(fn)
            if doc:
                buf.write('"""\\\n')
                for ln in doc:
                    buf.write(ln + "\n")
                buf.write('"""\n')
            buf.write(f"def {func}({', '.join(params)}) -> {ret}: ...\n")

        pyi_path.write_text(buf.getvalue(), encoding="utf-8")

    # Re-export submodule symbols from calculations/__init__.pyi
    init_buf = io.StringIO()
    init_buf.write(HEADER_CALCS)
    for module, items in sorted(by_module.items()):
        if not module:
            continue
        names = ", ".join(name for name, _ in sorted(items))
        init_buf.write(f"from .{module} import {names}\n")
    (CALC_DIR / "__init__.pyi").write_text(init_buf.getvalue(), encoding="utf-8")

    # 2) Write typed_api.pyi with Protocols, overloads, and typed forwarder defs
    typed_buf = io.StringIO()
    typed_buf.write(HEADER_TYPED)

    if calc_names:
        lits = ", ".join(f'"{n}"' for n in calc_names)
        typed_buf.write(f"CalcName = Literal[{lits}]\n\n")
    else:
        typed_buf.write('CalcName = Literal["__none__"]\n\n')

    for full in calc_names:
        fn = reg_get(full)
        params, _, ret = _params_for_stub(fn)
        doc = _doc_lines(fn)
        proto = _proto_name(full)
        typed_buf.write(f"class {proto}(Protocol):\n")
        if doc:
            typed_buf.write('    """\\\n')
            for ln in doc:
                typed_buf.write("    " + ln + "\n")
            typed_buf.write('    """\n')
        typed_buf.write(
            f"    def __call__({', '.join(['self'] + params)}) -> {ret}: ...\n\n"
        )

    for full in calc_names:
        proto = _proto_name(full)
        typed_buf.write("@overload\n")
        typed_buf.write(f'def get_calc(name: Literal["{full}"]) -> {proto}: ...\n')

    typed_buf.write("def get_calc(name: str) -> Any: ...\n")
    typed_buf.write("def calc_names() -> list[CalcName]: ...\n\n")

    # Typed stubs for forwarder functions (so calls are fully typed)
    for full in calc_names:
        fn = reg_get(full)
        params, _, ret = _params_for_stub(fn)
        sym = _symbol_name(full)
        typed_buf.write(f"def {sym}({', '.join(params)}) -> {ret}: ...\n")

    OUT_TYPED.write_text(typed_buf.getvalue(), encoding="utf-8")

    # 3) Write runtime forwarders with real docstrings (great hover UX)
    fwd_buf = io.StringIO()
    fwd_buf.write("# Auto-generated — DO NOT EDIT.\n")
    fwd_buf.write("from __future__ import annotations\n")
    fwd_buf.write("from typing import Any\n")
    fwd_buf.write("from .registry import get as _get\n\n")

    for full in calc_names:
        fn = reg_get(full)
        sym = _symbol_name(full)
        doc = _doc_lines(fn, limit=200)
        fwd_buf.write(f"def {sym}(*args: Any, **kwargs: Any):\n")
        if doc:
            fwd_buf.write('    """\\n')
            for ln in doc:
                fwd_buf.write("    " + ln + "\n")
            fwd_buf.write('    """\n')
        fwd_buf.write(f'    return _get("{full}")(*args, **kwargs)\n\n')

    OUT_FWD.write_text(fwd_buf.getvalue(), encoding="utf-8")

    print(f"Generated stubs for {len(calc_names)} calculations.")
    print(f" - {OUT_TYPED.relative_to(SRC_DIR)}")
    print(f" - {OUT_FWD.relative_to(SRC_DIR)}")
    print(f" - {CALC_DIR.relative_to(SRC_DIR)}/<module>.pyi + __init__.pyi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
