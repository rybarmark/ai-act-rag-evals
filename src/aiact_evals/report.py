"""Render a results JSON as a single self-contained HTML page."""

from __future__ import annotations

from jinja2 import Template

_TEMPLATE = Template(
    """<!doctype html><html lang="en"><meta charset="utf-8">
<title>AI Act RAG eval report</title>
<style>
 body{font:14px/1.5 system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem;color:#1a1a1a}
 table{border-collapse:collapse;width:100%;margin:1rem 0}
 th,td{border-bottom:1px solid #ddd;padding:.4rem .5rem;text-align:left;vertical-align:top}
 .fail{color:#b00020;font-weight:600}.pass{color:#1b7f3b;font-weight:600}
 pre{white-space:pre-wrap;margin:0;font-size:12px}
 .meta{color:#555}
</style>
<h1>AI Act RAG eval report</h1>
<p class="meta">{{ meta.timestamp }} · mode {{ meta.mode }} · {{ meta.cases }} cases × {{ meta.repeats }} runs ·
 generator {{ meta.generator }} · judge {{ meta.judge }} · corpus {{ meta.corpus_version }} · commit {{ meta.git_sha }}</p>
<h2>Scores</h2>
<table><tr><th>Grader</th><th>Pass rate</th><th>Passed / graded</th><th>Threshold</th></tr>
{% for name, g in summary.graders.items() %}
 {% set t = thresholds.get(name) %}
 <tr><td>{{ name }}</td>
 <td class="{{ 'fail' if (t is not none and g.rate is not none and g.rate < t) else 'pass' }}">
   {{ '%.1f%%' % (g.rate * 100) if g.rate is not none else 'n/a' }}</td>
 <td>{{ g.passed }} / {{ g.total }}</td><td>{{ '%.0f%%' % (t * 100) if t is not none else '' }}</td></tr>
{% endfor %}
</table>
<h2>Flaky cases ({{ summary.flaky | length }})</h2>
<p>Passed on some runs and failed on others.</p>
<ul>{% for f in summary.flaky %}<li>{{ f }}</li>{% else %}<li>none</li>{% endfor %}</ul>
<h2>Failures ({{ summary.failures | length }})</h2>
<table><tr><th>Case</th><th>Grader</th><th>Reason</th><th>Answer</th></tr>
{% for f in summary.failures %}
 <tr><td>{{ f.case_id }}{% if f.run is not none %}<br><small>run {{ f.run + 1 }}</small>{% endif %}</td>
 <td>{{ f.grader }}</td><td>{{ f.reason }}</td>
 <td>{% if f.question %}<b>{{ f.question }}</b><pre>{{ f.answer }}</pre><small>retrieved: {{ f.retrieved }}</small>{% endif %}</td></tr>
{% endfor %}
</table>
</html>"""
)


def render_report(results: dict, thresholds: dict[str, float]) -> str:
    return _TEMPLATE.render(meta=results["meta"], summary=results["summary"], thresholds=thresholds)
