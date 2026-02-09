# Dagster UI Guide

A comprehensive guide to navigating and using the Dagster web interface.

## Getting Started

### Launching the UI

```bash
make dev
```

Access the UI at: **http://localhost:3000**

## Main Navigation (Left Sidebar)

| Tab | Purpose |
|-----|---------|
| **Overview** | Dashboard with recent runs and asset health |
| **Assets** | View all data assets and their lineage graph |
| **Jobs** | Pre-configured groups of assets to run together |
| **Runs** | Execution history and logs |
| **Schedules** | View and manage scheduled jobs |
| **Sensors** | Event-driven triggers |
| **Resources** | External connections (databases, APIs, etc.) |

## Understanding Assets

### What is an Asset?

An **asset** represents a data product:
- Database table
- File (CSV, Parquet, etc.)
- ML model
- Dashboard
- API endpoint data

### The Asset Graph

The main **Assets** page shows a visual graph of your data pipeline:

```
raw_users ──┐
            ├──> cleaned_users ──┐
raw_posts ──┘                    ├──> enriched_posts ──┬──> posts_analytics
                                 │                      └──> company_analytics
```

**What the graph shows:**
- Each box = a data asset
- Arrows = dependencies (what depends on what)
- Automatically generated from your code

### Asset Status Colors

- **Green checkmark** ✓ = Successfully materialized (data exists)
- **Empty/gray** = Never materialized (no data yet)
- **Blue** = Currently running
- **Red** = Failed
- **Yellow** = Stale (upstream data changed)

## Running Your Pipeline

### Option 1: Materialize All

**Button:** "Materialize all" (top right)

This runs all assets in the correct order, respecting dependencies.

### Option 2: Materialize One Asset

1. Click on an asset in the graph
2. Click "Materialize" in the right panel
3. Dagster automatically runs dependencies first

**Example:** Click `posts_analytics` → Dagster runs `raw_users`, `raw_posts`, `cleaned_users`, and `enriched_posts` first!

### Option 3: Materialize Selected Assets

1. Click checkboxes next to multiple assets
2. Click "Materialize selected"

## Viewing Asset Details

Click any asset to see the right panel with tabs:

### Overview Tab
- **Description**: From your asset's docstring
- **Last materialization**: When it was last run
- **Compute kind**: Type of operation (Python, SQL, etc.)
- **Dependencies**: Upstream (inputs) and downstream (outputs)

### Partitions Tab
For partitioned assets (e.g., data by date, region, etc.)
- View partition status
- Materialize specific partitions
- See backfill progress

### Events Tab
History of materializations:
- When it ran
- How long it took
- Success/failure status
- Click an event to see logs

### Metadata Tab
Custom metadata from your code:
- Record counts
- File paths
- Data previews
- Statistics

### Plots Tab
Custom visualizations defined in your asset code

## Viewing Execution Details

### The Runs Page

After materializing assets, you're taken to the **Run** page:

1. **Run timeline**: Visual representation of asset execution
2. **Asset list**: All assets in this run
3. **Status indicators**: Running (blue), success (green), failed (red)

### Viewing Logs

**Option 1: From a Run**
1. Go to "Runs" in sidebar
2. Click a run
3. Click an asset to see its logs

**Option 2: From an Asset**
1. Click asset in graph
2. Go to "Events" tab
3. Click a materialization event
4. View logs

### Understanding Logs

Logs show:
- INFO messages from `context.log.info(...)`
- Step execution details
- Data loading/saving messages
- Error stack traces (if failed)

## Working with Schedules

### Viewing Schedules

1. Click "Schedules" in sidebar
2. See all defined schedules
3. View next run time

### Enabling/Disabling a Schedule

- Toggle the switch next to the schedule name
- Enabled schedules run automatically at their configured time

### Testing a Schedule

- Click schedule name
- Click "Test Schedule" to see what would run
- Click "Launch Run" to run immediately

## Common Workflows

### 1. Initial Setup - Run Everything

