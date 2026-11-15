# Tutorial video generator

Records the "How to play" tutorial videos in `public/tutorial/` by playing a
**made-up demo tour** through the real app (fictional tour data via intercepted
Supabase requests, a procedurally drawn fictional map, simulated GPS walking,
caption overlays). Re-run after UI changes so the video matches the app.

```bash
pip install playwright numpy pillow && playwright install chromium
# build the app with dummy Supabase env and serve it
VITE_SUPABASE_URL=https://dummy.supabase.co VITE_SUPABASE_ANON_KEY=x VITE_SUPABASE_SERVICE_ROLE_KEY=x \
  npx vite build --outDir /tmp/dist-test && npx vite preview --outDir /tmp/dist-test --port 4173 &
cd scripts/tutorial-video
for l in en; do   # English first; add de tr fr once translated
  python3 record.py $l out-$l && python3 mix.py out-$l ../../public/tutorial/tutorial-$l.mp4 2.0
done
```

Captions and demo-tour content live in `texts.py` (one block per language).
