"""English submission report generated only from this complete run's evidence."""
from html import escape
import os
import re
from pathlib import Path

from .report import QUESTIONS, chart


def link(path, folder):
    return Path(os.path.relpath(path, folder)).as_posix()


def write_full(result, folder, root):
    folder, root = Path(folder), Path(root)
    esc = lambda value: escape(str(value), quote=True)
    lines = ["# TP05: real-time data streaming using Apache Kafka", "",
             f"Run: `{result['run_id']}`. Status: **{result['status']}**.", "",
             "## Scope and environment", "",
             "A single Apache Kafka 3.9.1 broker runs in KRaft mode through Docker Compose. "
             "Python 3.11 and the teacher's kafka-python==2.0.2 client run synthetic campus sensor producers and consumers. "
             "The main topic has three partitions and replication factor 1. "
             "No ZooKeeper service or extra broker is involved.", "",
             "Student scripts remain unchanged. The automation assigns unique consumer groups, captures starting offsets, "
             "and applies an eight-second idle timeout so each report covers only its new batch. "
             "No existing consumer group is reset. No topic, Docker volume, or stored record is deleted. "
             "Unique investigation topics remain available until Kafka retention removes their records.", "",
             "## Required tasks and measured results", "",
             "| Scenario | Produced | Independently verified | Displayed | Alerts | Mean temperature C | CSV rows | Status |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    sections = []
    for mode, entry in result.get("scenarios", {}).items():
        data = entry["result"]
        lines.append(f"| {mode} | {data.get('produced', 'N/A')} | {data.get('verified_in_kafka', 'N/A')} | "
                     f"{data.get('displayed', 'N/A')} | {data.get('alerts', 'N/A')} | "
                     f"{data.get('average_temperature_c', 'N/A')} | {data.get('csv_rows', 'N/A')} | {data['status']} |")
        scenario_path = root / entry["path"]
        sections.append(f"<p><a href='{esc(link(scenario_path / 'report.html', folder))}'>{esc(mode)} detailed report and evidence</a></p>")
    lines.extend(["", "Teacher mode sends 30 readings at one-second intervals. Extended and CSV modes send 100 readings "
                  "at one-second intervals. They are different random batches, so their mean temperatures and alert counts "
                  "need not match. The larger batch takes longer to send. Extended processing calculates the running average "
                  "across every received event before filtering. Science is the default displayed building. "
                  "CSV contains only the displayed readings and the five requested columns: "
                  "event_id, sensor_id, temperature_c, humidity_pct, timestamp.", ""])
    for mode, entry in result.get("scenarios", {}).items():
        lines.append(f"- [{mode} detailed report]({link(root / entry['path'] / 'report.md', folder)})")
    investigation = result.get("investigations", {})
    lines.extend(["", "## Consumer-group experiment", ""])
    if investigation.get("status") == "PASS":
        shared = investigation["same_group"]
        different = investigation["different_groups"]
        one, three = investigation["one_partition"], investigation["three_partitions"]
        lines.extend([
            f"Fresh topic: `{investigation['topics'][0]}`. Thirty fixture events were sent, explicitly spread across three partitions.", "",
            f"Two members of the same group received {shared['counts']} records. Their partition assignments were {shared['assignments']}. "
            "Together they received all 30 records without duplicate partition/offset positions.", "",
            f"Two different groups received {[item['count'] for item in different]} records. Each independently read the complete retained batch. "
            "Restarting the first group after committing its offsets received zero old records despite earliest.", "",
            "This demonstrates partition ownership rather than strict round-robin allocation of individual messages. "
            "These group members run concurrently in two automation threads with separate KafkaConsumer instances; they are not two manually opened terminals.", "",
            "## One partition versus three", "",
            f"Fresh topic: `{investigation['topics'][1]}`. With one partition and 12 records, the two consumers received {one['counts']}; "
            f"assignments were {one['assignments']}.", "",
            "The same topic was altered to three partitions, then 12 more records were sent explicitly across the three partitions. "
            f"A fresh shared group read all 24 records with counts {three['counts']} and assignments {three['assignments']}.", "",
            "The experiment verified that the original 12 records remained in partition 0 at their original offsets. "
            "Both consumers can own partitions after expansion. Broker count and replication factor remain 1. "
            "There is no new broker failover or global ordering, and partition count cannot decrease in place.", "",
            "The investigation uses deterministic synthetic fixture events and explicit partition selection to make the comparison repeatable. "
            "The actual teacher and extended student producers still use their original automatic partition selection.", "",
            "[Investigation log](investigations/investigations.txt) | [Structured verification](investigations/results.json) | "
            "[One-partition description](investigations/one-partition.txt) | [Three-partition description](investigations/three-partitions.txt)", "",
        ])
    else:
        lines.extend(["Not verified in this run. See the failure below and preserved evidence.", ""])
    lines.extend(["## Report questions", ""])
    for index, (question, answer) in enumerate(QUESTIONS, 1):
        if index == 9 and len(result.get("screenshots", [])) == 7:
            answer = ("The screenshots linked below show Docker Compose status, topic description, live producer execution, "
                      "and live consumer execution for this run. Additional console captures display the saved investigation transcripts. "
                      "Full logs and structured results are included. Screenshots show excerpts; logs contain the complete output.")
        elif index == 9:
            answer = "Required screenshots were not all verified in this run. See the failure and preserved logs."
        lines.extend([f"### {index}. {question}", "", answer, ""])
    lines.extend(["## Evidence screenshots", ""])
    screenshot_html = []
    for item in result.get("screenshots", []):
        lines.extend([f"### {item['label']}", "", f"Capture type: {item['kind']}.", "", f"![{item['label']}]({item['path']})", ""])
        screenshot_html.append(f"<h3>{esc(item['label'])}</h3><p>{esc(item['kind'])}</p>"
                               f"<a href='{esc(item['path'])}'><img src='{esc(item['path'])}' alt='{esc(item['label'])}'></a>")
    lines.extend(["## Problems encountered and solutions", "",
                  "The teacher's old client pin is incompatible with newer Python runtimes used on this computer. "
                  "The runner uses the existing Python 3.11 environment instead of changing the teacher's dependency. "
                  "The client has known denial-of-service advisories and is retained only for this trusted local classroom exercise.", "",
                  "Windows localhost can resolve to IPv6. Compose exposes loopback IPv4 and IPv6 so the supplied localhost bootstrap address works. "
                  "KAFKA_LOG_DIRS points at the mounted data directory so broker storage survives container recreation.", "",
                  "Old retained messages and saved group offsets can make repeated classroom runs confusing. "
                  "Report consumers use new groups and explicitly recorded starting offsets without resetting the original groups. "
                  "The separate investigations deliberately read retained records to demonstrate group and offset behavior.", "",
                  "Earlier investigation evidence was deleted. This report uses only fresh results from its own complete run. "
                  "Screenshots are native Windows console captures, not HTML drawings or synthetic terminal viewers. "
                  "Capture requires an unlocked interactive desktop and briefly brings each console to the foreground. "
                  "A capture failure fails the complete workflow rather than silently replacing a screenshot with a fabricated image.", "",
                  "## Verification checks", ""])
    for item in result.get("checks", []):
        lines.append(f"- {'PASS' if item['passed'] else 'FAIL'}: {item['name']}")
    if result.get("error"):
        lines.extend(["", "## Failure", "", result["error"], "", "Inspect error.txt and the saved logs. A failed run is not proof of completion."])
    lines.extend(["", "## Submission and cleanup", "",
                  "The runner prepares local evidence and the report. It does not log in, commit, push to GitHub, or submit a repository URL. "
                  "Those submission actions remain pending. Include the TP05 source, compose.yaml, requirements.txt, README, this report, "
                  "and its linked evidence. Do not upload a virtual environment, credentials, or unnecessary older generated runs.", "",
                  "Docker is left running so the results can be inspected. When finished, run docker compose down from TP05. "
                  "Do not use down -v unless the stored Kafka data is no longer needed. A broker-failure experiment is not required "
                  "by the listed further-investigation tasks, and this runner does not stop the broker during testing.", ""])
    markdown = "\n".join(lines)
    (folder / "report.md").write_text(markdown, encoding="utf-8")
    # Keep Markdown as the complete text source and add real linked visual evidence.
    paragraphs = []
    in_table = False
    for line in lines:
        if line.startswith("|"):
            if not in_table:
                paragraphs.append("<div class='scroll'><table>")
                in_table = True
            if line.startswith("| ---"):
                continue
            paragraphs.append("<tr>" + "".join(f"<td>{esc(v.strip())}</td>" for v in line.strip("|").split("|")) + "</tr>")
            continue
        if in_table:
            paragraphs.append("</table></div>")
            in_table = False
        if line.startswith("#"):
            n = len(line) - len(line.lstrip("#"))
            paragraphs.append(f"<h{n}>{esc(line[n:].strip())}</h{n}>")
        elif line and not line.startswith("!["):
            inline = esc(line)
            inline = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href='\2'>\1</a>", inline)
            inline = re.sub(r"`([^`]+)`", r"<code>\1</code>", inline)
            inline = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", inline)
            paragraphs.append("<p>" + inline + "</p>")
    graphs = "".join(f"<h3>{esc(mode)} temperatures</h3>{chart(entry['result'].get('events', []))}"
                     for mode, entry in result.get("scenarios", {}).items())
    page = """<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>TP05 complete assignment report</title><style>
body{margin:0;background:#f7f5ef;color:#202c2b;font:17px/1.7 system-ui,sans-serif}main{max-width:1000px;margin:auto;padding:24px 16px}h1{line-height:1.2}h2{margin-top:36px}p{overflow-wrap:anywhere}a{color:#006a5e}table{border-collapse:collapse;width:100%;font-size:14px}td{border:1px solid #cbd4ce;padding:8px}.scroll{overflow-x:auto}img{max-width:100%;height:auto;border:1px solid #cbd4ce}svg{width:100%;height:auto}svg text{font:14px monospace;fill:#202c2b}.axis{stroke:#87958b}.threshold{stroke:#a94b20;stroke-dasharray:6 4}.series{fill:none;stroke:#006a5e;stroke-width:2}.muted{font-size:14px}nav{display:flex;gap:16px;flex-wrap:wrap}@media print{body{background:white}nav{display:none}img{max-height:650px;object-fit:contain}h2{break-after:avoid}}
</style></head><body><main><nav><a href='report.md'>Complete Markdown report</a><a href='results.json'>Run manifest</a><button onclick='print()'>Print / PDF</button></nav>"""
    page += "".join(paragraphs) + "<h2>Open the detailed reports</h2>" + "".join(sections)
    if investigation:
        page += "<p><a href='investigations/investigations.txt'>Investigation transcript</a> | <a href='investigations/results.json'>Investigation verification</a></p>"
    page += "<h2>Temperature charts</h2>" + graphs + "<h2>Native terminal screenshots</h2>" + "".join(screenshot_html)
    page += "</main></body></html>"
    (folder / "report.html").write_text(page, encoding="utf-8")
    relative = link(folder / "report.html", root)
    (root / "REPORT.html").write_text(
        "<!doctype html><html lang='en'><meta charset='utf-8'><title>TP05 report</title>"
        f"<h1>Latest complete TP05 run: {esc(result['status'])}</h1><p><a href='{esc(relative)}'>Open the complete English report, screenshots, and evidence</a></p></html>",
        encoding="utf-8")
    (root / "REPORT.md").write_text(
        f"# TP05 complete report\n\nStatus: {result['status']}.\n\n"
        f"[Open HTML report]({relative})\n\n[Open Markdown report]({link(folder / 'report.md', root)})\n\n"
        "Local verification does not upload or submit the work to GitHub.\n", encoding="utf-8")