```
1. Go to Assets
2. Click "Materialize all"
3. Watch execution in Run view
4. Check logs if anything fails
```

### 2. Update One Asset

```
1. Modify asset code
2. Go to Assets
3. Click the modified asset
4. Click "Materialize"
5. View updated data in metadata
```

### 3. Investigate a Failure

```
1. Go to Runs
2. Find failed run (red)
3. Click it
4. Click failed asset
5. Read error logs
6. Fix code
7. Re-materialize
```

### 4. Check Data Quality

```
1. Go to Assets
2. Click asset
3. View Metadata tab
4. Check preview/statistics
5. View Events for history
```

### 5. Backfill Historical Data

For partitioned assets:
```
1. Click asset
2. Go to Partitions tab
3. Select date/partition range
4. Click "Materialize"
5. Monitor backfill progress
```

## UI Features

### Global Search

- Press `/` or click search bar
- Search for assets, runs, schedules
- Quick navigation

### Filters

On Assets page:
- Filter by status (materialized, failed, etc.)
- Filter by compute kind (Python, SQL, etc.)
- Filter by tag

### Asset Groups

Group related assets:
- Shown in sidebar under Assets
- Click group to view only those assets
- Organize large projects

### Live Updates

- Run status updates in real-time
- See progress bars for running assets
- Auto-refresh on completion

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `/` | Focus search |
| `g` then `a` | Go to Assets |
| `g` then `r` | Go to Runs |
| `Esc` | Close panels |

## Tips & Tricks

### Viewing Large Graphs

- **Zoom**: Scroll wheel or pinch
- **Pan**: Click and drag
- **Fit to view**: Button in graph controls
- **Minimap**: Shows position in large graphs

### Understanding Data Flow

- Follow arrows from left to right
- Upstream = data sources (left)
- Downstream = data products (right)
- Click asset to highlight its lineage

### Debugging Failed Assets

1. Check the error message in logs
2. Look at "Structured metadata" for details
3. Check upstream assets (might be the issue)
4. View previous successful runs for comparison

### Monitoring Pipeline Health

- Overview page shows recent failures
- Asset health indicators show staleness
- Event log shows all materializations

## Sample Pipeline Walkthrough

Using the example pipeline in this repo:

### 1. View the Pipeline

```
Assets page shows:
- raw_users (API data)
- raw_posts (API data)
- cleaned_users (transformed)
- enriched_posts (joined)
- posts_analytics (aggregated)
- company_analytics (aggregated)
```

### 2. Run the Pipeline

```
Click "Materialize all"
→ Watch raw_users and raw_posts run in parallel
→ Then cleaned_users runs
→ Then enriched_posts runs
→ Finally both analytics run in parallel
```

### 3. Inspect Results

```
Click posts_analytics
→ Metadata tab shows:
  - num_records: 10
  - csv_path: output/posts_analytics.csv
  - preview: Data table
  - top_poster: "Bret"
```

### 4. View Data

```
Events tab shows:
→ All previous runs
→ Timestamps
→ Metadata from each run
```

## Troubleshooting

### "Asset never materialized"

**Cause**: Asset hasn't been run yet

**Solution**: Click "Materialize" to run it

### "Asset is stale"

**Cause**: Upstream data changed, this asset needs updating

**Solution**: Materialize to get latest data

### Can't find asset in graph

**Cause**: Large graph, asset not visible

**Solution**:
- Use search (/)
- Check asset groups in sidebar
- Use filters

### Logs are empty

**Cause**: Asset hasn't produced log messages

**Solution**: Add `context.log.info(...)` to your asset code

### Slow materialization

**Cause**: Processing large data or slow external API

**Solution**:
- Check logs for bottlenecks
- Consider partitioning large datasets
- Add progress logging

## Next Steps

- Explore the sample pipeline
- Try materializing individual assets
- View metadata and logs
- Modify an asset and re-run
- Set up a schedule

For code examples, see `src/ingestion_sample/defs/assets.py`
