# Dagster UI Guide for Airflow Users

## 🔄 Key Mindset Shift: Tasks vs Assets

**Airflow**: You think about **TASKS** (what to run)
- "Run this Python function, then run that SQL query"
- Focus on the execution steps

**Dagster**: You think about **ASSETS** (what to create)
- "Create this table, which depends on that API data"
- Focus on the data products

## 📍 Navigating the Dagster UI

### Main Navigation (Left Sidebar)

| Icon/Tab | Airflow Equivalent | What It Does |
|----------|-------------------|--------------|
| **Assets** | DAGs page | View all your data assets and their relationships |
| **Jobs** | DAGs (but simpler) | Pre-defined groups of assets to run together |
| **Runs** | DAG Runs | View execution history |
| **Schedules** | DAGs with schedule_interval | View and enable/disable schedules |
| **Sensors** | Sensors | Event-driven triggers |
| **Overview** | Home | Dashboard view |

## 🎯 Step-by-Step: Running Your Pipeline

### In Airflow, you would:
1. Go to DAGs page
2. Find your DAG
3. Click the "Play" button to trigger
4. Watch tasks turn green one by one

### In Dagster, you:

#### **Step 1: Go to Assets Page**
- Click **"Assets"** in the left sidebar (or it's the default view)
- This is your main workspace (like Airflow's DAGs page)

#### **Step 2: View the Asset Graph**
You'll see a **visual graph** showing your data pipeline:
```
raw_users ──┐
            ├──> cleaned_users ──┐
raw_posts ──┘                    ├──> enriched_posts ──┬──> posts_analytics
                                 │                      └──> company_analytics
```

**What this means:**
- Each box = a data asset (like a table, file, or dataset)
- Arrows = dependencies (what needs what)
- This is **automatic** - Dagster builds it from your code!

**In Airflow:**
- You'd see tasks in a graph
- You have to manually define dependencies with `>>`
- Focus is on execution order

**In Dagster:**
- You see data products
- Dependencies come from function parameters
- Focus is on data lineage

#### **Step 3: Materialize Assets (= Run the Pipeline)**

There are several ways to run assets:

**Option A: Materialize All (Run Everything)**
1. Click the **"Materialize all"** button (top right)
2. This runs all 6 assets in the correct order
3. Similar to triggering an entire DAG in Airflow

**Option B: Materialize One Asset**
1. Click on any asset box in the graph
2. Click **"Materialize"** in the right panel
3. Dagster will automatically run dependencies first
4. Example: Click `posts_analytics` → Dagster runs `raw_users`, `raw_posts`, `cleaned_users`, and `enriched_posts` first!

**Option C: Materialize Selected Assets**
1. Click checkboxes next to multiple assets
2. Click **"Materialize selected"**

#### **Step 4: Watch Execution**

After clicking Materialize:
1. You'll be redirected to the **Run** page (like Airflow's DAG Run view)
2. Watch assets change color:
   - **Gray** = Not started
   - **Blue** = Running
   - **Green** = Success
   - **Red** = Failed

3. Click on any asset to see:
   - Logs (like Airflow task logs)
   - Execution time
   - Input/output metadata

## 📊 Understanding the Asset Graph

### Color Coding
- **Green checkmark** = Successfully materialized (data exists)
- **Empty/gray** = Never materialized (no data yet)
- **Blue** = Currently running
- **Red** = Failed

### Viewing Asset Details

Click any asset to see the right panel with:

**"Overview" Tab:**
- Description (from your docstring)
- Last materialization time
- Dependencies (upstream/downstream)

**"Partitions" Tab:** (advanced - ignore for now)

**"Events" Tab:**
- History of materializations (like Airflow's task instance history)

**"Plots" Tab:** (for custom visualizations)

## 🎮 Common Tasks: Airflow vs Dagster

### 1. Run the Entire Pipeline

**Airflow:**
```
1. Go to DAGs
2. Find your DAG
3. Click "Trigger DAG" play button
4. Go to DAG Runs to watch
```

**Dagster:**
```
1. Go to Assets
2. Click "Materialize all"
3. Automatically taken to Run view
```

### 2. Run One Task/Asset

**Airflow:**
```
1. Go to DAG
2. Click on task
3. Click "Run" → "Run task"
4. Only that task runs (dependencies don't auto-run)
```

**Dagster:**
```
1. Go to Assets
2. Click asset
3. Click "Materialize"
4. Dependencies automatically run first!
```

### 3. View Execution Logs

**Airflow:**
```
1. Go to DAG
2. Click task
3. Click "Log"
```

**Dagster:**
```
1. Go to Runs (sidebar)
2. Click a run
3. Click an asset to see logs
OR
1. In Assets view, click asset
2. Click "Events" tab
3. Click a materialization event
```

### 4. View Lineage/Dependencies

**Airflow:**
```
1. Go to DAG
2. Click "Graph" view
3. See task dependencies
```

**Dagster:**
```
1. Go to Assets (default view)
2. See entire lineage graph immediately
3. More detailed than Airflow!
```

### 5. Enable/Disable Schedules

**Airflow:**
```
1. Go to DAGs
2. Toggle the switch next to DAG
```

**Dagster:**
```
1. Go to Schedules (sidebar)
2. Toggle the switch next to schedule
```

## 🔍 Exploring Your Sample Pipeline

Let's understand what you see for our sample pipeline:

### The 6 Assets You Have:

1. **raw_users** (🟢 Top Left)
   - Fetches users from API
   - No dependencies (starts first)

2. **raw_posts** (🟢 Top Left)
   - Fetches posts from API
   - No dependencies (runs in parallel with raw_users)

3. **cleaned_users** (🟡 Middle)
   - Cleans user data
   - Depends on: raw_users

4. **enriched_posts** (🟡 Middle)
   - Joins posts with user data
   - Depends on: raw_posts AND cleaned_users

5. **posts_analytics** (🔵 Right)
   - User-level statistics
   - Depends on: enriched_posts

6. **company_analytics** (🔵 Right)
   - Company-level statistics
   - Depends on: enriched_posts

### What Happens When You Click "Materialize all":

1. **Dagster runs `raw_users` and `raw_posts` in PARALLEL** ⚡
   - Like having two tasks with no dependencies in Airflow

2. **Then runs `cleaned_users`** (once raw_users is done)

3. **Then runs `enriched_posts`** (once both raw_posts and cleaned_users are done)

4. **Finally runs `posts_analytics` and `company_analytics` in PARALLEL** ⚡

Total execution: ~5-10 seconds (because of parallel execution!)

## 🆚 Side-by-Side Comparison

### Starting the UI

| Task | Airflow | Dagster |
|------|---------|---------|
| Start server | `docker-compose up` (need Docker) | `make dev` (no Docker!) |
| Access URL | http://localhost:8080 | http://localhost:3000 |
| Login required | Yes (airflow/airflow) | No |

### Main Workflow

| Action | Airflow | Dagster |
|--------|---------|---------|
| See pipelines | Click "DAGs" | Click "Assets" (default) |
| Run pipeline | Trigger DAG → watch in Grid | Materialize all → auto-watch |
| View structure | Graph tab | Asset graph (default view) |
| Check logs | DAG → Task → Logs | Runs → Run → Asset |
| See data lineage | Limited, manual | Automatic, comprehensive |

## 💡 Pro Tips for Airflow Users

1. **"Materialize" = "Run"**
   - When you see "Materialize", think "Run this task/DAG"

2. **Assets show data, not execution**
   - Green checkmark = data exists (was created)
   - Not about "task succeeded" but "data is available"

3. **Automatic dependency resolution**
   - Unlike Airflow, you don't manually trigger dependencies
   - Dagster figures out what needs to run

4. **No start_date or catchup**
   - Just materialize assets when you want
   - Use schedules for regular updates

5. **Testing is easier**
   - Click one asset → Materialize
   - Don't need to run the whole pipeline

6. **Backfills are different**
   - In Airflow: Clear tasks, re-run
   - In Dagster: Just materialize assets again

## 🎯 Try This Now!

1. **Go to http://localhost:3000** (if `make dev` is running)

2. **Click "Assets"** in the left sidebar

3. **See the graph** of your 6 assets

4. **Click "Materialize all"** (top right button)

5. **Watch the execution**:
   - See raw_users and raw_posts turn blue (running)
   - Then turn green (success)
   - Watch the cascade through the pipeline

6. **Click on `posts_analytics`** asset

7. **View the logs** to see what data was created

8. **Click "Assets"** again to return to the graph

9. **Try materializing just `company_analytics`**:
   - Click the asset
   - Click "Materialize"
   - Notice how Dagster runs enriched_posts first automatically!

## ❓ Common Questions

**Q: Where's the DAG file?**
A: Look at `src/ingestion_sample/defs/assets.py` - your assets ARE the DAG!

**Q: How do I see task instances?**
A: Go to Runs → Click a run → See all asset executions

**Q: Where are my schedules?**
A: Schedules sidebar. Enable `daily_pipeline_schedule` to run daily.

**Q: How do I pass data between tasks?**
A: Just return from one asset, receive as parameter in another. No XCom needed!

**Q: Can I trigger manually like Airflow?**
A: Yes! "Materialize" = manual trigger. Schedules = automatic trigger.

**Q: Where's the Gantt chart?**
A: In a Run view, you can see timing. But Dagster focuses more on lineage than timing.

## 🚀 Next Steps

1. Materialize your pipeline a few times
2. Check the "Runs" page to see history
3. Try enabling the schedule (Schedules → toggle switch)
4. Modify an asset in `assets.py` and re-materialize
5. Add your own asset!

---

**Need more help?**
- Dagster Docs: https://docs.dagster.io
- Your pipeline code: `src/ingestion_sample/defs/assets.py`
- Comparison guide: `AIRFLOW_COMPARISON.md`
