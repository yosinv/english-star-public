-- Structure of the 8 tables the semantic model reads (no data).
-- Generated from the app's D1 migrations so check_against_db.py can run without the private repo.

CREATE TABLE families (
  id TEXT PRIMARY KEY,
  auth_user_id TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
, is_frozen INTEGER NOT NULL DEFAULT 0 CHECK (is_frozen IN (0,1)), frozen_at TEXT, frozen_reason TEXT, frozen_by_family_id TEXT);

CREATE TABLE children (
  id TEXT PRIMARY KEY,
  family_id TEXT NOT NULL,
  display_name TEXT NOT NULL,
  avatar_object_key TEXT,
  level INTEGER NOT NULL DEFAULT 1,
  grade_band TEXT,
  instruction_language TEXT NOT NULL DEFAULT 'he',
  xp INTEGER NOT NULL DEFAULT 0,
  gems INTEGER NOT NULL DEFAULT 0,
  streak INTEGER NOT NULL DEFAULT 1,
  last_active_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, avatar_uploaded_at TEXT,
  FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
);

CREATE TABLE activities (
  id TEXT PRIMARY KEY,
  activity_type TEXT NOT NULL,
  skill TEXT NOT NULL,
  interest_pack_id TEXT,
  difficulty INTEGER NOT NULL DEFAULT 1,
  title TEXT NOT NULL,
  content_json TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (interest_pack_id) REFERENCES interest_packs(id)
);

CREATE TABLE activity_attempts (
  id TEXT PRIMARY KEY,
  child_id TEXT NOT NULL,
  activity_id TEXT NOT NULL,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  score REAL NOT NULL DEFAULT 0,
  xp_earned INTEGER NOT NULL DEFAULT 0,
  metadata_json TEXT,
  FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
  FOREIGN KEY (activity_id) REFERENCES activities(id)
);

CREATE TABLE assignments (
  id TEXT PRIMARY KEY,
  child_id TEXT NOT NULL,
  title TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'parent',
  due_date TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE
);

CREATE TABLE assignment_completions (
  id TEXT PRIMARY KEY,
  child_id TEXT NOT NULL,
  assignment_id TEXT NOT NULL,
  score REAL NOT NULL DEFAULT 0,
  xp_earned INTEGER NOT NULL DEFAULT 0,
  completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(child_id, assignment_id),
  FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
  FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE
);

CREATE TABLE learning_uploads (
  id TEXT PRIMARY KEY,
  child_id TEXT NOT NULL,
  assignment_id TEXT,
  object_key TEXT NOT NULL,
  original_filename TEXT,
  mime_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'uploaded',
  ai_model TEXT,
  extracted_summary TEXT,
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  processed_at TEXT, file_size_bytes INTEGER, source_tokens INTEGER, prompt_tokens INTEGER, completion_tokens INTEGER, total_tokens INTEGER, estimated_neurons REAL, estimated_cost_usd REAL, ai_provider TEXT, content_sha256 TEXT, requested_title TEXT, approval_status TEXT NOT NULL DEFAULT 'pending', approved_at TEXT, rejected_at TEXT, approved_by_family_id TEXT, admin_note TEXT, processing_started_at TEXT, judge_decision TEXT, judge_confidence REAL, judge_reason_code TEXT, judge_reason TEXT, judge_model TEXT, judge_prompt_tokens INTEGER, judge_completion_tokens INTEGER, judge_total_tokens INTEGER, judge_estimated_neurons REAL, judge_estimated_cost_usd REAL, judged_at TEXT, judge_features_json TEXT, image_deleted_at TEXT,
  FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
  FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE SET NULL
);

CREATE TABLE mastery (
  child_id TEXT NOT NULL,
  skill TEXT NOT NULL,
  item_key TEXT NOT NULL,
  mastery_score REAL NOT NULL DEFAULT 0,
  last_seen_at TEXT,
  next_review_at TEXT,
  correct_count INTEGER NOT NULL DEFAULT 0,
  wrong_count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (child_id, skill, item_key),
  FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE
);
