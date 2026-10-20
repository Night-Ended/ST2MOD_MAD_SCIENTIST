"""Seedream 4.0 image generation CLI (Volcano Ark).

A small, dependency-light wrapper around
    POST https://ark.cn-beijing.volces.com/api/v3/images/generations

Features
  * text to image, image to image, multi reference to image
  * sequential generation (a related set of N images) for Seedream 4.0
  * reference images can be local files (sent as data URIs, auto downscaled)
  * saves PNG + a metadata JSON next to it
  * batch mode driven by a JSON file
  * API key is stored outside the repo and entered interactively

Usable for any project, not just the MadScientist mod.

Examples
    python tools/seedream.py --set-key
    python tools/seedream.py "a cat" --size 2K
    python tools/seedream.py "same character, idle pose" --ref art/incoming/base.png -n 1
    python tools/seedream.py --batch art/prompts/01_base.json --out art/incoming/base
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is present in this workspace
    Image = None

ENDPOINT = os.environ.get("ARK_IMAGE_ENDPOINT", "https://ark.cn-beijing.volces.com/api/v3/images/generations")
DEFAULT_MODEL = "doubao-seedream-5-0-flash-260915"
KEY_FILE_DEFAULT = Path(os.environ.get("ARK_API_KEY_FILE", Path.home() / ".dsh" / "secrets" / "ark_api_key"))
MAX_REFS = 14


# --------------------------------------------------------------------------- #
# API key
# --------------------------------------------------------------------------- #
def load_key(explicit: str | None, key_file: Path) -> str | None:
    if explicit:
        return explicit.strip()
    env = os.environ.get("ARK_API_KEY", "").strip()
    if env:
        return env
    if key_file.exists():
        value = key_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    return None


def set_key(key_file: Path) -> None:
    import getpass

    print(f"Paste your Volcano Ark API key (input hidden). It will be stored in:\n  {key_file}")
    key = getpass.getpass("API key: ").strip()
    if not key:
        print("empty key, aborted", file=sys.stderr)
        raise SystemExit(1)
    if not re.fullmatch(r"[A-Za-z0-9\-_\.]{8,}", key):
        print("warning: this does not look like an Ark API key, saving anyway", file=sys.stderr)
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text(key + "\n", encoding="utf-8")
    try:
        key_file.chmod(0o600)
    except OSError:
        pass
    print(f"saved. ({len(key)} chars)")


# --------------------------------------------------------------------------- #
# reference images
# --------------------------------------------------------------------------- #
def encode_ref(path: Path, max_edge: int) -> tuple[str, int]:
    """Return (data_uri, original_size).  Downscales large images for the API."""
    raw = path.read_bytes()
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = raw
    if Image is not None and max_edge > 0:
        try:
            im = Image.open(io.BytesIO(raw))
            im.load()
            if max(im.size) > max_edge:
                im.thumbnail((max_edge, max_edge), Image.LANCZOS)
                buf = io.BytesIO()
                if im.mode not in ("RGB", "RGBA"):
                    im = im.convert("RGBA")
                im.save(buf, format="PNG", optimize=True)
                data = buf.getvalue()
                mime = "image/png"
        except Exception as e:  # noqa: BLE001
            print(f"warning: could not re-encode {path}: {e}", file=sys.stderr)
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}", len(data)


def resolve_refs(refs: list[str], base_dir: Path, max_edge: int) -> tuple[list[str], list[dict]]:
    uris, meta = [], []
    for r in refs:
        p = Path(r)
        if not p.is_absolute():
            p = (base_dir / p).resolve()
        if not p.exists():
            raise SystemExit(f"reference image not found: {p}")
        uri, size = encode_ref(p, max_edge)
        uris.append(uri)
        meta.append({"path": str(p), "bytes": size})
    return uris, meta


# --------------------------------------------------------------------------- #
# request
# --------------------------------------------------------------------------- #
def post_json(payload: dict, api_key: str, timeout: int, retries: int = 2) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last_err = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            ENDPOINT,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            try:
                msg = json.loads(detail)["error"]["message"]
            except Exception:  # noqa: BLE001
                msg = detail[:500]
            last_err = f"HTTP {e.code}: {msg}"
            if e.code in (401, 403, 400):
                break
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            break
        except urllib.error.URLError as e:
            last_err = f"network error: {e.reason}"
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            break
    raise SystemExit(f"Seedream request failed: {last_err}")


def build_payload(args, prompt: str, ref_uris: list[str]) -> dict:
    payload: dict = {
        "model": args.model or DEFAULT_MODEL,
        "prompt": prompt,
        "size": args.size,
        "response_format": "b64_json",
        "watermark": bool(args.watermark),
    }
    if ref_uris:
        payload["image"] = ref_uris if len(ref_uris) > 1 else ref_uris[0]
    if args.n > 1:
        payload["sequential_image_generation"] = "auto"
        payload["sequential_image_generation_options"] = {"max_images": args.n}
    return payload


def save_images(result: dict, out_dir: Path, name: str, meta: dict) -> list[Path]:
    items = result.get("data") or []
    if not items:
        raise SystemExit(f"no images in response: {json.dumps(result)[:400]}")

    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for i, item in enumerate(items, 1):
        suffix = f"_{i:02d}" if len(items) > 1 else ""
        target = out_dir / f"{name}{suffix}.png"

        if item.get("b64_json"):
            raw = base64.b64decode(item["b64_json"])
        elif item.get("url"):
            with urllib.request.urlopen(item["url"], timeout=120) as r:
                raw = r.read()
        else:
            continue

        if Image is not None:
            try:
                im = Image.open(io.BytesIO(raw))
                im.load()
                im.convert("RGBA").save(target)
            except Exception:  # noqa: BLE001
                target.write_bytes(raw)
        else:
            target.write_bytes(raw)

        saved.append(target)
        item_meta = dict(meta)
        item_meta.update({"index": i, "file": target.name, "usage": result.get("usage")})
        (out_dir / f"{name}{suffix}.json").write_text(
            json.dumps(item_meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return saved


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #
def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Seedream 4.0 (Volcano Ark) image generation helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("prompt", nargs="?", help="prompt text (omit when using --batch)")
    p.add_argument("--prompt-file", type=Path, help="read the prompt from a UTF-8 text file")
    p.add_argument("--batch", type=Path, help="run a batch JSON file (see docs/seedream.md)")
    p.add_argument("--only", help="comma separated job names to run from the batch")
    p.add_argument("--ref", action="append", default=[], help="reference image path (repeatable)")
    p.add_argument("--ref-max", type=int, default=1536, help="downscale refs so the long edge is <= N px (0 = off)")
    p.add_argument("--model", default=None, help=f"model id or endpoint id (default {DEFAULT_MODEL})")
    p.add_argument("--size", default="2K", help="1K / 2K / 4K or WIDTHxHEIGHT (multiples of 16)")
    p.add_argument("-n", "--n", type=int, default=1, help="generate a related set of N images (1-15)")
    p.add_argument("--out", type=Path, default=Path("seedream_out"), help="output directory")
    p.add_argument("--name", default=None, help="output file base name (default: prompt slug / job name)")
    p.add_argument("--watermark", action="store_true", help="ask the API to add a watermark (default off)")
    p.add_argument("--timeout", type=int, default=240, help="HTTP timeout in seconds")
    p.add_argument("--api-key", help="API key (prefer --set-key / ARK_API_KEY instead)")
    p.add_argument("--key-file", type=Path, default=KEY_FILE_DEFAULT, help=f"key file (default {KEY_FILE_DEFAULT})")
    p.add_argument("--set-key", action="store_true", help="prompt for an API key and store it")
    p.add_argument("--dry-run", action="store_true", help="print the payload without calling the API")
    return p


def slug(text: str, limit: int = 40) -> str:
    text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", text).strip("-")
    return (text[:limit] or "image").lower()


def run_one(args, prompt: str, refs: list[str], base_dir: Path, out_dir: Path, name: str | None) -> None:
    ref_uris, ref_meta = resolve_refs(refs, base_dir, args.ref_max)
    if len(ref_uris) > MAX_REFS:
        raise SystemExit(f"too many reference images ({len(ref_uris)} > {MAX_REFS})")
    if len(ref_uris) + args.n > 15:
        raise SystemExit("reference images + generated images must be <= 15")

    payload = build_payload(args, prompt, ref_uris)
    name = name or slug(prompt)

    if args.dry_run:
        preview = dict(payload)
        if "image" in preview:
            imgs = preview["image"] if isinstance(preview["image"], list) else [preview["image"]]
            preview["image"] = [f"<data uri {len(u) // 1024} KB>" for u in imgs]
        print(json.dumps({"endpoint": ENDPOINT, "payload": preview,
                          "refs": ref_meta, "out": str(out_dir), "name": name},
                         ensure_ascii=False, indent=2))
        return

    key = load_key(args.api_key, args.key_file)
    if not key:
        raise SystemExit(
            "no API key found.\n"
            f"  1) run:  python tools/seedream.py --set-key\n"
            f"  2) or set ARK_API_KEY\n"
            f"  3) or put the key in {args.key_file}"
        )

    print(f"-> {args.model or DEFAULT_MODEL} size={args.size} n={args.n} refs={len(ref_uris)} prompt={len(prompt)} chars")
    started = time.time()
    result = post_json(payload, key, args.timeout)
    elapsed = time.time() - started

    meta = {
        "prompt": prompt,
        "model": args.model or DEFAULT_MODEL,
        "size": args.size,
        "n": args.n,
        "refs": ref_meta,
        "endpoint": ENDPOINT,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_s": round(elapsed, 1),
    }
    saved = save_images(result, out_dir, name, meta)
    for path in saved:
        print(f"saved {path}  ({path.stat().st_size // 1024} KB)  {elapsed:.1f}s")


def run_batch(args, batch_path: Path, out_dir: Path) -> None:
    spec = json.loads(batch_path.read_text(encoding="utf-8"))
    defaults = spec.get("defaults", {})
    jobs = spec.get("jobs", [])
    if not jobs:
        raise SystemExit(f"no jobs in {batch_path}")

    wanted = {n.strip() for n in args.only.split(",")} if args.only else None
    base_dir = batch_path.parent
    for i, job in enumerate(jobs, 1):
        prompt = job.get("prompt", "")
        if not prompt:
            raise SystemExit(f"job #{i} has no prompt")
        refs = job.get("refs", defaults.get("refs", []))
        # local overrides for this job
        saved_attrs = (args.model, args.size, args.n)
        if args.model is None and ("model" in job or "model" in defaults):
            args.model = job.get("model", defaults.get("model"))
        if "size" in job or "size" in defaults:
            args.size = job.get("size", defaults.get("size", args.size))
        if "n" in job or "n" in defaults:
            args.n = int(job.get("n", defaults.get("n", args.n)))

        name = job.get("name") or f"job{i:02d}"
        if wanted and name not in wanted:
            continue
        print(f"=== [{i}/{len(jobs)}] {name}")
        try:
            run_one(args, prompt, refs, base_dir, out_dir, name)
        finally:
            args.model, args.size, args.n = saved_attrs


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    args = make_parser().parse_args()

    if args.set_key:
        set_key(args.key_file)
        return

    if args.batch:
        run_batch(args, args.batch.resolve(), args.out)
        return

    prompt = args.prompt
    if args.prompt_file:
        prompt = args.prompt_file.read_text(encoding="utf-8")
    if not prompt:
        raise SystemExit("missing prompt (or use --batch)")

    run_one(args, prompt, args.ref, Path.cwd(), args.out, args.name)


if __name__ == "__main__":
    main()
