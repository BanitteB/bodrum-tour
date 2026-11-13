-- ============================================================
-- 016 — Sync with the live schema of the original project
--
-- The original Supabase project (bkipxsboxfqmknhasyop) had a few changes that
-- were made directly in the dashboard and never captured in a migration.
-- This file brings a fresh project built from 001–015 to the same state.
-- Every statement is idempotent, so it is safe to re-run.
-- ============================================================

-- ── Columns ──────────────────────────────────────────────────
-- preview_token is TEXT without a default on live; the app generates it
-- itself (crypto.randomUUID() in lib/api.js).
ALTER TABLE tours ALTER COLUMN preview_token DROP DEFAULT;
ALTER TABLE tours ALTER COLUMN preview_token TYPE TEXT USING preview_token::text;

UPDATE tours SET sort_order = 0 WHERE sort_order IS NULL;
ALTER TABLE tours ALTER COLUMN sort_order SET NOT NULL;

ALTER TABLE skip_reports ALTER COLUMN tour_id SET NOT NULL;

-- ── Constraints / indexes ────────────────────────────────────
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tours_preview_token_unique') THEN
    ALTER TABLE tours ADD CONSTRAINT tours_preview_token_unique UNIQUE (preview_token);
  END IF;
END $$;

-- Required by upsertTourProgress (onConflict: 'tour_id,device_id').
CREATE UNIQUE INDEX IF NOT EXISTS tour_progress_tour_device_key
  ON tour_progress USING btree (tour_id, device_id);

-- ── Policies ─────────────────────────────────────────────────
DROP POLICY IF EXISTS "Admins can manage tours" ON tours;
CREATE POLICY "Admins can manage tours" ON tours FOR ALL
  USING (auth.uid() IN (SELECT id FROM admin_users))
  WITH CHECK (auth.uid() IN (SELECT id FROM admin_users));

DROP POLICY IF EXISTS "Admins can manage stops" ON tour_stops;
CREATE POLICY "Admins can manage stops" ON tour_stops FOR ALL
  USING (auth.uid() IN (SELECT id FROM admin_users))
  WITH CHECK (auth.uid() IN (SELECT id FROM admin_users));

DROP POLICY IF EXISTS "Admins can read all purchases" ON purchases;
CREATE POLICY "Admins can read all purchases" ON purchases FOR SELECT
  USING (auth.uid() IN (SELECT id FROM admin_users));

DROP POLICY IF EXISTS "Admins can read all progress" ON tour_progress;
CREATE POLICY "Admins can read all progress" ON tour_progress FOR SELECT
  USING (auth.uid() IN (SELECT id FROM admin_users));

DROP POLICY IF EXISTS "Anyone can read tour_progress" ON tour_progress;
CREATE POLICY "Anyone can read tour_progress" ON tour_progress FOR SELECT
  USING (true);

DROP POLICY IF EXISTS "Admins can read all stop progress" ON stop_progress;
CREATE POLICY "Admins can read all stop progress" ON stop_progress FOR SELECT
  USING (auth.uid() IN (SELECT id FROM admin_users));

DROP POLICY IF EXISTS "Anyone can read stop_progress" ON stop_progress;
CREATE POLICY "Anyone can read stop_progress" ON stop_progress FOR SELECT
  USING (true);

DROP POLICY IF EXISTS "admin_read_skip_reports" ON skip_reports;
CREATE POLICY "admin_read_skip_reports" ON skip_reports FOR SELECT
  USING (auth.uid() IN (SELECT id FROM admin_users));

DROP POLICY IF EXISTS "anon_insert_skip_reports" ON skip_reports;
CREATE POLICY "anon_insert_skip_reports" ON skip_reports FOR INSERT
  TO anon WITH CHECK (true);

NOTIFY pgrst, 'reload schema';
