"""Generate offline HTML and Markdown reports from measured run results."""
from html import escape
from pathlib import Path

QUESTIONS = [
    ("What problem does Kafka solve?", "It separates event producers from consumers, retains events, and lets applications read independently at their own pace."),
    ("Define the main terms.", "A producer sends events. A consumer reads them. A broker stores and serves partitions. A topic names an event category. A partition is an ordered log. An offset is a position in one partition. A consumer group divides partition ownership and tracks progress."),
    ("How does a topic differ from a partition?", "A topic is a logical category. Partitions divide its log and allow parallel consumption. Ordering is within a partition, not across the entire topic."),
    ("When does earliest apply?", "Only when the group has no valid committed position for a partition. It does not rewind valid committed progress. The report runner explicitly seeks its unique capture group to positions recorded before this run."),
    ("What is the group ID for?", "Members of one group share partition ownership. Different groups maintain independent progress and can read the same retained data. This report uses a unique group so existing groups are not changed."),
    ("Why JSON, and what is one limitation?", "JSON is readable and maps easily to Python dictionaries. It does not enforce a schema; missing or incorrectly typed fields can break these simple consumers."),
    ("How does Compose help?", "One configuration file defines Kafka's image, KRaft settings, ports, and persistent storage. Compose starts and inspects it without a manual host Java installation."),
    ("What are the limitations?", "One broker and replication factor 1 provide no broker failover. This local lab has plaintext connections, no authentication, no backups, and no exactly-once guarantee for CSV side effects. acks=all acknowledges the only replica here; it does not confirm consumer processing."),
    ("Where is the evidence?", "This run folder contains real producer/consumer logs, broker status, the topic description, verified results, and CSV when selected. Existing screenshots under TP05/screenshots belong to a separate run. This HTML is a report, not a live-terminal screenshot."),
]


def text(value):
    return escape(str(value), quote=True)


def table(headers, rows):
    head = "".join(f"<th scope='col'>{text(value)}</th>" for value in headers)
    body = "".join("<tr>" + "".join(f"<td>{text(value)}</td>" for value in row) + "</tr>" for row in rows)
    return f"<div class='scroll'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def chart(events):
    if not events:
        return "<p>No verified event series is available.</p>"
    values = [float(event["temperature_c"]) for event in events]
    low, high = min(15, min(values) - 2), max(45, max(values) + 2)
    def x(index):
        return 54 + index * 690 / max(1, len(values) - 1)
    def y(value):
        return 215 - (value - low) * 175 / (high - low)
    points = " ".join(f"{x(i):.1f},{y(value):.1f}" for i, value in enumerate(values))
    labels = "".join(f"<text x='8' y='{y(value) + 4:.1f}'>{value:g} C</text>" for value in [low, 35, high])
    return f"""<svg viewBox='0 0 780 260' role='img' aria-label='Temperature by event ID, with a 35 degree alert threshold'>
<title>Verified temperatures, sorted by event ID. Not a global Kafka partition ordering guarantee.</title>
<line class='axis' x1='54' y1='30' x2='54' y2='215'/><line class='axis' x1='54' y1='215' x2='744' y2='215'/>
<line class='threshold' x1='54' y1='{y(35):.1f}' x2='744' y2='{y(35):.1f}'/>
<polyline class='series' points='{points}'/>{labels}
<text x='54' y='242'>Event {text(events[0]['event_id'])}</text>
<text x='660' y='242'>Event {text(events[-1]['event_id'])}</text></svg>
<p class='muted'>Verified Kafka values sorted by the application event_id. The dashed line is 35 C. This display does not imply global ordering across partitions.</p>"""


