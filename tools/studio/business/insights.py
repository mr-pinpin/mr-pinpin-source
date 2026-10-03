"""Observed Studio history; never infer retries or provider time from similar jobs."""
from collections import Counter, defaultdict
from datetime import datetime
from statistics import median


def elapsed(start, end):
    try:
        value = (datetime.fromisoformat(end.replace('Z', '+00:00')) -
                 datetime.fromisoformat(start.replace('Z', '+00:00'))).total_seconds()
        return round(value, 3) if value >= 0 else None
    except (TypeError, ValueError, AttributeError):
        return None


def insights(store):
    state = store.read()
    jobs, events = state.get('jobs', []), state.get('events', [])
    statuses = Counter(j.get('status', 'unknown') for j in jobs)
    known = {j['id']: j for j in jobs}
    retries = [dict(jobId=j['id'], retryOf=j['retryOf']) for j in jobs
               if j.get('retryOf') in known and j['retryOf'] != j['id']]
    durations, missing, registrations = [], 0, 0
    hotspots = defaultdict(lambda: dict(jobs=0, failures=0, rejections=0, retries=0, jobIds=[]))
    for job in jobs:
        terminal = job.get('completedAt') if job.get('status') == 'completed' else None
        if job.get('status') == 'failed':
            terminal = next((e.get('createdAt') for e in reversed(events)
                             if e.get('type') == 'job.failed' and e.get('jobId') == job['id']), None)
        registration = job.get('historicalRegistration') is True or job.get('instruction', '').startswith('Register already-generated ')
        registrations += registration
        seconds = None if registration else elapsed(job.get('claimedAt'), terminal)
        if seconds is not None:
            durations.append(dict(jobId=job['id'], seconds=seconds))
        elif not registration and job.get('status') in ('completed', 'failed'):
            missing += 1
        targets = job.get('sceneIds') or [job.get('entityId') or 'unscoped']
        for target in targets:
            key = (job.get('chapterId'), target, job.get('kind', 'unknown'))
            row = hotspots[key]
            row['jobs'] += 1
            row['failures'] += job.get('status') == 'failed'
            row['rejections'] += sum(a.get('reviewStatus') == 'user-rejected' for a in job.get('artifacts', []))
            row['retries'] += any(r['jobId'] == job['id'] for r in retries)
            row['jobIds'].append(job['id'])
    rows = [dict(chapterId=k[0], targetId=k[1], kind=k[2], **v) for k, v in hotspots.items()
            if v['failures'] or v['rejections'] or v['retries']]
    rows.sort(key=lambda r: (-(r['failures'] + r['rejections'] + r['retries']), r['targetId']))
    return dict(schemaVersion=1, revision=state['revision'], totalJobs=len(jobs),
                statuses=dict(statuses), eventCount=len(events),
                explicitRetries=len(retries), retryLinks=retries,
                retryCoverage='Explicit retryOf links only; earlier retry lineage is unknown.',
                observedDurations=dict(unit='seconds', sampleCount=len(durations),
                    medianSeconds=median([r['seconds'] for r in durations]) if durations else None,
                    terminalJobsWithoutTiming=missing, excludedHistoricalRegistrations=registrations, samples=durations,
                    meaning='Claim to completion/failure ledger interval; not provider generation time. Explicit already-generated registrations are excluded.'),
                hotspots=rows, notes=[
                    'Only this Studio job/event ledger is counted. Imported artwork is not a recorded generation call.',
                    'Multiple jobs for one target do not establish a retry. Historical cost and provider time are unknown.',
                    'A job with several scene targets appears in each relevant hotspot. Rejections count current artifact decisions.'])
