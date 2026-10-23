"""Runs every field and metric of the semantic model against SQLite built from the app's real
D1 migrations, with a few synthetic rows. Proves each definition references real columns and
returns a sensible value. Usage: python check_against_db.py <model.yaml> <migrations_dir>"""
import sqlite3, sys, yaml, pathlib, re
model = yaml.safe_load(open(sys.argv[1]))
db = sqlite3.connect(":memory:")
for p in sorted(pathlib.Path(sys.argv[2]).glob("*.sql")):
    db.executescript(p.read_text())
# Synthetic data: 1 family, 2 children, 3 rounds, 2 lessons, 3 uploads (ready, rejected, ready).
db.executescript("""
INSERT INTO families(id,auth_user_id) VALUES ('f1','u1');
INSERT INTO children(id,family_id,display_name,xp) VALUES ('c1','f1','x',30),('c2','f1','y',0);
INSERT INTO activities(id,activity_type,skill,title,content_json) VALUES ('basics-abc','basics','letters','ABC','{}');
INSERT INTO activity_attempts(id,child_id,activity_id,score,xp_earned,completed_at) VALUES
 ('a1','c1','basics-abc',100,10,CURRENT_TIMESTAMP),('a2','c1','basics-abc',50,5,CURRENT_TIMESTAMP),('a3','c2','basics-abc',100,10,CURRENT_TIMESTAMP);
INSERT INTO assignments(id,child_id,title,source) VALUES ('s1','c1','Our planet','ai-upload:u1'),('s2','c2','Unit 2','legacy:school-page');
INSERT INTO assignment_completions(id,child_id,assignment_id,score,xp_earned) VALUES ('k1','c1','s1',80,8);
INSERT INTO learning_uploads(id,child_id,assignment_id,object_key,mime_type,status,approval_status,judge_decision,estimated_cost_usd,judge_estimated_cost_usd)
 VALUES ('u1','c1','s1','k','image/png','ready','approved','approve',0.0012,0.0001),
        ('u2','c1',NULL,'k','image/png','rejected','rejected','reject',NULL,0.0001),
        ('u3','c2',NULL,'k','image/png','ready','approved','review',0.0010,0.0001);
INSERT INTO mastery(child_id,skill,item_key,mastery_score,correct_count,wrong_count) VALUES ('c1','vocabulary','apple',0.8,4,1),('c1','vocabulary','tree',0.4,1,3);
""")
def ansi(e): return next(d["expression"] for d in e["dialects"] if d["dialect"]=="ANSI_SQL")
def table(ds): return ds["source"].split(".")[-1]
def view(ds):  # the dataset as its declared fields
    cols = ", ".join(f'{ansi(f["expression"])} AS "{f["name"]}"' for f in ds["fields"])
    return f'SELECT {cols} FROM {table(ds)}'
def sqlite_ok(expr): return expr.replace("AS DECIMAL", "AS REAL")  # ANSI DECIMAL -> SQLite REAL
results, errors = [], []
by = {d["name"]: d for d in model["datasets"]}
for ds in model["datasets"]:
    try: db.execute(view(ds)).fetchall()
    except Exception as e: errors.append(f'{ds["name"]} fields: {e}')
    for mt in ds.get("metrics", []):
        q = f'SELECT {sqlite_ok(ansi(mt["expression"]))} FROM ({view(ds)})'
        try: results.append((f'{ds["name"]}.{mt["name"]}', db.execute(q).fetchone()[0]))
        except Exception as e: errors.append(f'{ds["name"]}.{mt["name"]}: {e}')
# Model metrics, with Ossie measure semantics (relational_semantics.md, G2): every aggregate is
# evaluated over its own dataset's rows, so combining datasets never fans out or double-counts.
import sqlglot
from sqlglot import exp
for mt in model.get("metrics", []):
    tree = sqlglot.parse_one(ansi(mt["expression"]), read="sqlite")
    def as_measure(node):
        if isinstance(node, exp.AggFunc):
            owners = {c.table for c in node.find_all(exp.Column)}
            if len(owners) == 1:
                ds = owners.pop()
                inner = node.copy()
                for c in inner.find_all(exp.Column): c.set("table", None)
                return sqlglot.parse_one(f"(SELECT {inner.sql(dialect='sqlite')} FROM ({view(by[ds])}))", read="sqlite")
        return node
    q = "SELECT " + sqlite_ok(tree.transform(as_measure).sql(dialect="sqlite"))
    try: results.append((mt["name"], db.execute(q).fetchone()[0]))
    except Exception as e: errors.append(f'{mt["name"]}: {e} :: {q}')
# Expected values for the synthetic rows above, worked out by hand.
EXPECTED = {"CHILD.total_xp": 30, "ACTIVITY_ATTEMPT.game_xp": 25, "ACTIVITY_ATTEMPT.avg_round_score": 250/3,
    "ACTIVITY_ATTEMPT.perfect_round_rate": 2/3, "ASSIGNMENT.ai_lessons": 1, "ASSIGNMENT_COMPLETION.lesson_xp": 8,
    "LEARNING_UPLOAD.auto_decision_rate": 2/3, "LEARNING_UPLOAD.ai_cost_usd": 0.0025,
    "LEARNING_UPLOAD.ai_cost_per_ready_lesson_usd": 0.00125, "MASTERY.answer_accuracy": 5/9,
    "total_earned_xp": 33, "active_learners": 2, "lesson_completion_rate": 0.5, "ai_cost_per_active_learner_usd": 0.0011}
got = dict(results)
for k, want in EXPECTED.items():
    if k not in got or got[k] is None or abs(float(got[k]) - want) > 1e-9:
        errors.append(f"{k}: expected {want}, got {got.get(k)}")
# Every synonym must point to exactly one metric or field, or an AI has to guess.
from collections import defaultdict
owners = defaultdict(set)
def collect(obj, label):
    ai = obj.get("ai_context")
    if isinstance(ai, dict):
        for s in ai.get("synonyms", []): owners[s.casefold()].add(label)
for ds in model["datasets"]:
    collect(ds, ds["name"])
    for x in ds.get("fields", []) + ds.get("metrics", []): collect(x, f'{ds["name"]}.{x["name"]}')
for x in model.get("metrics", []): collect(x, x["name"])
for s, who in owners.items():
    if len(who) > 1: errors.append(f"synonym '{s}' is used by {sorted(who)}")
for n, v in results: print(f"  {n:45} {v}")
print(f"\n{len(results)} metrics executed, {len(errors)} errors"); [print("  ERROR", e) for e in errors]
sys.exit(1 if errors else 0)