def write_report(result, folder):
    folder = Path(folder)
    checks = result.get("checks", [])
    metrics = [
        ("Expected events", result["expected_events"]),
        ("Printed by producer", result.get("produced", "Not verified")),
        ("Independently verified in Kafka", result.get("verified_in_kafka", "Not verified")),
        ("Displayed after filtering", result.get("displayed", "Not verified")),
        ("Alerts for displayed events", result.get("alerts", "Not verified")),
    ]
    analysis = [("Average across all received events, C", result.get("average_temperature_c", "Not verified")),
                ("Building filter", result.get("building") or "All buildings"),
                ("CSV rows", result.get("csv_rows", "Not applicable")),
                ("Duration, seconds", result.get("duration_seconds", "Not available"))]
    settings = [("Producer", result["producer"]), ("Consumer", result["consumer"]),
                ("Topic", result.get("topic", "Not available")),
                ("Report group", result.get("group_id", "Not available")),
                ("Python", result.get("python", "Not available"))]
    error = f"<p class='error'>{text(result['error'])}</p>" if result.get("error") else ""
    check_html = table(["Check", "Outcome"], [(check["name"], "PASS" if check["passed"] else "FAILED") for check in checks]) if checks else "<p>No verification checks completed. Read the error and logs before retrying.</p>"
    artifacts = result.get("artifacts", [])
    links = "".join(f"<li><a href='{text(name)}'>{text(name)}</a></li>" for name in artifacts)
    qa = "".join(f"<details><summary>{index}. {text(question)}</summary><p>{text(answer)}</p></details>" for index, (question, answer) in enumerate(QUESTIONS, 1))
    data_rows = [(event["event_id"], event["sensor_id"], event["temperature_c"],
                  event["humidity_pct"], event.get("campus_building", "Not supplied"), event["timestamp"])
                 for event in result.get("events", [])]
    offsets = [(number, start, result.get("end_offsets", {}).get(number, "Not verified"))
               for number, start in result.get("start_offsets", {}).items()]
    html = f"""<!DOCTYPE html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>TP05 | {text(result['title'])} | {text(result['status'])}</title>
<style>
:root{{--bg:#f6f3ec;--fg:#202c2b;--panel:#fffdf8;--line:#d1d8cd;--accent:#006a5e;--muted:#52635b;--danger:#a53624;--code:#edf0e8}}
:root[data-theme=dark]{{--bg:#15201d;--fg:#e6ebdf;--panel:#1f2d27;--line:#435548;--accent:#a3d8b1;--muted:#b6c6b6;--danger:#ffb19d;--code:#25372b}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.7 Georgia,serif}}main{{max-width:1000px;margin:auto;padding:28px 20px}}h1{{font-size:clamp(28px,5vw,43px);line-height:1.2;margin:12px 0}}h2{{font-size:25px;margin-top:32px}}h3{{font-size:20px}}a{{color:var(--accent)}}code,pre,.stamp{{font-family:Consolas,monospace}}.stamp{{color:var(--accent);font-size:13px}}.muted{{color:var(--muted)}}.panel,details{{background:var(--panel);border:1px solid var(--line);padding:16px;border-radius:10px;margin:14px 0}}.error{{color:var(--danger);font-weight:bold}}button{{font:inherit;border:1px solid var(--line);background:var(--panel);color:var(--fg);border-radius:8px;padding:8px 14px;cursor:pointer}}button:focus-visible,a:focus-visible,summary:focus-visible{{outline:3px solid var(--accent);outline-offset:3px}}summary{{cursor:pointer;font-weight:bold}}.scroll{{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin:12px 0}}table{{width:100%;border-collapse:collapse;background:var(--panel)}}th,td{{padding:11px 14px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}}th{{background:var(--code)}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:var(--code);padding:14px;border-radius:8px}}svg{{width:100%;height:auto;color:var(--muted)}}svg text{{fill:currentColor;font:13px Consolas,monospace}}.axis{{stroke:var(--muted)}}.threshold{{stroke:var(--danger);stroke-dasharray:6 5}}.series{{fill:none;stroke:var(--accent);stroke-width:2}}.status{{font:bold 15px Consolas,monospace;display:inline-block;border:1px solid var(--accent);padding:5px 12px;border-radius:30px;color:var(--accent)}}.failed{{color:var(--danger);border-color:var(--danger)}}footer{{margin-top:30px;border-top:1px solid var(--line);padding-top:16px}}
@media(max-width:520px){{main{{padding:16px 12px}}th,td{{padding:8px;font-size:14px}}}}
@media print{{button{{display:none}}body{{background:white;color:black}}main{{max-width:none;padding:0}}details,svg,tr{{break-inside:avoid}}.scroll{{overflow:visible}}}}
</style></head><body><main>
<p class='stamp'>TP05 / GENERATED FROM AN ACTUAL RUN</p><h1>{text(result['title'])}</h1>
<p class='status {'failed' if result['status'] != 'PASS' else ''}'>{text(result['status'])}</p>
<p class='muted'>Run {text(result['run_id'])}<br>Started {text(result['started_utc'])}<br>Finished {text(result.get('finished_utc', 'Not available'))}</p>
<button type='button' id='theme'>Switch light / dark</button> <button type='button' id='print'>Print / save PDF</button>
{error}
<h2>1. What ran</h2>{table(['Setting', 'Value'], settings)}
<p class='panel'>{text(result['automation_scope'])}</p>
<p>Only the basic stream for this mode is tested here. Consumer-group comparisons, partition-count changes, and broker-failure experiments are not automatically repeated by these launchers. The exam code stays in the original producer/consumer files; orchestration lives under automation/.</p>
<h2>2. Measured results</h2>{table(['Measurement', 'Value'], metrics)}{table(['Analysis', 'Value'], analysis)}
<p>The average includes every new event received in this run. Display, alerts, and CSV in the combined consumer apply after the building filter. CSV contains the five requested measurement columns, not the calculated average.</p>
<h2>3. Temperature series</h2>{chart(result.get('events', []))}
<h2>4. Verification</h2>{check_html}
{table(['Partition', 'Start position', 'End position'], offsets) if offsets else ''}
<h2>5. Output and evidence</h2><p>These are saved outputs from this run, not fabricated terminal screenshots. No existing screenshot is claimed to belong to this new run.</p>
<ul>{links}<li><a href='results.json'>results.json</a></li><li><a href='report.md'>Markdown report</a></li></ul>
<details><summary>All verified measurements</summary>{table(['Event', 'Sensor', 'Temperature C', 'Humidity %', 'Building', 'Timestamp'], data_rows) if data_rows else '<p>No verified measurements.</p>'}</details>
<h2>6. Report questions</h2>{qa}
<h2>7. Source integrity</h2>{table(['Student file', 'SHA-256 before execution'], result['source_sha256'].items())}
<p>The source-integrity check compares these fingerprints after execution. The run does not edit the student scripts, reset existing groups, delete topics, or remove volumes. Docker is left running.</p>
<footer><a href='../index.html'>All runs for this scenario</a> · <a href='../../../README.md'>Project instructions</a><p class='muted'>Offline report. No external libraries, fonts, or network assets are required.</p></footer>
</main><script>
const root=document.documentElement;const theme=document.getElementById('theme');theme.addEventListener('click',()=>{{root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';}});
document.getElementById('print').addEventListener('click',()=>window.print());let states=[];window.addEventListener('beforeprint',()=>{{states=Array.from(document.querySelectorAll('details')).map(d=>[d,d.open]);states.forEach(p=>p[0].open=true);}});window.addEventListener('afterprint',()=>states.forEach(p=>p[0].open=p[1]));
</script></body></html>"""
    (folder / "report.html").write_text(html, encoding="utf-8")
    lines = [f"# TP05: {result['title']}", "", f"Status: **{result['status']}**", "",
             f"Run: `{result['run_id']}`", "", f"Started: {result['started_utc']}", "",
             "## What ran", "", *[f"- {name}: `{value}`" for name, value in settings], "",
             result["automation_scope"], "", "## Measurements", "",
             *[f"- {name}: {value}" for name, value in metrics], "", "## Analysis", "",
             *[f"- {name}: {value}" for name, value in analysis], "", "## Verification", "",
             *[f"- {'PASS' if check['passed'] else 'FAILED'}: {check['name']}" for check in checks], ""]
    if result.get("error"):
        lines.extend(["## Error", "", result["error"], ""])
    lines.extend(["## Scope", "", "This mode does not automatically repeat group comparisons, partition alterations, or broker-failure experiments. Source files are not edited. Existing groups, topics, and volumes are not reset or deleted.", "", "## Report answers", ""])
    for index, (question, answer) in enumerate(QUESTIONS, 1):
        lines.extend([f"### {index}. {question}", "", answer, ""])
    lines.extend(["## Evidence", "", *[f"- [{name}]({name})" for name in artifacts], "", "[Full HTML report](report.html) · [Verified data](results.json)", ""])
    (folder / "report.md").write_text("\n".join(lines), encoding="utf-8")
    parent = folder.parent
    runs = sorted([p for p in parent.iterdir() if p.is_dir() and (p / "report.html").exists()], reverse=True)
    links = "".join(f"<li><a href='{text(p.name)}/report.html'>{text(p.name)}</a></li>" for p in runs)
    index = f"<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>TP05 reports</title></head><body><h1>{text(result['title'])}</h1><p>Newest run first. Each run has a separate folder; earlier results are preserved.</p><ol>{links}</ol></body></html>"
    (parent / "index.html").write_text(index, encoding="utf-8")


