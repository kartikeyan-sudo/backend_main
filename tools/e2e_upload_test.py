import os
import time
import tempfile
import cv2
import requests

API = os.getenv("API_URL", "http://localhost:8000")


def make_test_video(path, frames=12, w=160, h=120, fps=5):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, fps, (w, h))
    for i in range(frames):
        frame = (255 * ((i % 2) * 1) * (i % 3) * 0 + 0 * 1) + (i * 20 % 255)
        import numpy as np
        f = np.ones((h, w, 3), dtype="uint8") * ((i * 20) % 255)
        out.write(f)
    out.release()


def upload_and_wait(video_path, folder=None, timeout=300):
    files = {"file": open(video_path, "rb")}
    data = {}
    if folder:
        data["folder"] = folder
    print(f"Uploading {video_path} to {API}/upload ...")
    r = requests.post(f"{API}/upload", files=files, data=data)
    files["file"].close()
    if r.status_code != 200:
        print("Upload failed:", r.status_code, r.text)
        return
    job = r.json()
    job_id = job.get("job_id")
    print("Job queued:", job_id)

    start = time.time()
    while True:
        r = requests.get(f"{API}/status/{job_id}")
        if r.status_code != 200:
            print("Status request failed:", r.status_code, r.text)
            return
        s = r.json()
        print(f"Status: {s.get('status')} progress={s.get('progress')} message={s.get('message')}")
        if s.get("status") == "completed":
            print("Completed! result:", s.get("result_url"))
            return s
        if s.get("status") == "failed":
            print("Job failed:", s.get("message"))
            return s
        if time.time() - start > timeout:
            print("Timed out waiting for job")
            return s
        time.sleep(2)


def main():
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp_path = tmp.name
    tmp.close()
    make_test_video(tmp_path)
    folder = os.getenv("DEFAULT_CLOUD_FOLDER", "test_e2e")
    res = upload_and_wait(tmp_path, folder=folder, timeout=600)
    print("Done. Result object:\n", res)
    try:
        os.unlink(tmp_path)
    except Exception:
        pass


if __name__ == "__main__":
    main()
