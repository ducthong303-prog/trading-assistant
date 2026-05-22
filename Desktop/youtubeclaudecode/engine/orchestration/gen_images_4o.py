#!/usr/bin/env python3
"""Generate 28 images via KieAI GPT-4o API. Single webhook for all jobs."""
import sys, json, time, requests, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_KEY = "27e835b5dac34ff6ed36aa8d8f6bbd6c"
API_URL = "https://api.kie.ai/api/v1/gpt4o-image/generate"
IMG_DIR = ROOT / "channels/bible-explainer/images/every-time-jesus-wept"
SESSION = requests.Session()
SESSION.headers.update({"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})


def load_prompts():
    prompts = []
    for pf in sorted(IMG_DIR.glob("part*_prompts.md")):
        text = pf.read_text()
        blocks = re.split(r'\n## Prompt \d+:', text)
        for i, block in enumerate(blocks[1:], 1):
            prompt = block.split('\n---')[0].strip()
            if prompt:
                pnum = int(re.search(r'part(\d+)', pf.stem).group(1))
                prompts.append({"id": f"img_{pnum:02d}_{i:03d}", "prompt": prompt})
    return prompts


def submit_all(prompts, callback_url):
    """Submit all jobs, return dict of id → taskId."""
    tasks = {}
    for p in prompts:
        try:
            r = SESSION.post(API_URL, json={
                "prompt": p["prompt"],
                "size": "3:2",
                "callBackUrl": callback_url,
            }, timeout=30)
            r.raise_for_status()
            tid = r.json().get("data", {}).get("taskId", "")
            if tid:
                tasks[p["id"]] = tid
                print(f"  Submit {p['id']}: {tid[:16]}...")
            time.sleep(0.3)
        except Exception as e:
            print(f"  Submit FAIL {p['id']}: {e}")
    return tasks


def poll_and_download(wh_uuid, tasks, max_wait=300):
    """Poll webhook until all tasks have callbacks, download images."""
    downloaded = set()
    results = {}
    start = time.time()

    while time.time() - start < max_wait and len(downloaded) < len(tasks):
        try:
            r = requests.get(
                f"https://webhook.site/token/{wh_uuid}/requests?sorting=newest",
                headers={"Accept": "application/json"}, timeout=10)
            reqs = r.json().get("data", [])

            for req in reqs:
                try:
                    data = json.loads(req.get("content", "{}"))
                except Exception:
                    continue

                # 4o format: {"code":200, "data": {"taskId": "...", "info": {"result_urls": [...]}}}
                inner = data.get("data", {})
                tid = inner.get("taskId", "")

                if tid in tasks.values() and tid not in downloaded:
                    urls = inner.get("info", {}).get("result_urls", [])
                    if urls:
                        # Find which prompt this taskId belongs to
                        for pid, ptid in tasks.items():
                            if ptid == tid:
                                # Download
                                try:
                                    img = SESSION.get(urls[0], timeout=60).content
                                    fp = IMG_DIR / f"{pid}.jpeg"
                                    fp.write_bytes(img)
                                    results[pid] = str(fp)
                                    downloaded.add(tid)
                                    print(f"  Done {pid}: {len(downloaded)}/{len(tasks)}")
                                except Exception as e:
                                    print(f"  Download FAIL {pid}: {e}")
                                break
        except Exception as e:
            pass
        time.sleep(3)

    return results


def main():
    prompts = load_prompts()
    print(f"Generate {len(prompts)} ảnh GPT-4o\n")

    # Tạo 1 webhook cho tất cả
    wh_uuid = requests.post("https://webhook.site/token",
                            headers={"Accept": "application/json"}, timeout=10).json().get("uuid")
    callback = f"https://webhook.site/{wh_uuid}"
    print(f"Webhook: {callback}\n")

    # Submit tất cả jobs
    print("Submit 28 jobs...")
    tasks = submit_all(prompts, callback)
    print(f"  → {len(tasks)} jobs submitted\n")

    # Poll + download
    print("Polling callback & downloading...")
    results = poll_and_download(wh_uuid, tasks)

    ok = len(results)
    print(f"\n{'='*50}")
    print(f"  {ok}/{len(prompts)} ảnh thành công")
    if ok < len(prompts):
        missing = [pid for pid in tasks if pid not in results]
        print(f"  Missing: {missing}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