def write_overview(root):
    """Refresh the report entry point without changing any historical run data."""
    import json
    root = Path(root)
    rows = []
    for mode in ["teacher", "extended", "csv"]:
        paths = sorted((root / "reports" / mode).glob("*/results.json"), reverse=True)
        if paths:
            data = json.loads(paths[0].read_text(encoding="utf-8"))
            relative = paths[0].parent.relative_to(root).as_posix()
            rows.append((data, relative))
    entries = "".join(
        f"<tr><td><a href='{text(path)}/report.html'>{text(data['title'])}</a></td>"
        f"<td>{text(data['status'])}</td><td>{text(data.get('verified_in_kafka', 'Not verified'))}</td>"
        f"<td>{text(data.get('displayed', 'Not verified'))}</td><td>{text(data.get('csv_rows', 'Not applicable'))}</td>"
        f"<td>{text(data.get('duration_seconds', 'Not available'))}</td></tr>"
        for data, path in rows)
    bars = []
    for index, (data, _) in enumerate(rows):
        y = 30 + index * 65
        count = data.get("verified_in_kafka", 0)
        shown = data.get("displayed", 0)
        maximum = max(100, *(item[0].get("verified_in_kafka", 0) for item in rows))
        bars.append(f"<text x='8' y='{y + 17}'>{text(data['mode'])}</text>"
                    f"<rect x='105' y='{y}' width='{count * 480 / maximum:.1f}' height='17' fill='#006a5e'/>"
                    f"<text x='{115 + count * 480 / maximum:.1f}' y='{y + 14}'>{count}</text>"
                    f"<rect x='105' y='{y + 21}' width='{shown * 480 / maximum:.1f}' height='17' fill='#a76b27'/>"
                    f"<text x='{115 + shown * 480 / maximum:.1f}' y='{y + 35}'>{shown}</text>")
    qa = "".join(f"<details><summary>{i}. {text(question)}</summary><p>{text(answer)}</p></details>"
                 for i, (question, answer) in enumerate(QUESTIONS, 1))
    page = f"""<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>TP05 | Generated report overview</title><style>
body{{margin:0;background:#f6f3ec;color:#202c2b;font:17px/1.7 Georgia,serif}}main{{max-width:960px;padding:24px 16px;margin:auto}}h1{{font-size:36px;line-height:1.2}}a{{color:#006a5e}}.scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;background:#fffdf8}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #d1d8cd}}svg{{width:100%;height:auto}}svg text{{font:14px Consolas,monospace;fill:#202c2b}}details{{background:#fffdf8;border:1px solid #d1d8cd;border-radius:8px;padding:12px;margin:10px 0}}summary{{cursor:pointer;font-weight:bold}}code{{font-family:Consolas,monospace}}.note{{border-left:4px solid #006a5e;padding:12px 16px;background:#e2eee7}}@media print{{body{{background:white}}.scroll{{overflow:visible}}}}
</style></head><body><main><p>TP05 / RECORDED RUNS</p><h1>Kafka lab report</h1>
<p>This overview uses the latest saved result for each scenario. Open a scenario for its checks, temperature chart, source fingerprints, logs, and Markdown report.</p>
<div class='scroll'><table><thead><tr><th>Scenario</th><th>Status</th><th>Verified events</th><th>Displayed</th><th>CSV rows</th><th>Seconds</th></tr></thead><tbody>{entries}</tbody></table></div>
<h2>Received versus displayed</h2><p>Green: all verified new Kafka events. Brown: readings displayed after the building filter.</p>
<svg viewBox='0 0 690 250' role='img' aria-label='Verified event counts compared with displayed event counts by scenario'>{''.join(bars)}</svg>
<p class='note'>Each scenario is a different random batch. The extended and CSV modes filter Science by default. Their averages still include all new received events. These are real recorded results, not promised values for the next run.</p>
<h2>Generate a new run</h2><p>Use Python 3.10 or 3.11 with requirements.txt installed. Run one command from TP05:</p>
<pre>python run_teacher.py
python run_extended.py
python run_csv.py</pre><p>Run only the scenario you want. Teacher mode takes about 70 seconds on this machine; the 100-event modes about 140 seconds. Docker must be available; the runner starts this project's Compose service if needed. It leaves Docker running.</p>
<h2>Regenerate the reports without Kafka</h2><pre>python generate_reports.py</pre><p>This rebuilds HTML and Markdown from existing reports/*/*/results.json. It does not send events or rerun verification. If results.json was deleted too, run the desired scenario again.</p>
<h2>Report answers</h2>{qa}
<p>Existing screenshot files come from a separate earlier run. These pages are generated reports, not live-terminal screenshots. The launchers do not repeat group comparisons, partition alterations, or broker-failure experiments.</p>
<p><a href='README.md'>Setup and commands</a> · <a href='Kafka-exam-guide-ar.html'>Arabic code explanation</a></p>
</main></body></html>"""
    (root / "REPORT.html").write_text(page, encoding="utf-8")
    lines = ["# TP05: generated Kafka report", "", "Open [REPORT.html](REPORT.html) for the latest recorded scenarios.", "",
             "| Scenario | Status | Verified events | Displayed | CSV rows |", "| --- | --- | --- | --- | --- |"]
    for data, path in rows:
        lines.append(f"| [{data['title']}]({path}/report.html) | {data['status']} | {data.get('verified_in_kafka', 'Not verified')} | {data.get('displayed', 'Not verified')} | {data.get('csv_rows', 'Not applicable')} |")
    lines.extend(["", "Each scenario has its own HTML/Markdown report and raw evidence. Different scenarios use different random batches.", "", "## Commands", "", "```powershell", "python run_teacher.py", "python run_extended.py", "python run_csv.py", "```", "", "Choose one scenario. Use Python 3.10 or 3.11 with requirements.txt installed. See README.md for this computer's existing E: environment.", "", "Regenerate saved reports without sending events:", "", "```powershell", "python generate_reports.py", "```", "", "Report regeneration reads saved results; it does not perform a new verification. Old runs are preserved in separate folders. The student producer and consumer files are not edited, existing groups are not reset, and Docker volumes are not removed.", "", "## Report answers", ""])
    for i, (question, answer) in enumerate(QUESTIONS, 1):
        lines.extend([f"### {i}. {question}", "", answer, ""])
    (root / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
